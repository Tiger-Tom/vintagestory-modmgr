#> Setup PyI_Splash
def _pyi_splash(text_or_cmd: str | bool) -> bool | Exception:
    # False closes splash, str updates text; returns success or exception
    if not pyi_splash.is_alive(): return False
    try:
        if text_or_cmd is False:
            pyi_splash.close(); return True
        if 'os' in dir():
            text_or_cmd += f'\n{getattr(os, "getlogin", lambda: "(login name unknown)")()} | {os.getcwd()}'
            if hasattr(os, 'uname'): text_or_cmd += f'\n{os.uname()}'
            else: text_or_cmd += 'os.name'
        if 'sys' in dir():
            text_or_cmd += f'\n{" ".join(sys.argv)}'
        pyi_splash.update_text(text_or_cmd)
        return True
    except Exception as e: return e
#</Setup PyI_Splash

#> Imports
import sys, os                 # basic system libraries
import importlib.machinery     # import GU/API modules
import argparse                # typehints
try: import webview            # HTML/CSS/JS GUI
except Exception as e: webview = e
try:
    import pyi_splash          # PyInstaller splash screen
    splash = _pyi_splash
except ModuleNotFoundError: splash = lambda _: None
try:
    from gui import guapi      # default Graphical User / Application Protocol Interface
except Exception as e: guapi = e
from lib.basemod import Mod
from lib.smoosh import smoosh
#</Imports

#> Setup
eprint = lambda *a, **kw: print(*a, **kw, file=sys.stderr)

am_frozed = getattr(sys, 'frozen', False)
builtin_gui_dir = os.path.join('gui', 'index.html') if not am_frozed else os.path.join(sys._MEIPASS, 'gui', 'index.html')
has_builtin_gui = os.path.exists(builtin_gui_dir)
#</Setup

#> Base Hooks
class BaseHook:
    __slots__ = ('ns', 'frozen', 'splash', 'Mod', 'guapi', 'webview')
    def __init__(self, ns: argparse.Namespace, is_frozen: bool, splash=splash):
        self.ns = ns; self.Mod = Mod; self.frozen = is_frozen
        self.guapi = None; self.window = None; self.webview = None
        eprint(f'Hook instantiated; frozen?: {is_frozen}'); self.splash = splash
        self.splash('Hooks have been set up and will take control of splashes')
    def pre_api_create(self):
        '''called before the GU/API, returns kwargs for GUAPI.__init__'''
        eprint('GU/API about to be created'); self.splash('Setting up GU/API')
        return {}#{'initial_dir': initial_dir}
    def post_api_create(self, guapi: 'GUAPI'):
        '''called after the GU/API is created'''
        eprint(f'GU/API created: {guapi}'); self.splash('Finished setting up GU/API')
        self.guapi = guapi
    def pre_window_created(self):
        '''called before webview.create_window, return value updates default kwargs'''
        eprint('Window about to be created'); self.splash('Setting up window')
        return {}
    def post_window_created(self, w: 'webview.Window'):
        '''called after webview.create_window'''
        eprint(f'Window created: {w}'); self.splash('Finished setting up window')
    def pre_webview_start(self, wv: 'webview'):
        '''called before webview.start, return value updates default kwargs'''
        eprint(f'WebView about to start: {wv}'); self.splash('Setting up Python WebView')
        self.webview = wv
        return {}
    def as_webview_start(self):
        '''called by webview.start as func=, unless it was overridden by pre_webview_start'''
        eprint(f'WebView is starting/ed'); self.splash('Python WebView started')
        self.splash(False)
    def post_webview_start(self, wv: 'webview'):
        '''called after webview.start'''
        eprint(f'WebView was started: {wv}')
        self.webview = wv

    def uncaught_exception(self, e: Exception):
        '''called whenever an uncaught exception occurs during any of the following:
            self.pre_api_create
            GUAPI.__init__
            self.post_api_create
            self.pre_window_created
            webview.create_window
            self.post_window_created
            self.pre_webview_start
            webview.start
            self.post_webview_start'''
        eprint(f'Uncaught exception: {e}')
        raise e
#</Base Hooks

#> Header >/
if os.name == 'nt': cache_err = 'you are running Windows'
else:
    cache_dir_base = os.path.expanduser(f'~/.cache/{os.path.basename(sys.argv[0])}')
    if os.path.exists(f'{cache_dir_base}/CacheStorage') and os.path.exists(f'{cache_dir_base}/WebKitCache'):
        cache_err = False
    else: cache_err = f'{cache_dir_base} does not appear to exist'
