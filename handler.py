# Aliyun FC Handler

from score_notify import login, fetch_grades


def handler(event, context):
    return fetch_grades(login())
