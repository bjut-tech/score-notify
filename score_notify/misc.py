from __future__ import annotations

from typing import TYPE_CHECKING, List, Tuple, Optional

if TYPE_CHECKING:
    from bjut_tech.tunnel import AbstractTunnel


class JwMisc:

    def __init__(
        self,
        tunnel: AbstractTunnel,
        base_url: str
    ):
        self.tunnel = tunnel
        self.base_url = base_url
        self.user = self.get_user()

    def get_user(self) -> dict:
        session = self.tunnel.get_session()
        url = self.tunnel.transform_url(f'{self.base_url}/query/query_cxXsxxPaged.html')

        response = session.get(url, follow_redirects=False)
        if response.status_code != 200:
            raise RuntimeError('Invalid session')

        data = response.json()['items'][0]
        return {
            'id': data['XH'],
            'name': data['XM'],
            'term': (data['XNM'], ({'3': 1, '12': 2}[data['XQM']])),
            'grade_id': data['NJDM_ID'],
            'major_id': data['ZYH_ID'],
            'major_name': data['ZYMC'],
            'class_id': data['BH_ID'],
            'class_name': data['BJMC']
        }

    def get_classes(self) -> List[dict]:
        session = self.tunnel.get_session()
        url = self.tunnel.transform_url(f'{self.base_url}/xtgl/comm_cxBjdmList.html')

        response = session.get(url, follow_redirects=False)
        if response.status_code != 200:
            raise RuntimeError('Invalid session')

        return [{
            'id': i['bh_id'],
            'name': i.get('bj', i.get('bh', i['bh_id'])),
            'grade_id': i['njdm_id'],
            'major_id': i['zyh_id'],
            'major_name': i.get('zymc', i.get('zyh', i['zyh_id']))
        } for i in response.json()]

    def get_schedule(self, term: Tuple[int, int], grade_id: str, major_id: str, class_id: str) -> Optional[dict]:
        session = self.tunnel.get_session()
        url = self.tunnel.transform_url(f'{self.base_url}/kbdy/bjkbdy_cxBjKb.html')

        response = session.post(url, params={
            'gnmkdm': 'N214550'
        }, data={
            'xnm': term[0],
            'xqm': ({1: '3', 2: '12'}[int(term[1])]),
            'njdm_id': grade_id,
            'zyh_id': major_id,
            'bh_id': class_id,
            'tjkbzdm': 1,
            'tjkbzxsdm': 0
        }, follow_redirects=False)
        if response.status_code != 200:
            raise RuntimeError('Invalid session')

        return response.json()
