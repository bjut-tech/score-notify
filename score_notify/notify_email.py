import webbrowser
from tempfile import NamedTemporaryFile

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from jinja2 import PackageLoader, select_autoescape, Environment

from .config import ALIYUN_ACCESS_ID, ALIYUN_ACCESS_SECRET, NOTIFY_EMAIL, NOTIFY_DRY_RUN


def render_template(data: dict) -> str:
    loader = PackageLoader('score_notify')
    auto_escape = select_autoescape()
    env = Environment(loader=loader, autoescape=auto_escape)
    template = env.get_template("email.html")
    return template.render(**data)


def notify_email(data: dict):
    if NOTIFY_DRY_RUN:
        with NamedTemporaryFile(mode='w',
                                encoding='utf-8',
                                suffix='.htm',
                                delete=False) as f:
            f.write(render_template(data))
            webbrowser.open(f.name)
        return

    print('[*] Sending e-mail notification...')
    client = AcsClient(ALIYUN_ACCESS_ID, ALIYUN_ACCESS_SECRET)
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
    request.add_query_param('ToAddress', NOTIFY_EMAIL)
    request.add_query_param('FromAlias', 'bjut.tech')
    request.add_query_param('HtmlBody', render_template(data))
    request.add_query_param('TagName', 'Notification')
    client.do_action_with_exception(request)
