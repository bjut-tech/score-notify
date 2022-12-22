from typing import List, Optional

from school_sdk import UserClient
from school_sdk.client import Score

from .config import NOTIFY_DRY_RUN
from .notify_email import notify_email
from .utils import get_current_term


def fetch_grades(client: UserClient, last: Optional[List[dict]] = None, notify='email') -> List[dict]:
    score_client = Score(client)
    score_client.load_score(**get_current_term())

    grades_all = [{
        'name': i.get('kcmc'),
        'category': i.get('kcxzmc', '') + (' / ' if i.get('kcgsmc') else '') + i.get('kcgsmc', ''),
        'score': float(i.get('cj', 0)),
        'credit': float(i.get('xf', 0)),
        'gp': float(i.get('jd', 0)),
        'excluded': i.get('kcxzmc') == '自主课堂' or i.get('kcgsmc') == '第二课堂'
    } for i in score_client.raw_score.get('items')]

    if last:
        last_names = [i['name'] for i in last]
        grades_new = [i for i in grades_all if i['name'] not in last_names]
    else:
        grades_new = None

    grades_included = [i for i in grades_all if not i['excluded']]
    data = {
        'grades_new': grades_new,
        'grades_all': grades_all,
        'score_average': round(sum([
            i['score'] * i['credit'] for i in grades_included
        ]) / sum([i['credit'] for i in grades_included]), 2),
        'sum_credit': sum([i['credit'] for i in grades_all]),
        'gpa': round(sum([
            i['gp'] * i['credit'] for i in grades_included
        ]) / sum([i['credit'] for i in grades_included]), 2)
    }

    if grades_new or not last or NOTIFY_DRY_RUN:
        if notify == 'email':
            notify_email(grades_new, grades_all)

    return grades_all
