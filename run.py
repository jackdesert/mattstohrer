import os
from jinja2 import Template
import hashlib
from dataclasses import dataclass

from pathlib import Path
import ipdb
import requests
from bs4 import BeautifulSoup

DOMAIN = 'https://www.stohrermusic.com/'
PAGES = {}
OUTPUT_FNAME = 'index.html'


@dataclass(frozen=True)
class Link:
    href: str
    text: str

    def is_internal(self):
        """
        If this a link to a page on Matt's site, return True.
        Otherwise, return False.
        """
        return DOMAIN in self.href


class Page:
    CACHE_DIR = 'cache'
    # Create cache directory
    Path(CACHE_DIR).mkdir(exist_ok=True)

    __slots__ = ('path', 'external_links', 'title',)
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
        doc = BeautifulSoup(text)
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
                print(f'skipping because href is {href}')
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
                print(f'Adding {link.href} to PAGES')
                new_page = type(self)(link.href)
                PAGES[link.href] = new_page
                new_page.fetch_and_process()

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


def fetch_all():
    base = Page(DOMAIN)
    PAGES[DOMAIN] = base
    base.fetch_and_process()


def build_page():
    html = template().render(pages=sorted(PAGES.items()))
    with open(OUTPUT_FNAME, 'w') as writer:
        writer.write(html)
    print(f'Output written to {OUTPUT_FNAME}')


def template():
    return Template(
        '''
        <!DOCTYPE html>
        <html lang='en'>
        <head>
            <meta charset='utf-8'>
            <meta http-equiv='X-UA-Compatible' content='IE=edge'>
            <meta name='viewport' content='width=device-width, initial-scale=1.0'>
            <meta name='description' content='If you want to see each and every page that Matt Stohrer has posted on saxophone repair, this list is your boy.'>
            <meta name='author' content='Jack Desert'>
            <title>Stalking Matt Stohrer</title>
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
    <h1>Stalking Matt Stohrer</h1>
   <p>
    Matt has a lot of great content, but some of it was hard for me to find.
    What you see here is an easy reference to each and and every page on
    stohrermusic.com, in alphabetical order by url.
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
                    <li class='elink'><a href='{{ link.href }}'>{{ link.href }}</a> &nbsp;  "{{ link.text }}"</li>
                {% endfor %}
            </ul>
        </div>
    {% endfor %}
    </ol>
    <hr />
    <div class='footer'>
    This page was generated by a plucky python script which is available for reuse at <a href='https://github.com/jackdesert/stohrermusic.com'>github.com/jackdesert/stohrermusic.com</a>
    </div>
    </body>
    '''
    )


if __name__ == '__main__':
    fetch_all()
    build_page()
