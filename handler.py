import json
import sys

from bjut_tech import ConfigRegistry
from score_notify import main

# Aliyun FC Handler for score_notify
#
# Event format:
# {
#   config?: Record<string, string | number | boolean>
#   credentials?: {
#     username: string
#     password: string
#     passwordJw?: string
#   }
# }
#
# If no config is explicitly provided,
# environment variables will be used.
#
# For all config entries, see the bjut_tech package.


def handler(event: str, context):
    try:
        request = json.loads(event)
    except Exception as e:
        if event:
            print(f'Failed to parse event: {event}', file=sys.stderr)

        request = None

    config = ConfigRegistry()
    overrides = {
        'ALIBABA_CLOUD_INTERNAL': True,
        'PERSISTENCE_TYPE': 'oss'
    }

    if isinstance(request, dict):
        if isinstance(request.get('credentials'), dict):
            overrides.update({
                'CAS_USERNAME': request['credentials'].get('username'),
                'CAS_PASSWORD': request['credentials'].get('password'),
                'JW_PASSWORD': request['credentials'].get('passwordJw')
            })
        if isinstance(request.get('config'), dict):
            overrides.update(request['config'])
    config.set_overrides(overrides)

    return main(config)
