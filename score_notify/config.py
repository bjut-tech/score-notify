from environs import Env

_env = Env()
_env.read_env()

CAS_USERNAME = _env.str("CAS_USERNAME")
CAS_PASSWORD = _env.str("CAS_PASSWORD")

NOTIFY_EMAIL = _env.str("NOTIFY_EMAIL", default=None)
NOTIFY_DRY_RUN = _env.bool("NOTIFY_DRY_RUN", default=False)

ALIYUN_ACCESS_ID = _env.str("ALIYUN_ACCESS_ID", default=None)
ALIYUN_ACCESS_SECRET = _env.str("ALIYUN_ACCESS_SECRET", default=None)
if NOTIFY_EMAIL and (not ALIYUN_ACCESS_ID or not ALIYUN_ACCESS_SECRET):
    raise ValueError("ALIYUN_ACCESS_ID and ALIYUN_ACCESS_SECRET must be set when NOTIFY_EMAIL is set.")

PROXY_URL = _env.str("HTTP_PROXY", default=None)
