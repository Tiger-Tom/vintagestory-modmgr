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
html_comments = re.compile(r'<!--.*?-->', re.DOTALL)
try:
    from jsmin import jsmin
    def js_minify(js):
        eprint('<JS minified>')
        return jsmin(js, quote_chars='\'"`')
except ModuleNotFoundError: js_minify = lambda x: x
def html_minify(html):
    eprint('<HTML minified>')
    return lead_trail_whitespace.sub('', html_comments.sub('', html))
def css_minify(css, strip=False):
    eprint(f'<CSS minified; {strip=}>')
    css = lead_trail_whitespace.sub('', c_style_comments.sub('', css))
    if strip: css = css_id_defn.sub('', css_class_defn.sub('', css))
    return newlines.sub('', css)
#</Minifier

#> Header
eprint = lambda *a,**k: print('[Inliner]:', *a, file=sys.stderr, **k)

def is_url(src):
    return src.startswith('https://') or src.startswith('http://')
@functools.cache
def _fetch(src, headers=()): return requests.get(src, headers=dict(headers))
def fetch(src, base='', *, text=True, headers={'accept-encoding': 'gzip'}) -> str | bytes:
    if is_url(src):
        eprint(f'Fetching remote {src}')
        r = _fetch(src, headers=tuple(headers.items()))
        if text: return r.text
        else: return r.content
    src = os.path.join(base, src)
    eprint(f'Fetching local {src}')
    with open(src, f'r{"" if text else "b"}') as f: return f.read()

class Inliner:
    __slots__ = ('base', 'minify')
    # flags
    no_inline = re.compile('noinline')
    # not flags
    pbase_attr = '=["\']([^"\']+)["\']'
    def __init__(self, base, minify):
        self.base = base; self.minify = minify
    def fetch(self, src, **kw): return fetch(src, self.base, **kw)
    def _script_tag_sub(self, m):
        if self.no_inline.search(m.group(1)): return m.group(0)
        if sm := self.script_src.search(m.group(1)): src = sm.group(1)
        else:
            body = m.group(2)
            if self.minify: body = js_minify(body)
            return f'<script{m.group(1)}>globalThis.___inlined___=1;{body}</script>'
        ismodule = self.script_is_module.search(m.group(1)) != None
        isdefer = self.script_is_defer.search(m.group(1)) != None
        body = self.inline_js(self.fetch(src), os.path.dirname(src))
        if isdefer: body = f'addEventListener("DOMContentLoaded", function(){{{body}}});'
        eprint(f'Inlining {"deferred " if isdefer else ""}{"module-typed " if ismodule else ""}script: {src}')
        return f'''<!--inlined-{'deferred-' if isdefer else ''}{'module-' if ismodule else ''}script:{src}--><script{' type="module"' if ismodule else ""}>{body}</script>'''
    script_is_module = re.compile('type=["\']module["\']')
    script_is_defer = re.compile('defer')
    script_src = re.compile(f'src{pbase_attr}')
    def _css_sub(self, m):
        eprint(f'Inlining CSS: {m.group(1)}')
        return f'<!--inlined-css:{m.group(1)}--><style>{self.inline_css(self.fetch(m.group(1)), m.group(2))}</style>'
    def inline_html(self, html):
        if self.minify: html = html_minify(html)
        html = self.script_tag.sub(self._script_tag_sub, html)
        html = self.stylesheet.sub(self._css_sub, html)
        return html
    script_tag = re.compile(r'<script([^>]*)>(.*?)</script>', re.DOTALL)
    stylesheet = re.compile(r'''<link rel=["']stylesheet["'] href=["']([^"']+)["']([^>]+)>''')
    def _import_sub(self, relative_base):
        def _import_sub_(m):
            src = os.path.join(relative_base, m.group(1))
            eprint(f'Inlining JS module: {src}')
            exports = f'__export_{hex(abs(hash(src)))}'
            body = f'((async function(){{"inlined-module:{src}"; globalThis.___inlined___=1; let {exports}={{}}; {self.inline_js(self.fetch(src), os.path.dirname(src))}; return {exports};}})())'
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
        if self.minify: css = css_minify(css, 'inline-strip' in attrs)
        if 'inline-urls' in attrs: css = self.css_url.sub(self._css_url_sub, css)
        return css
    css_url = re.compile(r'url\(["\']?(.*?)["\']?\)')
#</Header

#> Main >/
def smoosh(path, minify):
    return Inliner(os.path.dirname(path), minify).inline_html(fetch(path))
