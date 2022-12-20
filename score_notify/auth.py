from io import BytesIO
from xml.etree import ElementTree

import rsa
from requests import Session
from requests.exceptions import RequestException
from school_sdk import UserClient, SchoolClient

from .config import CAS_USERNAME, CAS_PASSWORD, PROXY_URL
from .mp import patch_proxy, patch_session

CONNECT_DIRECT = {
    'host': 'jwglxt.bjut.edu.cn',
    'port': 443,
    'ssl': True
}
CONNECT_WEBVPN = {
    'host': 'jwglxt-bjut-edu-cn-s.libziyuan.bjut.edu.cn',
    'port': 8118,
    'ssl': False
}


def _login(**kwargs) -> UserClient:
    school = SchoolClient(**kwargs)
    client: UserClient = school.user_login(CAS_USERNAME, CAS_PASSWORD)

    print('[+] Login successful')
    print(f'[*] Current user: {client.get_info()["name"]}')

    return client


def login() -> UserClient:
    try:
        # try to connect directly
        return _login(**CONNECT_DIRECT)
    except RequestException:
        pass

    if PROXY_URL:
        print('[*] Unable to connect directly, retry using proxy')

        # zf-school-sdk doesn't support proxy for now, using monkey-patch
        patch_proxy(PROXY_URL)

        return _login(**CONNECT_DIRECT)
    else:
        print('[*] Unable to connect directly, retry using webvpn')

        # login to webvpn
        session = Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
        })

        response = session.get('https://libziyuan.bjut.edu.cn/por/login_auth.csp', params={
            'apiversion': 1
        }, stream=True)
        response.raise_for_status()

        etree = ElementTree.parse(BytesIO(response.content))
        csrf_token = etree.find('CSRF_RAND_CODE').text
        rsa_key = etree.find('RSA_ENCRYPT_KEY').text
        rsa_exp = etree.find('RSA_ENCRYPT_EXP').text

        pub_key = rsa.PublicKey(int(rsa_key, 16), int(rsa_exp))
        clear_text = f'{CAS_PASSWORD}_{csrf_token}'.encode('utf-8')
        password_encrypted = rsa.encrypt(clear_text, pub_key).hex()

        response = session.post('https://libziyuan.bjut.edu.cn/por/login_psw.csp', params={
            'anti_replay': 1,
            'encrypt': 1,
            'apiversion': 1
        }, data={
            'mitm_result': '',
            'svpn_req_randcode': csrf_token,
            'svpn_name': CAS_USERNAME,
            'svpn_password': password_encrypted,
            'svpn_rand_code': ''
        })
        response.raise_for_status()
        if 'success' not in response.text:
            raise RuntimeError('Login to webvpn failed')

        # monkey-patch custom session
        patch_session(session)

        return _login(**CONNECT_WEBVPN)
