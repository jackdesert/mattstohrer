import os
from dataclasses import dataclass

import ipdb
import requests
from bs4 import BeautifulSoup

DOMAIN = 'https://www.stohrermusic.com'

@dataclass(frozen=True)
class Link:
    href: str
    text: str

    def internal(self):
        """
        If this a link to a page on Matt's site, return True.
        Otherwise, return False.
        """
        return (DOMAIN in self.href)

class Page:

    def __init__(self, path):
        self.path = path

    def fetch(self):
        url = os.path.join(DOMAIN, self.path)
        req = requests.get(url)
        doc = BeautifulSoup(req.text)
        links = []
        for anchor in doc.find_all('a'):
            href = anchor.get('href')
            if href.startswith('#'):
                print('skipping because href is #')
                continue
            text = anchor.text
            link = Link(href, text)
            links.append(link)

        ipdb.set_trace()
        1


if __name__ == '__main__':
    base = Page('')
    base.fetch()
