#!/bin/python

#> Imports
import os,sys                      # paths and sys.stderr
import re                          # pattern matching
import requests                    # fetch data
import base64, mimetypes           # inlining data URIs
from html.parser import HTMLParser # parse HTML
#</Imports

#> Header >/
eprint = lambda *a,**k: print('[Inliner]:', *a, file=sys.stderr, **k)

is_remote = lambda src: src.startswith('https://') or src.startswith('http://')
def fetch(src, *, as_bytes=False, headers={'accept-encoding': 'gzip'}) -> str | bytes:
    if is_remote(src):
        eprint(f'Fetch remote: {src}')
        r = requests.get(src, headers=headers)
        return r.content if as_bytes else r.text
    eprint(f'Fetch local: {src}')
    with open(src, f'r{"b" if as_bytes else ""}') as f: return f.read()

class Tag:
    __slots__ = ('_tag', '_attrs', '_type', 'innerHTML')
    _valueless_attr= object()
    def __init__(self, tag, *, inner='', attrs=(), type='open'):
        assert type in {'open', 'self_closing', 'declaration'}
        self._tag = tag; self._type = type
        self._attrs = dict(attrs)
        self.innerHTML = inner
    def __render_opentag(self):
        b = [self._tag]
        for attr,val in self._attrs.items():
            if val is self._valueless_attr: b.append(attr)
            else: b.append(f'{attr}={val!r}')
        return ' '.join(b)
    def __repr__(self): return self._render(data=False)
    def __str__(self): return self._render(data=True)
    def _render(self, data=True):
        match self._type:
            case 'open': return f'<{self.__render_opentag()}>{self.innerHTML if data else "..."}</{self._tag}>'
            case 'self_closing': return f'<{self.__render_opentag()} />'
            case 'declaration': return f'<!{self.innerHTML}>'
    def __getattr__(self, attr):
        if attr in self.__slots__:
            return object.__getattribute__(self, attr)
        return object.__getattribute__(self, '_attrs')[attr]
    def __setattr__(self, attr, val=_valueless_attr):
        if attr in self.__slots__:
            return object.__setattr__(self, attr, val)
        self._attrs[attr] = val
#</Header

#> Inliner >/
class Tagifier(HTMLParser):
    __slots__ = ('minify', 'tree', 'tree_up')
    def __init__(self, minify=False):
        super().__init__()
        self.minify = minify
        self.tree = [[]]; self.tree_up = None
    def __call__(self, data, data_is_uri=False):
        self.feed(data if not data_is_uri else fetch(data))
    # handlers
    def handle_decl(self, decl): self.tree.append(Tag(None, inner=decl, type='declaration'))
    def handle_starttag(self, tag, attrs):
        print(f'starttag:{tag=!r} {attrs=!r}')
        self.tree_up = self.tree
        self.tree = self.tree[-1]
    def handle_endtag(self, tag):
        print(f'endtag:{tag=!r}')
        self.tree = self.tree_up
    def handle_startendtag(self, tag, attrs):
        print(f'startendtag:{tag=!r} {attrs=!r}')
        self.tree.append(Tag(tag, attrs=attrs, type='self_closing'))
    def handle_data(self, data):
        print(f'data:{data!r}')
        t = -1
        while not isinstance(self.tree[t], Tag): t -= 1
        self.tree[t].innerHTML += data
