#!/bin/python

#> Imports
import os, sys  # basic system libraries
import argparse # argument handling

from basemod import Mod
from gui.gui import GUI
#</Imports

#> Updates
def add_update_arguments(p: argparse.ArgumentParser):
    p.add_argument('-e', '--error-behavior', metavar='mode', choices=('ask', 'ignore', 'fail'), default='ask', help='How to behave when an error is encountered (default: "ask")')
    p.add_argument('-t', '--query-threads', default=0, metavar='threads', type=int, help='How many threads to use for querying mod information (default: 0, which means infinite)')
    p.add_argument('-u', '--unattended', action='store_true', help='Don\'t ask for user input before selecting mod candidates or removing files')
    p.add_argument('--api-url', metavar='url', default='https://mods.vintagestory.at/api/mod/{}', help='The URL for querying mod information from, replacing "{}" with the mod\'s ID (default: "https://mods.vintagestory.at/api/mod/{}")')
    p.add_argument('--file-url', metavar='url', default='https://mods.vintagestory.at/{}', help='The base URL for downloading files, replacing "{}" with the mod API\'s "mainfile" value (default: "https://mods.vintagestory.at/{}")')
    p.add_argument('path', default='.', nargs='?', help='Where the mods are (defaults to ".", AKA current directory)')
def cmd_update(ns: argparse.Namespace):
    eprint = lambda *a, **kw: print(*a, **kw, file=sys.stderr)
    mods = []
    miter = Mod.from_directory(ns.path)
    eprint('Searching for mods')
    for m,p in miter:
        if isinstance(m, Mod): mods.append(m)
        else:
            eprint(m)
            match ns.error_behavior:
                case 'ask':
                    eprint(f'Could not read mod info for {os.path.basename(p)}. Continue (Y/n), or retry (r)? >', end='')
                    match input().lower():
                        case 'n': exit(1)
                        case 'r': miter.send(True)
                        case _: miter.send(False)
                case 'ignore': miter.send(False)
                case 'fail': exit(1)
                case _: raise ValueError('Illegal value of "--error-behavior" detected, failing for safety')
    if not len(mods):
        eprint('Nothing to do - couldn\'t find any mods to update'); return
    eprint(f'Found {len(mods)} mod(s)')
    metas = Mod.multiget_upstream_releases(mods, ns.query_threads, ns.api_url)
    candidates = {}
    for m,releases in metas:
        for r in sorted(releases, key=lambda r: r['releaseid'], reverse=True):
            if r['modversion'] is None: continue
            if Version(r['modversion']) <= m.version: break
            if m not in candidates: candidates[m] = []
            candidates[m].append(r)
        if m not in candidates: eprint(f'{m.name} {m.version} is up to date')
    if not len(candidates):
        eprint('Nothing to do - all mods are up to date'); return
    eprint(f'{len(candidates)} mod(s) may need updates')
    updates = {}
    for m,cs in candidates.items():
        eprint(f'Update {m.name} [{m.version}] to:')
        for i,c in reversed(tuple(enumerate(cs))):
            eprint(f' [{i}] {c["modversion"]} (VS version(s) {" ".join(c["tags"])})')
        if ns.unattended: v = '0'
        else:
            eprint(f'Enter version to install (0-{len(cs)-1}), or "q" to ignore (0 is default) >', end='')
            v = input()
        if v.startswith('q'): break
        try:
            v = int(v)
            if not (0 <= v < len(cs)): raise ValueError
        except ValueError:
            eprint('Illegal or no value entered, selecting 0 (most recent)')
            v = 0
        updates[m] = cs[v]
    if not len(updates):
        eprint('Nothing to do - no updates were selected'); return
    eprint(f'{len(updates)} update(s) to apply')
    for m,r in updates.items():
        Mod.download(ns.file_url, r['mainfile'], os.path.join(os.path.dirname(m.source), r['filename']))
        if not ns.unattended:
            eprint(f'Remove old mod at {m.source} ? (y/N) >', end='')
            if not input().lower().startswith('y'): continue
        os.remove(m.source)
#</Updates

#> Main >/
def main():
    p = argparse.ArgumentParser('vintagestory-modmgr', description='Update and share Vintage Story mods')
    sp = p.add_subparsers(dest='mode', required=True)
    add_update_arguments(sp.add_parser('update', help='Get updates from the ModDB for a folder of mods'))

    args = p.parse_args()
    cmd_update(args)
    #{'update': cmd_update, 'import': cmd_import, 'export': cmd_export, 'gui': GUI.command, None: GUI.command}[args.mode](args)
if __name__ == '__main__': main()
