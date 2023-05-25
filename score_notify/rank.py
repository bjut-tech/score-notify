from bs4 import BeautifulSoup
from school_sdk.client.api import BaseCrawler


class Rank(BaseCrawler):

    def get_rank(self, **kwargs) -> str:
        res = self.get('/xszzy/xszzysqgl_sbXszzysqView.html', params={
            'gnmkdm': 'N106204'
        })

        soup = BeautifulSoup(res.text, 'html.parser')
        return soup.find(id='zypm').text.strip()
