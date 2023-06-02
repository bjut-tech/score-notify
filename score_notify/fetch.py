import pickle
import traceback
from typing import List

import oss2
from school_sdk import UserClient
from school_sdk.client import Score

from .config import ALIYUN_ACCESS_ID, ALIYUN_ACCESS_SECRET, IS_FC, NOTIFY_DRY_RUN
from .notify_email import notify_email
from .rank import Rank
from .utils import get_current_term, get_term_before

endpoint = 'https://oss-cn-beijing-internal.aliyuncs.com' if IS_FC \
    else 'https://oss-cn-beijing.aliyuncs.com'
bucket = oss2.Bucket(
    oss2.Auth(ALIYUN_ACCESS_ID, ALIYUN_ACCESS_SECRET),
    endpoint,
    'bjut-tech'
)


def _load_last():
    if bucket.object_exists('score-notify/last.bin'):
        return pickle.loads(bucket.get_object('score-notify/last.bin').read())
    else:
        return None


def _save_last(grades: List[dict]):
    bucket.put_object('score-notify/last.bin', pickle.dumps(grades))


def _fetch_grades(client: UserClient, term: dict) -> List[dict]:
    score_client = Score(client)
    score_client.load_score(**term)

    grades_all = []
    for item in score_client.raw_score.get('items', []):
        item_data = {
            'name': item.get('kcmc', ''),
            'category': (item.get('kcxzmc', ''), item.get('kcgsmc', '')),
            'score': item.get('cj', 0),
            'credit': float(item.get('xf', 0)),
            'gp': float(item.get('jd', 0)),
            'excluded': False
        }

        try:
            item_data['score'] = float(item_data['score'])
        except ValueError:
            item_data['excluded'] = True

        if item_data['category'][0] == '自主课程' or item_data['category'][1] == '第二课堂':
            item_data['excluded'] = True

        if item_data['category'][1]:
            item_data['category'] = ' / '.join(item_data['category'])
        else:
            item_data['category'] = item_data['category'][0]

        grades_all.append(item_data)

    return grades_all


def fetch_grades(client: UserClient, notify='email') -> List[dict]:
    term = get_current_term()
    grades_all = _fetch_grades(client, term)

    last = _load_last()
    if last:
        last_names = [i['name'] for i in last]
        grades_new = [i for i in grades_all if i['name'] not in last_names]
    else:
        grades_new = None

    # fetch historical grades for gpa and average score
    grades_included = []
    this_grades_all = grades_all
    while True:
        grades_included += [i for i in this_grades_all if not i['excluded']]
        term = get_term_before(term)
        this_grades_all = _fetch_grades(client, term)

        if not this_grades_all:
            break

    # fetch current rank
    try:
        rank_client = Rank(client)
        rank = rank_client.get_rank()
    except Exception:
        traceback.print_exc()
        rank = None

    data = {
        'grades_new': grades_new,
        'grades_all': grades_all,
        'score_average': round(sum([
            i['score'] * i['credit'] for i in grades_included
        ]) / sum([i['credit'] for i in grades_included]), 2) if grades_included else None,
        'gpa': round(sum([
            i['gp'] * i['credit'] for i in grades_included
        ]) / sum([i['credit'] for i in grades_included]), 2) if grades_included else None,
        'rank': rank
    }

    if grades_all == grades_new:
        data['grades_new'] = None

    if grades_new or not last or NOTIFY_DRY_RUN:
        if notify == 'email':
            notify_email(data)

    if grades_all and (grades_new or not last):
        _save_last(grades_all)

    return grades_all
