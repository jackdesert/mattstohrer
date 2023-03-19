import os
import hashlib
from dataclasses import dataclass

from pathlib import Path
import ipdb
import requests
from bs4 import BeautifulSoup

DOMAIN = 'https://www.stohrermusic.com/'
PAGES = {}

@dataclass(frozen=True)
class Link:
    href: str
    text: str

    def is_internal(self):
        """
        If this a link to a page on Matt's site, return True.
        Otherwise, return False.
        """
        return (DOMAIN in self.href)

class Page:
    CACHE_DIR = 'cache'
    # Create cache directory
    Path(CACHE_DIR).mkdir(exist_ok=True)

    def __init__(self, path):
        if path.startswith(DOMAIN):
            path = path.replace(DOMAIN, '', 1)
        self.path = path
        self.external_links = []

    def fetch_and_process(self):
        """
        Fetch the contents of this page

        [This is a recursive function!]

        Find all the anchors (links) in the page.
        If an anchor represents another page, create it
        and add it to PAGES.
        """

        text = self._fetch()
        doc = BeautifulSoup(text)
        for anchor in doc.find_all('a'):
            href = anchor.get('href')
            if href is None or href.startswith('#') or href.endswith('.jpg'):
                print(f'skipping because href is {href}')
                continue
            # Remove `#` anchor from the end of the link for deduplication
            href = href.split('#')[0]

            text = anchor.text
            link = Link(href, text)
            if link.is_internal() and link.href not in PAGES:
                # Create a new page and add it to PAGES
                print(f'Adding {link.href} to PAGES')
                new_page = type(self)(link.href)
                PAGES[link.href] = new_page
                new_page.fetch_and_process()
            else:
                self.external_links.append(link)

    @property
    def url(self):
        return os.path.join(DOMAIN, self.path)

    @property
    def _cache_fname(self):
        sha = hashlib.sha256()
        sha.update(self.url.encode())
        return os.path.join(self.CACHE_DIR, sha.hexdigest())

    def _fetch(self):
        """
        First attempt to read from filesystem cache.
        Otherwise fetch from the internet
        """
        try:
            # First attempt to read from cache
            with open(self._cache_fname) as reader:
                return reader.read()
            print(f'Found {self.url} from cache')
        except FileNotFoundError:
            # Fetch from network
            print(f'fetching {self.url}')
            req = requests.get(self.url)
            text = req.text
            # Save to cache for next time
            with open(self._cache_fname, 'w') as writer:
                writer.write(text)
            return text


    def _filename(self):
        """
        To make fewer server request (and to improve speed
        while prototyping)
        """

def build_page():
    for url, page in sorted(PAGES.items()):
        pass


if __name__ == '__main__':
    home = ''
    base = Page(home)
    PAGES[home] = base
    base.fetch_and_process()
    build_page()
