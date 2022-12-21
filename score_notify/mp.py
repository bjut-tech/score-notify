from requests import Session
from school_sdk.client.api import BaseCrawler
from school_sdk.client.api.login import ZFLogin

original = {
    'BaseCrawer.__init__': BaseCrawler.__init__,
    'BaseCrawer.__requests': BaseCrawler._requests,
    'ZFLogin._is_login': ZFLogin._is_login
}

patched = {
    'proxy': False,
    'session': False
}


def patch_proxy(proxy_url: str):
    """
    Monkey-patch to modify functions of `zf-school-sdk` to support proxy

    Patched methods:
     - `school_sdk.client.api.BaseCrawler._requests`
    """

    # Patched method
    def BaseCrawer__requests(self, **kwargs):
        retries = 0
        while retries < 3:
            try:
                return original['BaseCrawer.__requests'](self, proxies={
                    'http': proxy_url,
                    'https': proxy_url
                }, verify=False, **kwargs)
            except Exception as e:
                retries += 1
                if retries == 3:
                    raise e

    # Apply patch
    if not patched['proxy']:
        BaseCrawler._requests = BaseCrawer__requests

    patched['proxy'] = True


def patch_session(session: Session):
    """
    Monkey-patch to modify functions of `zf-school-sdk` to apply a http session

    Patched methods:
     - `school_sdk.client.api.BaseCrawler.__init__`
     - `school_sdk.client.api.BaseCrawler._requests`
     - `school_sdk.client.api.login.ZFLogin._is_login`
    """

    # Patched method
    def BaseCrawer__init__(self, user_client):
        original['BaseCrawer.__init__'](self, user_client)
        self._http = session
    def BaseCrawer__requests(self, **kwargs):
        return original['BaseCrawer.__requests'](self, verify=False, **kwargs)
    def ZFLogin__is_login(self, _):
        return True  # Always treated as logged in

    # Apply patch
    if not patched['session']:
        BaseCrawler.__init__ = BaseCrawer__init__
        BaseCrawler._requests = BaseCrawer__requests
        ZFLogin._is_login = ZFLogin__is_login

    patched['session'] = True
