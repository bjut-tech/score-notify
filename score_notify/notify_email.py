from __future__ import annotations

import webbrowser
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from jinja2 import PackageLoader, select_autoescape, Environment

if TYPE_CHECKING:
    from bjut_tech import ConfigRegistry


class EmailNotifier:

    def __init__(self, config: ConfigRegistry, data: dict):
        self.receiver = config['NOTIFY_EMAIL']
        self.dry_run = config.get('NOTIFY_DRY_RUN', False)

        if not self.dry_run:
            self.client = AcsClient(
                config['ALIBABA_CLOUD_ACCESS_KEY_ID'],
                config['ALIBABA_CLOUD_ACCESS_KEY_SECRET']
            )

        self.data = data

    def render(self) -> str:
        loader = PackageLoader('score_notify')
        auto_escape = select_autoescape()
        env = Environment(loader=loader, autoescape=auto_escape)
        template = env.get_template("email.html")
        return template.render(**self.data)

    def send(self):
        if self.dry_run:
            with NamedTemporaryFile(mode='w',
                                    encoding='utf-8',
                                    suffix='.htm',
                                    delete=False) as f:
                f.write(self.render())
                webbrowser.open(f.name)
            return

        print('[*] Sending e-mail notification...')
        request = CommonRequest()
        request.set_accept_format('json')
        request.set_domain('dm.aliyuncs.com')
        request.set_method('POST')
        request.set_protocol_type('https')
        request.set_version('2015-11-23')
        request.set_action_name('SingleSendMail')
        request.add_query_param('AccountName', 'notify@bjut.tech')
        request.add_query_param('AddressType', '1')
        request.add_query_param('ReplyToAddress', 'false')
        request.add_query_param('Subject', '[bjut.tech] Score Notification')
        request.add_query_param('ToAddress', self.receiver)
        request.add_query_param('FromAlias', 'bjut.tech')
        request.add_query_param('HtmlBody', self.render())
        request.add_query_param('TagName', 'Notification')
        self.client.do_action_with_exception(request)
