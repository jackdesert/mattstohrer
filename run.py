import hashlib
import os
from pathlib import Path
from time import sleep

import ipdb
import requests
import urllib3
from bs4 import BeautifulSoup
from jinja2 import Template

DOMAIN = 'https://www.stohrermusic.com/'
PAGES = {}
TITLE = 'The Complete Works of Matt Stohrer'
OUTPUT_FNAME = 'index.html'

# Use a common user agent so some sites like theowanne.com will return 200 instead of 403
USER_AGENT = (
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1'
)


class CacheUtil:
    """
    Utils for caching.
    Note this is a separate class so it can clearly be referenced
    from other modules.
    """

    CACHE_DIR = 'cache'
    # Create cache directory
    Path(CACHE_DIR).mkdir(exist_ok=True)

    @classmethod
    def fname(cls, url):
        """
        builds the sha256 of `url`
        """
        sha = hashlib.sha256()
        sha.update(url.encode())
        return os.path.join(cls.CACHE_DIR, sha.hexdigest())

    @classmethod
    def invalidate(cls, url):
        """
        Invalidate the cache for this url
        """

        fname = cls.fname(url)
        try:
            os.unlink(fname)
            print(f'Invalidated cache for {url}')
        except FileNotFoundError:
            print(f'ERROR: Not found in cache: {url}')


class Fetchable:
    """
    Abstract class that supports fetching a url and storing it
    in filesystem cache for future retrieval.
    """

    def __init__(self):
        raise TypeError('Do not instantiate directly. Subclass instead')

    @property
    def url(self):
        raise TypeError('Subclass must overwrite this method')

    @property
    def _cache_fname(self):
        return CacheUtil.fname(self.url)

    def _fetch(self):
        """
        First attempt to read from filesystem cache.
        Otherwise fetch from the internet
        """
        try:
            # First attempt to read from cache
            with open(self._cache_fname, encoding=UTF8) as reader:
                return reader.read()
        except FileNotFoundError:
            # Fetch from network
            pass

        print(f'fetching {self.url}')
        headers = {'User-agent': USER_AGENT}
        sleep(1)
        try:
            req = requests.get(self.url, headers=headers, verify=False, timeout=60)
            text = req.text
        except (
            requests.exceptions.InvalidSchema,
            requests.exceptions.InvalidURL,
            requests.exceptions.ConnectionError,
            urllib3.exceptions.NewConnectionError,
        ) as exc:
            # Set the title to show up
            text = f'<head><title content="ERROR: {exc}" /></head>'
        # Save to cache for next time
        with open(self._cache_fname, 'w', encoding=UTF8) as writer:
            writer.write(text)
        return text


class Link(Fetchable):
    href: str
    text: str

    __slots__ = ('href', 'text')

    def __init__(self, href, text):
        self.href = href
        self.text = text
        self.title = self.fetch_title()

    def is_internal(self):
        """
        If this a link to a page on Matt's site, return True.
        Otherwise, return False.
        """
        return DOMAIN in self.href

    @property
    def url(self):
        return self.href

    def fetch_title(self):
        """
        Fetch the url and return the page <title>
        """
        html = self._fetch()
        doc = BeautifulSoup(html, features='lxml')
        if doc is None or (len(doc) == 0):
            return '(Broken Link)'
        if not doc.title:
            return f'{self.url} (No title)'
        title = doc.title.text
        print(f'{self.href}: {title}')
        return title


