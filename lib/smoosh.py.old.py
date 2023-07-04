#!/bin/python

#> Imports
import os, sys
import re
import requests
#</Imports

#> Header-Header # header for the header?
eprint = lambda *a,**k: print('[Smoosh]:', *a, file=sys.stderr, **k)
multiline_cstyle_comment = re.compile(r'/\*(.*?)\*/', re.DOTALL)
class SmooshHelper:
    __slots__ = ('base', 'minify')
    js_minify = (
        re.compile(r'//.*$', re.MULTILINE),
        multiline_cstyle_comment,
    )
    css_minify = (
        multiline_cstyle_comment,
        re.compile(r'\s{2,}'),
        re.compile(r'\n'),
    )
    def __init__(self, *, base, minify):
        self.base = base; self.minify = minify
        print(base)
    def fetch(self, src, addbase=True):
        if src.startswith('http://') or src.startswith('https://'):
            eprint(f'Fetching remote {src}')
            return requests.get(src).text
        if addbase: src = os.path.join(self.base, src)
        eprint(f'Fetching local {src}')
        with open(src) as f: return f.read()
    def script(self, src, defer=False, module=False):
        body = self.fetch(src)
        if defer:
            body = f'addEventListener(()=>{{{body}}})'
        if self.minify:
            for r in self.js_minify: body = r.sub('', body)
        body = patterns['js_import'].sub(lambda m: self.jsimport(m.group(1)), body)
        return f'''<script{module and ' type="module"'}>/*{src}*/{body}</script>'''
    def jsimport(self, src):
        body = self.fetch(src)
        if self.minify:
            for r in self.js_minify: body = r.sub('', body)
        return f'{{{body}}}'
    def style(self, src):
        body = self.fetch(src)
        if self.minify:
            for r in self.css_minify: body = r.sub('', body)
        return f'<style>/*{src}*/{body}</style>'
patterns = {
    ## misc
    'js_comment': re.compile(r'^\s*//.*$', re.MULTILINE),
    'html_comment': re.compile('<!--.*?-->', re.DOTALL),
    'newline': re.compile(r'\n'),
    'leading_trailing_whitespace': re.compile(r'([^\S\n]+$)|(^[^\S\n]+)', re.MULTILINE),
    'complex_whitespace': re.compile(r'$\s+^\s+', re.MULTILINE),
    ## tags
    'basic_script': re.compile('<script src=["\']([^"\']+)["\']>.*?</script>', re.DOTALL),
    'module_script': re.compile('<
    'deferred_script': re.compile('</script src=["\']([^"\']+)["\']>.*?</script>', re.DOTALL),
    'js_import': re.compile(r'''import[\(\s]["']([^"']+)["'][[\)\s]'''),
    'style': re.compile(r'''<link\s+rel=["']stylesheet["']\s+href=["']([^"']+)["']>'''),
}
patterns_repl_nothing = ('js_comment',
                         'html_comment',
                         'leading_trailing_whitespace',
                         'newline',
                         'complex_whitespace'
)
patterns_repl_nothing = ()
#</Header-Header

#> Header >/
def smoosh(path, minify=True):
    h = SmooshHelper(base=os.path.dirname(path), minify=minify)
    html = h.fetch(path, False)
    if minify:
        for k in patterns_repl_nothing:
            html = patterns[k].sub('', html)
    html = patterns['basic_script'].sub(lambda m: h.script(m.group(1)), html)
    html = patterns['deferred_script'].sub(lambda m: h.script(m.group(1), True), html)
    html = patterns['js_import'].sub(lambda m: h.jsimport(m.group(1)), html)
    html = patterns['style'].sub(lambda m: h.style(m.group(1)), html)
    return html
