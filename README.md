The Complete Works of Matt Stohrer
==================================

Generates a complete index of all the pages on [stohrermusic.com](https://stohrermusic.com).

It does this by crawling the pages (not by using sitemap.xml.)


Where is this Hosted
--------------------

This is hosted at [mattstohrer.jackdesert.com](http://mattstohrer.jackdesert.com).

Format
------

The format is to show each page on [stohrermusic.com](https://stohrermusic.com), and grouped
with the page are any external links the page points to.

Setup
-----

    pipx install poetry
    poetry install --sync

Build
-----

    bin/build

Deploy
------

    bin/deploy
