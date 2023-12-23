from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import Client

from bjut_tech.auth import JwglxtAuthentication
from bjut_tech.persistence import get_persistence
from bjut_tech.tunnel import TunnelSelector
from .grades import GradesFetcher
from .notify_email import EmailNotifier

if TYPE_CHECKING:
    from bjut_tech import ConfigRegistry


def main(config: ConfigRegistry):
    session = Client(headers={
        'User-Agent': 'Mozilla/5.0'
    }, verify=False)
    tunnel = TunnelSelector(session, config).get_best()

    base_url = config.get('JW_BASE_URL', 'https://jwglxt.bjut.edu.cn')
    username = config['CAS_USERNAME']
    password = config.get('JW_PASSWORD', config['CAS_PASSWORD'])
    auth = JwglxtAuthentication(tunnel, base_url, username, password)
    auth.authenticate()

    persistence = get_persistence(config)
    fetcher = GradesFetcher(tunnel, persistence, base_url)
    data = fetcher()

    if data['grades_new']:
        notifier = EmailNotifier(config, data)
        notifier.send()

    return data
