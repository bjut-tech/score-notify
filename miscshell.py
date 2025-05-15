"""
Python interactive shell with JwMisc set up

Run with: `python -i miscshell.py`
"""

from bjut_tech import ConfigRegistry
from httpx import Client

from bjut_tech.auth import JwglxtAuthentication
from bjut_tech.tunnel import TunnelSelector
from score_notify import JwMisc

session = Client(headers={
    'User-Agent': 'Mozilla/5.0'
}, verify=False)
config = ConfigRegistry()
tunnel = TunnelSelector(session, config).get_best()
base_url = config.get('JW_BASE_URL', 'https://jwglxt.bjut.edu.cn')
username = config['CAS_USERNAME']
password = config.get('JW_PASSWORD', config['CAS_PASSWORD'])
auth = JwglxtAuthentication(tunnel, base_url, username, password)
auth.authenticate()
misc = JwMisc(tunnel, base_url)