def add_arguments(p: argparse.ArgumentParser):
    splash('Parsing arguments')
    if webview is False:
        p.description = 'GUI mode cannot be used without webview. Try `pip install webview` or otherwise installing python-pywebview?'
        return
    if has_builtin_gui:
        p.add_argument('-g', '--gui', metavar='path', default=builtin_gui_dir, help='The GUI file (or URI) to serve, defaults to the stored GUI in a bundled executable or the builtin GUI at gui/index.html')
    else: p.add_argument('-g', '--gui', metavar='path', required=True, help='The GUI file (or URI) to serve')
    p.add_argument('-s', '--http-server', metavar='port', default=False, type=int, help='If provided, the web GUI and API will be served on a local HTTP server at the port (not recommended due to security concerns)')
    p.add_argument('-d', '--debug', action='store_true', help='Start PyWebView with debug=True, opening/enabling inspect tools and JS console')
    if not cache_err: p.add_argument('--clear-cache', action='store_true', help=f'Tries to clear the cache by removing {cache_dir_base}')
    else: p.add_argument('--clear-cache', action='store_const', const=False, default=False, help=f'Would clear the cache, but currently has no effect because {cache_err}')
    p.add_argument('--guapi', '--api', default=None, help='The Python module of the API to provide to the GUI (GU/API) (defaults to modes/guapi.py). Additionally, this file provides hooks that can modify the way the program behaves in various ways')
    p.add_argument('--no-inline', action='store_true', help='Don\'t speed up loading times by inlining certain parts of the main HTML page')
    p.add_argument('--no-minify', action='store_true', help='Don\'t minify during inlining (has no affect when used with --no-inline) (most minifying requires the css-html-js-minify package)')
    p.add_argument('--backend', choices=('cef', 'qt', 'gtk'), default=None, help='The backend to use for rendering (one of "cef", "qt", "gtk") (default depends on webview)')
    p.add_argument('flags', nargs='*', help='Flags to pass to the webapp through the GU/API')
    #p.add_argument('initial_dir', metavar='path', nargs='?', default=None, help='The directory to start in (optional)')
def command(ns: argparse.Namespace):
    splash('Loading GUI')
    # Remove cache if needed
    splash('Checking if cache needs to be removed')
    if ns.clear_cache:
        splash('Removing cache')
        import shutil
        for c in (f'{cache_dir_base}/CacheStorage', f'{cache_dir_base}/WebKitCache'):
            eprint(f'Clearing cache: deleting {c}'); splash(f'Removing cache: {c}')
            shutil.rmtree(c)
    # Check for errors
    splash('Verifying')
    if isinstance(webview, Exception):
        eprint('Cannot execute GUI, Python WebView does not appear to have been installed or properly loaded:'); eprint(webview)
        splash('Python WebView was not installed or properly loaded'); exit(2)
    if not os.path.exists(ns.gui):
        eprint(f'{ns.gui} does not exist, can not continue')
        splash(f'{ns.gui} does not exist, can not continue'); exit(1)
    # Get GU/API
    splash('Loading GU/API')
    if ns.guapi is None:
        splash('Loading builtin GU/API')
        gpi = guapi
        if isinstance(gpi, Exception):
            eprint('Builtin GU/API could not be loaded:'); eprint(gpi)
            splash('Builtin GU/API could not be loaded'); exit(1);
    else:
        try:
            splash(f'Loading external GU/API from {ns.guapi}')
            gpi = importlib.machinery.SourceFileLoader('guapi', ns.guapi).load_module()
        except Exception as e:
            eprint(f'Cannot get GU/API module from {ns.guapi}:'); eprint(e)
            splash(f'External GU/API {ns.guapi} could not be loaded'); exit(1)
    splash('Setting up hooks')
    if hasattr(gpi, 'hook_factory'): hook = gpi.hook_factory(BaseHook)(ns, am_frozed, splash)
    else: hook = BaseHook(ns, am_frozed)
    if not ns.no_inline:
        eprint('Inlining'); splash('Inlining')
        gui_dir = '{}.inlined{}'.format(*os.path.splitext(ns.gui))
        with open(gui_dir, 'w') as f:
            f.write(smoosh(ns.gui, not ns.no_minify))
    else: gui_dir = ns.gui
    try:
        splash('Setting up GU/API')
        ga = gpi.GUAPI(**({'mod': Mod, 'debug': ns.debug} | hook.pre_api_create())); hook.post_api_create(ga)
        splash('Creating window')
        hook.post_window_created(webview.create_window(**({'url': gui_dir, 'js_api': ga} | hook.pre_window_created())))
        webview.start(**{'func': hook.as_webview_start, 'debug': ns.debug, 'http_server': (ns.http_server is not None), 'http_port': ns.http_server, 'gui': ns.backend} | hook.pre_webview_start(webview))
        hook.post_webview_start(webview)
    except Exception as e: hook.uncaught_exception(e)
    if not ns.no_inline:
        try: os.remove(gui_dir)
        except Exception: pass
