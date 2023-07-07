#> Imports
import sys                            # basic system libraries
from pathlib import Path              # path manipulation
import argparse                       # type hinting
from packaging.version import Version # version comparison

from lib.basemod import Mod
#</Imports

#> Header >/
eprint = lambda *a, **kw: print(*a, **kw, file=sys.stderr)

def add_arguments(p: argparse.ArgumentParser):
    p.add_argument('-u', '--unattended', action='store_true', help='Don\'t ask for user input before selecting mod candidates or removing files')
    p.add_argument('-t', '--threads', default=8, metavar='threads', type=int, help='How many threads to use for querying mod information and downloading mods (0 is infinite) (default: 8)')
    p.add_argument('-e', '--error-behavior', metavar='mode', choices=('ask', 'ignore', 'fail'), default='ask', help='How to behave when an error is encountered (default: "ask")')
    p.add_argument('--api-url', metavar='url', default='https://mods.vintagestory.at/api/mod/{}', help='The URL for querying mod information from, replacing "{}" with the mod\'s ID (default: "https://mods.vintagestory.at/api/mod/{}")')
    p.add_argument('--file-url', metavar='url', default='https://mods.vintagestory.at/{}', help='The base URL for downloading files, replacing "{}" with the mod API\'s "mainfile" value (default: "https://mods.vintagestory.at/{}")')
    p.add_argument('path', default=Path.cwd(), nargs='?', type=Path, help='Where the mods are (defaults to ".", AKA current directory)')

def command(ns: argparse.Namespace):
    mods = []
    miter = Mod.from_directory(ns.path)
    eprint('Searching for mods')
    for m,p in miter:
        if isinstance(m, Mod): mods.append(m)
        else:
            eprint(m)
            match ns.error_behavior:
                case 'ask':
                    eprint(f'Could not read mod info for {p.name}. Continue (Y/n), or retry (r)? >', end='')
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
    metas = Mod.multiget_upstream_releases(mods, nthreads=ns.threads, url=ns.api_url,
        callback_start=lambda m: eprint(f'Fetching mod info for {m.id}'), callback_done=lambda m: eprint(f'Got mod info for {m.id}'))
    candidates = {}
    for m,rs in metas:
        for r in rs:
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
        if v.startswith('q'): continue
        try:
            v = int(v)
            if not (0 <= v < len(cs)): raise ValueError
        except ValueError:
            eprint('Illegal or no value entered, selecting 0 (most recent)')
            v = 0
        updates[m] = cs[v]
    if not ns.unattended:
        for m,r in tuple(updates.items()):
            eprint(f'Install {ns.file_url.format(r["mainfile"])} to {ns.path / r["filename"]}? (y/N) >', end='')
            if input().lower() != 'y': del updates[m]
    if not len(updates):
        eprint('Nothing to do - no updates were selected'); return
    eprint(f'{len(updates)} update(s) to apply')
    Mod.multidownload(tuple(r['mainfile'] for r in updates.values()), ns.file_url, ns.path / '{}', nthreads=ns.threads, callback_start=lambda f,d: eprint(f'Downloading {f} to {d}'), callback_done=lambda f,d: eprint(f'Downloaded {f} to {d}'))
    for m in updates.keys():
        eprint(f'Removing old mod {m.source}')
        m.source.unlink()
