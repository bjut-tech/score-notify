# Aliyun FC Handler for score_notify
#
# Event format:
# {
#   operation?: 'main' | 'auth' | 'get_grades' | 'get_classes' | 'get_schedule'
#   data?: Any  # for operations that require additional data
#   config?: Dict[string, string | number | boolean]
#   credentials?: {
#     username: string
#     password: string
#     passwordJw?: string
#   }
#   session?: string
# }
#
# If no config is explicitly provided,
# environment variables will be used.
#
# Set operation to 'auth' to authenticate only and get the authenticated session;
# pass a valid session to skip authentication.
#
# For all config entries, see the bjut_tech package.

from __future__ import annotations

import base64
import binascii
import json
import sys
from typing import TYPE_CHECKING, Optional

from httpx import Client

from bjut_tech import ConfigRegistry
from bjut_tech.auth import JwglxtAuthentication
from bjut_tech.persistence import get_persistence
from bjut_tech.tunnel import TunnelSelector
from score_notify import GradesFetcher, JwMisc, main

if TYPE_CHECKING:
    from bjut_tech.tunnel import AbstractTunnel


def deserialize_session(session: str, config: ConfigRegistry) -> Optional[AbstractTunnel]:
    # 1. 解码
    try:
        info = json.loads(base64.b64decode(session.encode('utf-8')).decode('utf-8'))
    except json.JSONDecodeError or binascii.Error or UnicodeDecodeError:
        return None

    # 2. 创建 Session + 恢复 Cookie
    session = Client(headers={
        'User-Agent': 'Mozilla/5.0'
    }, verify=False)
    for cookie in info['session']:
        session.cookies.set(*cookie)

    # 3. 恢复 Tunnel
    try:
        tunnel_cls = TunnelSelector.find(info['tunnel'])
    except ValueError:
        return None
    return tunnel_cls.construct(session, config)


def serialize_session(tunnel: AbstractTunnel) -> str:
    # 1. 保存 Cookie
    cookies = []
    for cookie in tunnel.get_session().cookies.jar:
        cookies.append((cookie.name, cookie.value, cookie.domain, cookie.path))

    # 2. 保存 Tunnel 名称 + 编码
    return base64.b64encode(json.dumps({
        'tunnel': tunnel.get_name(),
        'session': cookies
    }, ensure_ascii=False, indent=None).encode('utf-8')).decode('utf-8')


def handler(event: str, context) -> dict:
    try:
        request = json.loads(event)
    except Exception as e:
        if event:
            print(f'Failed to parse event: {event}', file=sys.stderr)

        request = None

    # 参数默认值
    operation = 'main'
    saved_session = None
    config = ConfigRegistry()
    overrides = {
        'ALIBABA_CLOUD_INTERNAL': True,
        'PERSISTENCE_TYPE': 'oss'
    }

    # 读取传入事件
    if isinstance(request, dict):
        if isinstance(request.get('credentials'), dict):
            overrides.update({
                'CAS_USERNAME': request['credentials'].get('username', '_'),
                'CAS_PASSWORD': request['credentials'].get('password', '_'),
                'JW_PASSWORD': request['credentials'].get('passwordJw')
            })
        if isinstance(request.get('config'), dict):
            overrides.update(request['config'])
        if isinstance(request.get('operation'), str):
            operation = request['operation']
        if isinstance(request.get('session'), str):
            saved_session = request['session']
    config.set_overrides(overrides)
    if saved_session:
        saved_session = deserialize_session(saved_session, config)

    # 直接执行模块主函数（查询分数 + 发送通知）
    if operation == 'main':
        return main(config)

    # 作为 `score-server` 后端服务，执行其他操作
    try:
        if saved_session:
            tunnel = saved_session
        else:
            session = Client(headers={
                'User-Agent': 'Mozilla/5.0'
            }, verify=False)
            tunnel = TunnelSelector(session, config).get_best()

        base_url = config.get('JW_BASE_URL', 'https://jwglxt.bjut.edu.cn')
        username = config.get('CAS_USERNAME')
        password = config.get('JW_PASSWORD') or config.get('CAS_PASSWORD')
        auth = JwglxtAuthentication(tunnel, base_url, username, password)
        auth.authenticate()  # implicitly checks if authenticated
        misc = JwMisc(tunnel, base_url)
        persistence = get_persistence(config)

        data = None
        if operation == 'auth':
            data = misc.user
        elif operation == 'get_grades':
            fetcher = GradesFetcher(tunnel, persistence, base_url)
            data = fetcher()
        elif operation == 'get_classes':
            data = misc.get_classes()
        elif operation == 'get_schedule':
            data = misc.get_schedule(**request.get('data', {
                'term': misc.user['term'],
                'grade_id': misc.user['grade_id'],
                'major_id': misc.user['major_id'],
                'class_id': misc.user['class_id']
            }))
        else:
            raise ValueError(f'Invalid operation: {operation}')
        return {
            'success': True,
            'session': serialize_session(tunnel),
            'data': data
        }
    except Exception as e:
        return {
            'success': False,
            'session': None,
            'error': str(e)
        }
