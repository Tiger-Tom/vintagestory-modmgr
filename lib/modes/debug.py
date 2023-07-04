#!/bin/python

#> Imports
import os, sys
import shutil
import argparse
from lib import basemod
#</Imports

#> Header >/
def add_arguments(parser: argparse.ArgumentParser):
    parser.add_argument('--tree', default=None, help='A path to walk')
    parser.add_argument('--export', action='store_true', help='Copy frozen data (PyInstaller sys._MEIPASS) to ./_MEIPASS/')

def command(ns: argparse.Namespace):
    print(sys.version)
    print(f'{os.name}: {" ".join(getattr(os, "uname", lambda: ("{{could", "not", "get", "uname}}"))())}')
    print(f'frozen? {getattr(sys, "frozen", False)}')
    print( 'paths:')
    print(f'- cwd={os.getcwd()}')
    print(f'- _MEIPASS={getattr(sys, "_MEIPASS", "{{not set}}")}')
    print( '- source: {ns._globals["__file__"]}:')
    print(f'  - basemod module source: {basemod.__file__}')
    print(f'  - update module source: {ns._globals["update"].__file__}')
    print(f'  - import/export module source: {ns._globals["impexp"].__file__}')
    print(f'  - GUI module source: {ns._globals["gui"].__file__}')
    print(f'  - debug module source: {ns._globals["debug"].__file__}')
    print(f'- Builtin GUI dir: {ns._globals["gui"].builtin_gui_dir}')
    print(f'  - Has builtin GUI (dir exists): {ns._globals["gui"].has_builtin_gui}')
    print(f'  - GUI in frozed mode: {ns._globals["gui"].am_frozed}')
    print(f'  - GUI WebView: {ns._globals["gui"].webview}')
    print(f'  - GUI GU/API: {ns._globals["gui"].guapi}')
    print(f'  - GUI PyInstaller Splash: {getattr(ns._globals["gui"], "pyi_splash", "{{not loaded}}")}')

    if ns.tree is not None:
        for r,d,fs in os.walk(ns.tree):
            idnt = ' '*(4*r.replace(ns.tree, '').count(os.sep))
            print(f'{idnt}{os.path.basename(r)}/')
            for f in fs: print(f'{idnt}    {f}')
    if ns.export:
        if not getattr(sys, '_MEIPASS', None):
            print('Cannot export frozen data, as application wasn\'t frozen with data (sys._MEIPASS is not defined)'); exit(1)
        if not os.path.exists('./_MEIPASS'): os.makedirs('./_MEIPASS')
        base = os.path.basename(sys._MEIPASS)
        shutil.copytree(sys._MEIPASS, f'./_MEIPASS/{base}')
        print(os.path.abspath(f'./_MEIPASS/{base}'))
