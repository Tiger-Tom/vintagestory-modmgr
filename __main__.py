#!/bin/python

#> Imports
import argparse # argument handling

from modes import update
from modes import import_export as impexp
from modes.gui import GUI
#</Imports

#> Main >/
def main():
    p = argparse.ArgumentParser('vintagestory-modmgr', description='Update and share Vintage Story mods')
    sp = p.add_subparsers(dest='mode')
    update.add_arguments(sp.add_parser('update', help='Get updates from the ModDB for a folder of mods'))
    impexp.add_export_arguments(sp.add_parser('export', help='Export your modlist for somebody else (or you) to import later'))
    impexp.add_import_arguments(sp.add_parser('import', help='Import somebody else\'s exported modlist'))
    GUI.add_arguments(sp.add_parser('gui', help='Interactive GUI'))
    args = p.parse_args()
    {'update': update.command, 'import': impexp.import_command, 'export': impexp.export_command, 'gui': GUI.command, None: GUI.command}[args.mode](args)
if __name__ == '__main__': main()
