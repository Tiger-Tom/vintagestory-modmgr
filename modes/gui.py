#!/bin/python

#> Imports
import sys, os                 # basic system libraries
import importlib.machinery     # import GU/API modules
import argparse                # typehints
try: import webview            # HTML/CSS/JS GUI
except Exception as e: webview = e

try:
    from modes import d_guapi  # default Graphical User / Application Protocol Interface
except Exception as e: d_guapi = e

from basemod import Mod
#</Imports

#> Setup
eprint = lambda *a, **kw: print(*a, **kw, file=sys.stderr)

am_frozed = getattr(sys, 'frozen', False)
builtin_gui_dir = os.path.join('gui', 'index.html') if not am_frozed else os.path.join(sys._MEIPASS, 'gui', 'index.html')
#</Setup

#> Base Hooks
class BaseHook:
    __slots__ = ('ns', 'Mod', 'guapi', 'window', 'webview')
    def __init__(self, ns: argparse.Namespace):
        self.ns = ns; self.Mod = Mod
        self.guapi = None; self.window = None; self.webview = None
        eprint('Hook instantiated')

    def pre_api_create(self):
        '''called before the GU/API, returns kwargs for GUAPI.__init__'''
        eprint('GU/API about to be created')
        return {}
    def post_api_create(self, guapi: 'GUAPI'):
        '''called after the GU/API is created'''
        eprint(f'GU/API created: {guapi}')
        self.guapi = guapi
    def pre_window_created(self):
        '''called before webview.create_window, return value updates default kwargs'''
        eprint('Window about to be created')
        return {}
    def post_window_created(self, w: 'webview.Window'):
        '''called after webview.create_window'''
        eprint(f'Window created: {w}')
        self.window = w
    def pre_webview_start(self, wv: webview):
        '''called before webview.start, return value updates default kwargs'''
        eprint(f'WebView about to start: {wv}')
        self.webview = wv
        return {}
    def as_webview_start(self):
        '''called by webview.start as func=, unless it was overridden by pre_webview_start'''
        eprint(f'WebView is starting/ed')
    def post_webview_start(self, wv: webview):
        '''called after webview.start'''
        eprint(f'WebView was started: {wv}')
        self.webview = wv

    def uncaught_exception(self, e: Exception):
        '''whenever an uncaught exception occurs during any of the following:
            self.pre_api_create
            guapi.GUAPI.__init__
            self.post_api_create
            self.pre_window_created
            webview.create_window
            self.post_window_created
            self.pre_webview_start
            webview.start
            self.post_webview_start'''
        eprint(f'Uncaught exception: {e}')
        input('Press enter to close') # input to allow GUI users to see error in console before it closes
        raise e
#</Base Hooks

#> Header >/
def add_arguments(p: argparse.ArgumentParser):
    if webview is False:
        p.description = 'GUI mode cannot be used without webview. Try `pip install webview` or otherwise installing python-webview?'
        return
    if os.path.exists(builtin_gui_dir):
        p.add_argument('gui_file', metavar='path', nargs='?', default=builtin_gui_dir, help='The GUI file (or URI) to serve, defaults to the stored GUI in a bundled executable or the builtin GUI at gui/index.html')
    else: p.add_argument('gui_file', metavar='path', help='The GUI file (or URI) to serve')
    p.add_argument('-s', '--http-server', metavar='port', default=False, type=int, help='If provided, the web GUI and API will be served on a local HTTP server at the port (not recommended due to security concerns)')
    p.add_argument('-d', '--debug', action='store_true', help='Start PyWebView with debug=True, opening/enabling inspect tools and JS console')
    p.add_argument('--guapi', '--api', default=None, help='The Python module of the API to provide to the GUI (GU/API) (defaults to modes/guapi.py). Additionally, this file provides ')
def command(ns: argparse.Namespace):
    # Check for errors
    if isinstance(webview, Exception):
        eprint('Cannot execute GUI, Python WebView does not appear to have been installed or properly loaded:'); eprint(webview)
        input('Press enter to close'); exit(2)
    if not os.path.exists(ns.gui_file):
        eprint(f'{ns.gui_file} does not exist, can not continue')
        input('Press enter to close'); exit(1) # input to allow GUI users to see error in console before it closes
    # Get GU/API
    if ns.guapi is None:
        guapi = d_guapi
        if isinstance(guapi, Exception):
            eprint('Builtin API could not be loaded:'); eprint(guapi)
            input('Press enter to close'); exit(1);
    else:
        try:
            guapi = importlib.machinery.SourceFileLoader('guapi', ns.api).load_module()
        except Exception as e:
            eprint(f'Cannot get GU/API module from {ns.api}:')
            eprint(e); input('Press enter to close'); exit(1)
    if hasattr(guapi, 'hook_factory'): hook = guapi.hook_factory(BaseHook)(ns)
    else: hook = BaseHook(ns)
    try:
        ga = guapi.GUAPI(**hook.pre_api_create()); hook.post_api_create(ga)
        hook.post_window_created(webview.create_window(**({'url': ns.gui_file, 'js_api': ga} | hook.pre_window_created())))
        webview.start(**{'func': hook.as_webview_start, 'debug': ns.debug, 'http_server': (ns.http_server is not None), 'http_port': ns.http_server} | hook.pre_webview_start(webview))
        hook.post_webview_start(webview)
    except Exception as e: hook.uncaught_exception(e)
