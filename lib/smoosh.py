#!/bin/python

#> Imports
import os,sys
import re; import base64
import requests; import mimetypes
import functools
#</Imports

#> Minifier
newlines = re.compile(r'\r?\n')
lead_trail_whitespace = re.compile(r'(^\s+)|(\s+$)', re.MULTILINE)
c_style_comments = re.compile(r'/\*.*?\*/', re.DOTALL)
css_class_defn = re.compile(r'^\w*?\.[^}]+}', re.MULTILINE)
css_id_defn = re.compile(r'^#[^}]+}', re.MULTILINE)
try:
    from jsmin import jsmin
    def js_minify(js):
        eprint('<JS minified>')
        return jsmin(js, quote_chars='\'"`')
except ModuleNotFoundError: js_minify = lambda x: x
def html_minify(html):
    eprint('<HTML minified>')
    return lead_trail_whitespace.sub('', html)
def css_minify(css, strip=False):
    eprint(f'<CSS minified; {strip=}>')
    css = lead_trail_whitespace.sub('', c_style_comments.sub('', css))
    if strip: css = css_id_defn.sub('', css_class_defn.sub('', css))
    return newlines.sub('', css)
#</Minifier

#> Inliner "flags"
# HTML comment flags
flag_remove = re.compile(r'^(.*?)<!--inline:remove-->(.*?)$', re.MULTILINE)
# Script attr flags
flag_no_inline = re.compile('noinline')
# CSS attr flags
flag_inline_strip = 'inline-strip'
flag_inline_urls = 'inline-urls'
#</Inliner "flags"

#> Header
eprint = lambda *a,**k: print('[Inliner]:', *a, file=sys.stderr, **k)

def is_url(src):
    return src.startswith('https://') or src.startswith('http://')
@functools.cache
def _fetch(src, headers=()): return requests.get(src, headers=dict(headers))
def fetch(src, base='', *, text=True, headers={'accept-encoding': 'gzip'}) -> str | bytes:
    if is_url(base) and not is_url(src): src = requests.compat.urljoin(base, src)
    if is_url(src):
        eprint(f'Fetching remote {src}')
        r = _fetch(src, headers=tuple(headers.items()))
        if text: return r.text
        else: return r.content
    src = os.path.join(base, src)
    eprint(f'Fetching local {src}')
    with open(src, f'r{"" if text else "b"}') as f: return f.read()

class Inliner:
    __slots__ = ('base', 'url_base', 'minify', 'skip_css_urls')
    pbase_attr = '=["\']([^"\']+)["\']'
    def __init__(self, base, minify, skip_css_urls):
        self.base = base; self.minify = minify
        self.skip_css_urls = skip_css_urls
        self.url_base = None
    def insert_info(self):
        return f'globalThis.___inlined___={"globalThis.___minified___=" if self.minify else ""}1;'
    def fetch(self, src, **kw):
        return fetch(src, self.url_base or self.base, **kw)
    def _script_tag_sub(self, m):
        if flag_no_inline.search(m.group(1)): return m.group(0)
        if sm := self.script_src.search(m.group(1)): src = sm.group(1)
        else:
            body = m.group(2)
            if self.minify: body = js_minify(body)
            return f'<script{m.group(1)}>{body}</script>'
        ismodule = self.script_is_module.search(m.group(1)) != None
        isdefer = self.script_is_defer.search(m.group(1)) != None
        body = self.inline_js(self.fetch(src), os.path.dirname(src))
        if isdefer: body = f'addEventListener("DOMContentLoaded", function(){{{body}}});'
        eprint(f'Inlining {"deferred " if isdefer else ""}{"module-typed " if ismodule else ""}script: {src}')
        return f'''<!--inlined-{'deferred-' if isdefer else ''}{'module-' if ismodule else ''}script:{src}--><script{' type="module"' if ismodule else ""}>{body}</script>'''
    script_is_module = re.compile('type=["\']module["\']')
    script_is_defer = re.compile('defer')
    script_src = re.compile(f'src{pbase_attr}')
    def _head_sub(self, m):
        eprint(f'Embedding information (___inlined___=1; ___minified___={self.minify:d})')
        return f'{m.group(0)}<script>{self.insert_info()}</script>'
    def _css_sub(self, m):
        eprint(f'Inlining CSS: {m.group(1)}')
        body = self.fetch(m.group(1))
        if is_url(m.group(1)): self.url_base = m.group(1)
        body = f'<!--inlined-css:{m.group(1)}--><style>{self.inline_css(body, m.group(2))}</style>'
        self.url_base = None; return body
    def inline_html(self, html):
        html = flag_remove.sub(r'<!--inline removed \1\2-->', html)
        if self.minify: html = html_minify(html)
        html = self.head_tag.sub(self._head_sub, html)
        html = self.script_tag.sub(self._script_tag_sub, html)
        html = self.stylesheet.sub(self._css_sub, html)
        if self.minify: html = self.html_comments.sub('', html)
        return html
    head_tag = re.compile(r'<html(?:\s.*?)?>.*?<head(?:\s.*?)?>', re.DOTALL+re.IGNORECASE)
    script_tag = re.compile(r'<script([^>]*)>(.*?)</script>', re.DOTALL)
    stylesheet = re.compile(r'''<link rel=["']stylesheet["'] href=["']([^"']+)["']([^>]*)>''')
    html_comments = re.compile(r'<!--.*?-->', re.DOTALL)
    def _import_sub(self, relative_base):
        def _import_sub_(m):
            src = os.path.join(relative_base, m.group(1))
            eprint(f'Inlining JS module: {src}')
            exports = f'__export_{hex(abs(hash(src)))}'
            body = f'((async function(){{"inlined-module:{src}"; let {exports}={{}}; {self.inline_js(self.fetch(src), os.path.dirname(src))}; return {exports};}})())'
            body = self.module_export_default.sub(rf'{exports}["default"]=\1;', f'{body}')
            if self.minify: return js_minify(body)
            return body
        return _import_sub_
    module_export_default = re.compile(r'export default ([^;]+?)(?:;|$)', re.MULTILINE)
    def inline_js(self, js, relative_base=None):
        if relative_base is None: relative_base = self.base
        js = self.import_patt.sub(self._import_sub(relative_base), js)
        if self.minify: js = js_minify(js)
        return js
    import_patt = re.compile(r'''import\(["']([^"']+)["']\)''')
    def _css_url_sub(self, m):
        mt,_ = mimetypes.guess_type(m.group(1))
        if mt is None:
            eprint(f'Could not inline CSS url("{m.group(1)}"): mimetype is unknown')
            return m.group(0)
        eprint(f'Inlining CSS url("{m.group(1)}"): {mt}')
        return f'url("data:{mt};base64,{base64.b64encode(self.fetch(m.group(1), text=False)).decode()}")'
    def inline_css(self, css, attrs):
        if self.minify: css = css_minify(css, flag_inline_strip in attrs)
        if (flag_inline_urls in attrs) and (not self.skip_css_urls): css = self.css_url.sub(self._css_url_sub, css)
        return css
    css_url = re.compile(r'url\(["\']?(.*?)["\']?\)')
#</Header

#> Main >/
def smoosh(path, minify, skip_css_urls):
    return Inliner(os.path.dirname(path), minify=minify, skip_css_urls=skip_css_urls).inline_html(fetch(str(path)))
