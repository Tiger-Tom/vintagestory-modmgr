#!/bin/python

#> Imports
import argparse # argument handling
import sys      # check if frozen

from modes import update
from modes import import_export as impexp
from modes import gui
from modes import debug
#</Imports

#> Main >/
def main(args = None):
    p = argparse.ArgumentParser('vintagestory-modmgr', description='Update and share Vintage Story mods')
    sp = p.add_subparsers(dest='mode')
    update.add_arguments(sp.add_parser('update', help='Get updates from the ModDB for a folder of mods'))
    impexp.add_export_arguments(sp.add_parser('export', help='Export your modlist for somebody else (or you) to import later'))
    impexp.add_import_arguments(sp.add_parser('import', help='Import somebody else\'s exported modlist'))
    gui.add_arguments(sp.add_parser('gui', help='Interactive GUI (the default)'))
    debug.add_arguments(sp.add_parser('debug', help='Shows a bunch of debug information (mostly useful for PyInstaller bundles)'))
    args,extra = p.parse_known_args(args); args._globals = globals()
    if args.mode is None:
        if gui.has_builtin_gui: return main(['--help']+extra)
        else: return main(['gui']+extra)
    return {'update': update.command, 'import': impexp.import_command, 'export': impexp.export_command, 'gui': gui.command, 'debug': debug.command}[args.mode](args)
if __name__ == '__main__': main()
