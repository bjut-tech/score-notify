from __future__ import annotations

import time
from math import floor
from typing import TYPE_CHECKING, Tuple, Optional

from bs4 import BeautifulSoup

from bjut_tech.utils import get_current_term

if TYPE_CHECKING:
    from bjut_tech.persistence import AbstractPersistenceProvider
    from bjut_tech.tunnel import AbstractTunnel


class GradesFetcher:

    def __init__(
        self,
        tunnel: AbstractTunnel,
        persistence: AbstractPersistenceProvider,
        base_url: str
    ):
        self.tunnel = tunnel
        self.persistence = persistence
        self.base_url = base_url

        self.uid = self.get_uid()
        self.persistence_key = f'score-notify/{self.uid}/last.bin'

    def __call__(self):
        grades_last = self.persistence.load(self.persistence_key)
        if grades_last is None:
            grades_last = []

        grades_current = self._process_duplicates(self.get_grades(get_current_term()))
        grades_new = []
        for grade in grades_current:
            for last in grades_last:
                if grade['id'] == last['id']:
                    if grade['score'] != last['score']:
                        grades_new.append(grade)
                    break
            else:
                grades_new.append(grade)

        if len(grades_new) > 0:
            self.persistence.save(self.persistence_key, grades_current)
        else:
            grades_new = None

        grades_all = self._process_duplicates(self.get_grades_all())
        grades_included = [i for i in grades_all if i['included']]

        if len(grades_included) > 0:
            score_average = round(sum([
                i['score'] * i['credit'] for i in grades_included
            ]) / sum([i['credit'] for i in grades_included]), 2)
            score_average_1 = round(sum([
                i['score_1'] * i['credit'] for i in grades_included
            ]) / sum([i['credit'] for i in grades_included]), 2)
            gpa = round(sum([
                i['gp'] * i['credit'] for i in grades_included
            ]) / sum([i['credit'] for i in grades_included]), 2)
        else:
            grades_included = None
            score_average = None
            score_average_1 = None
            gpa = None

        return {
            'grades_new': grades_new,
            'grades_current': grades_current,
            # 'grades_included': grades_included,
            'score_average': score_average,
            'score_average_1': score_average_1,
            'gpa': gpa
        }

    def get_uid(self) -> str:
        session = self.tunnel.get_session()
        url = self.tunnel.transform_url(f'{self.base_url}/xtgl/index_initMenu.html')

        response = session.get(url, params={
            '_t': floor(time.time() * 1000)
        }, follow_redirects=False)
        if response.status_code != 200:
            raise RuntimeError('Invalid session')

        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.find('input', {'id': 'sessionUserKey'}).get('value')

    def get_grades(self, term: Optional[Tuple[int, int]]) -> list:
        year_code = term[0] if term is not None else ''
        term_code = ({1: '3', 2: '12'}[int(term[1])]) if term is not None else ''

        session = self.tunnel.get_session()
        url = self.tunnel.transform_url(f'{self.base_url}/cjcx/cjcx_cxXsgrcj.html')

        response = session.post(url, params={
            'doType': 'query',
            'gnmkdm': 'N305005'
        }, data={
            'xnm': year_code,
            'xqm': term_code,
            '_search': 'false',
            'nd': floor(time.time() * 1000),
            'queryModel.showCount': 5000,
            'queryModel.currentPage': 1,
            'queryModel.sortName': '',
            'queryModel.sortOrder': 'asc',
            'time': 0
        })
        response.raise_for_status()

        data = response.json()['items']
        return [{
            'id': i['kch_id'],
            'name': i.get('kcmc', ''),
            'category': (i.get('kcxzmc', ''), i.get('kcgsmc', '')),
            'score': int(i.get('bfzcj', 0)),
            'is_score_1': i.get('ksxz') == '正常考试',  # TODO: 正考的缓考也应该算做正考，不知道是否正确处理
            'credit': float(i.get('xf', 0)),
            'gp': float(i.get('jd', 0)),
            'included': self._is_included(i)
        } for i in data]

    def get_grades_all(self) -> list:
        return self.get_grades(None)

    @staticmethod
    def _process_duplicates(grades: list) -> list:
        # 处理重复项：
        # - 若有一门课程多次考试，只保留最高分
        # - `score_1` 永远存储正考成绩

        grade_dict = {}
        for grade in grades:
            if grade['id'] not in grade_dict:
                # 没见过这门课，保留成绩
                grade_dict[grade['id']] = grade
                grade_dict[grade['id']]['score_1'] = grade['score']
            else:
                # 已经保存过这门课的一个成绩，处理重复项
                try:
                    if grade['score'] > grade_dict[grade['id']]['score']:
                        # 如果本次考试成绩大于先前保存的成绩
                        # 应该覆盖先前的成绩；但如果这次不是正考成绩，保留先前的正考成绩
                        if not grade['is_score_1']:
                            grade['score_1'] = grade_dict[grade['id']]['score_1']
                        grade_dict[grade['id']] = grade
                    elif grade['is_score_1']:
                        # 本次考试不是最高的一次，但是是正考
                        # 保存本次成绩为正考成绩
                        grade_dict[grade['id']]['score_1'] = grade['score']
                except KeyError or ValueError:
                    pass

        for grade in grade_dict.values():
            if 'is_score_1' in grade:
                del grade['is_score_1']

        return list(grade_dict.values())

    @staticmethod
    def _is_included(grade: dict) -> bool:
        # 检查课程是否纳入加权计算
        # 辅修、微专业等不纳入（只有主修纳入）
        if grade.get('kcbj') != '主修':
            return False
        # 自主课程、第二课堂、创新创业课程不纳入
        for i in ['自主课程', '第二课堂', '创新创业']:
            if i in grade.get('kcxzmc', '') or i in grade.get('kcgsmc', ''):
                return False
        return True