class Page(Fetchable):

    __slots__ = (
        'path',
        'external_links',
        'title',
    )

    def __init__(self, path):
        if path.startswith(DOMAIN):
            path = path.replace(DOMAIN, '', 1)
        self.path = path
        self.external_links = []
        self.title = None

    def fetch_and_process(self):
        """
        Fetch the contents of this page

        [This is a recursive function!]

        Find all the anchors (links) in the page.
        If an anchor represents another page, create it
        and add it to PAGES.
        """

        text = self._fetch()
        doc = BeautifulSoup(text, features='lxml')
        self.title = doc.title.text.replace(' – Stohrer Music', '')
        for anchor in doc.find_all('a'):
            href = anchor.get('href')
            if (
                href is None
                or href.startswith('#')
                or href.endswith('.png?ssl=1')
                or href.endswith('.png')
                or href.endswith('.gif')
                or href.endswith('.jpg')
                or href.endswith('.jpg?ssl=1')
                or href.endswith('.JPG')
                or href.endswith('.jpeg')
                or href == 'https://generatepress.com'
            ):
                print(f'    skipping because href is {href}')
                continue

            # Remove `#` anchor from the end of the link for deduplication
            href = href.split('#')[0]

            # Remove references from amazon links
            href = href.split('ref=')[0]

            if href == '':
                href = 'https://www.stohrermusic.com'

            text = anchor.text
            link = Link(href, text)
            if not link.is_internal():
                # Link is external so store in external links
                self.external_links.append(link)
                continue
            if link.href not in PAGES:
                # Create a new page and add it to PAGES
                print(f'{len(PAGES)} Adding {link.href} to PAGES')
                new_page = type(self)(link.href)
                PAGES[link.href] = new_page
                new_page.fetch_and_process()

    @property
    def url(self):
        return os.path.join(DOMAIN, self.path)


def fetch_all():
    base = Page(DOMAIN)
    PAGES[DOMAIN] = base
    base.fetch_and_process()


def build_page():
    html = template().render(title=TITLE, pages=sorted(PAGES.items()))
    with open(OUTPUT_FNAME, 'w') as writer:
        writer.write(html)
    print(f'Output written to {OUTPUT_FNAME}')


def template():
    return Template(
        '''<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='utf-8'>
    <meta http-equiv='X-UA-Compatible' content='IE=edge'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <meta name='description' content='Comprehensive list of all saxophone repair articles by Matt Stohrer of stohrermusic.com, in alphabetical order by url.'>
    <meta name='keywords' content='saxophone, saxophone repair, matt stohrer, open source saxophone, woodwind repair, keywork, saxophone pad'>
    <meta name='author' content='Jack Desert'>
    <meta name='google-site-verification' content='PLwz_aDDCHG0XBwbGlwZ48Il-jQOHbQpN7-LqkfDhCc' />
    <title>{{ title }}</title>
</head>
<style>
html{
    font-size: 18px;
    font-family: roman;
}
html,div,ul,ol,h1,h2,h3{
    margin: 0;
    padding: 0;
    font-size: 1rem;
}
h1{
    font-size: 2rem;
}
p{
    max-width: 40rem;
}
ul,ol{
    list-style-position: inside;
}
.odd{
    background: #ddd;
}
.page{
    padding: 0.5rem;
    font-size: 1.3rem;
}
.elink{
    font-size: 1.1rem;
    padding-left: 2rem;
    font-family: arial;
    margin-top: 0.4rem;
}
.footer{
    margin: 2rem 0;
}
</style>
</head>

<body>
<main>
    <h1>{{ title }}</h1>
    <p>
    An easy reference to each and and every page on
    <a href='https://stohrermusic.com'>stohrermusic.com</a>, in alphabetical order by url.
    </p>
    <p>
    Happy saxophone repairing!
    </p>
    <ol>
    {% for url, page in pages %}
    <div class='page {{ loop.cycle("odd", "even") }}'>
    Page {{ loop.index }}: {{ page.title }}
    <div class='url'><a href='{{ url }}'> {{ url }} </a></div>
    {% if page.external_links %}
        <div class='elink'>External links:</div>
    {% endif %}
        <ul>
            {% for link in page.external_links %}
                <li class='elink'><a href='{{ link.href }}'>{{ link.href }}</a> &nbsp;  "{{ link.title }}"</li>
            {% endfor %}
        </ul>
    </div>
    {% endfor %}
    </ol>
</main>
<hr />
<div class='footer'>
This page was generated by a plucky python script which is available at <a href='https://github.com/jackdesert/mattstohrer'>github.com/jackdesert/mattstohrer</a>
</div>
</body>
    '''
    )


if __name__ == '__main__':
    fetch_all()
    build_page()
