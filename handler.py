# Aliyun FC Handler

import pickle

import oss2

from score_notify import login, fetch_grades
from score_notify.config import ALIYUN_ACCESS_ID, ALIYUN_ACCESS_SECRET


def handler(event, context):
    bucket = oss2.Bucket(
        oss2.Auth(ALIYUN_ACCESS_ID, ALIYUN_ACCESS_SECRET),
        'https://oss-cn-beijing-internal.aliyuncs.com',
        'bjut-tech'
    )

    if bucket.object_exists('score-notify/last.bin'):
        last = pickle.loads(bucket.get_object('score-notify/last.bin').read())
    else:
        last = None

    client = login()
    result = fetch_grades(client, last)

    if result:
        bucket.put_object('score-notify/last.bin', pickle.dumps(result))
        return result
