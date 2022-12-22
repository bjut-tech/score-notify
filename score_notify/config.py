from environs import Env

_env = Env()
_env.read_env()

CAS_USERNAME = _env.str("CAS_USERNAME")
CAS_PASSWORD = _env.str("CAS_PASSWORD")

NOTIFY_EMAIL = _env.str("NOTIFY_EMAIL", default=None)
NOTIFY_DRY_RUN = _env.bool("NOTIFY_DRY_RUN", default=False)

ALIYUN_ACCESS_ID = _env.str("ALIYUN_ACCESS_ID")
ALIYUN_ACCESS_SECRET = _env.str("ALIYUN_ACCESS_SECRET")
IS_FC = not not _env.str("FC_INSTANCE_ID", default=None)

PROXY_URL = _env.str("HTTP_PROXY", default=None)
