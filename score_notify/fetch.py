from typing import List, Optional

from school_sdk import UserClient
from school_sdk.client import Score

from .notify_email import notify_email
from .utils import get_current_term


def fetch_grades(client: UserClient, last: Optional[List[dict]] = None, notify='email') -> List[dict]:
    score_client = Score(client)
    score_client.load_score(**get_current_term())

    grades_all = [{
        'name': i.get('kcmc'),
        'category': i.get('kcxzmc', '') + (' / ' if i.get('kcgsmc') else '') + i.get('kcgsmc', ''),
        'score': i.get('cj'),
        'credit': i.get('xf'),
        'gp': i.get('jd'),
        'gpa': i.get('xfjd') if i.get('kcxzmc') != '自主课堂' and i.get('kcgsmc') != '第二课堂' else 'Excluded',
    } for i in score_client.raw_score.get('items')]

    if last:
        last_names = [i['name'] for i in last]
        grades_new = [i for i in grades_all if i['name'] not in last_names]
    else:
        grades_new = None

    if grades_new or not last:
        if notify == 'email':
            notify_email(grades_new, grades_all)

    return grades_all
