#!/bin/python

#> Imports
import os, sys
import shutil
import argparse
from lib import basemod
from lib import bundle_compat
#</Imports

#> Header >/
def add_arguments(parser: argparse.ArgumentParser):
    parser.add_argument('--tree', default=None, help='A path to walk')
    parser.add_argument('--export', action='store_true', help='Copy frozen data (PyInstaller sys._MEIPASS) to ./_MEIPASS/')

def command(ns: argparse.Namespace):
    print(sys.version)
    print(f'{os.name}: {" ".join(getattr(os, "uname", lambda: ("{{could", "not", "get", "uname}}"))())}')
    print(f'bundle info: {bundle_compat}')
    print(f' - loader: {ns._globals["__loader__"]}')
    print(f' - real BundleablePath: {bundle_compat.BundleablePath.real()}')
    print( ' - attrs:')
    if za := bundle_compat.bundle.zipapp_attrs:
        print(f'   - zipapp temp dir: {za.temp_directory}')
        print(f'   - zipapp archive: {za.archive_path}')
        print(f'   - zipapp populated tops: {za.populated_tops}')
    if fa := bundle_compat.bundle.frozen_attrs:
        print(f'   - frozen data dir: {fa.data_dir}')
    print( 'paths:')
    print(f'- cwd={os.getcwd()}')
    print(f'- source: {ns._globals["__file__"]}:')
    print(f'  - basemod module source: {basemod.__file__}')
    print(f'  - update module source: {ns._globals["update"].__file__}')
    print(f'  - import/export module source: {ns._globals["impexp"].__file__}')
    print(f'  - GUI module source: {ns._globals["gui"].__file__}')
    print(f'  - debug module source: {ns._globals["debug"].__file__}')
    print(f'- Builtin GUI dir: {ns._globals["gui"].builtin_gui_dir}')
    print(f'  - Has builtin GUI (dir exists): {ns._globals["gui"].has_builtin_gui}')
    print(f'  - GUI WebView: {ns._globals["gui"].webview}')
    print(f'  - GUI (builtin) GU/API: {ns._globals["gui"].guapi}')
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
