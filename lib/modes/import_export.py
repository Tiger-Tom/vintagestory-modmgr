#> Imports
import os, sys                        # basic system libraries
import argparse                       # type hinting
import json                           # load .vsmmgr files (.json files with a changed extension)
from packaging.version import Version # version comparison

from lib.basemod import Mod
#</Imports

#> Header >/
eprint = lambda *a, **kw: print(*a, **kw, file=sys.stderr)

# Import
def add_import_arguments(p: argparse.ArgumentParser):
    p.add_argument('-i', '--interactive', action='store_true', help='Ask before downloading each mod (somewhat unneeded with --auto-ask)')
    p.add_argument('-t', '--threads', default=8, metavar='threads', type=int, help='How many threads to use for querying mod information and downloading mods (0 means infinite) (default: 8)')
    p.add_argument('-e', '--exclude', metavar='modid', default=[], action='append', help='Add a mod ID to not be imported (can be used multiple times)')
    p.add_argument('--release', default='auto', choices=('auto', 'auto_ask', 'latest', 'ask'), help='Which release of the mod to install. "auto" (the default) and "auto_ask" check if it\'s specified in the file, or gets the latest if it isn\'t for "auto" and asks for "auto_ask", "ask" and "latest" are self-explanatory')
    p.add_argument('--api-url', metavar='url', default='https://mods.vintagestory.at/api/mod/{}', help='The URL for querying mod information from, replacing "{}" with the mod\'s ID (default: "https://mods.vintagestory.at/api/mod/{}")')
    p.add_argument('--file-url', metavar='url', default='https://mods.vintagestory.at/{}', help='The base URL for downloading files, replacing "{}" with the mod API\'s "mainfile" value (default: "https://mods.vintagestory.at/{}")')
    p.add_argument('import_file', default=sys.stdin, nargs='?', metavar='source', type=argparse.FileType(), help='The .vsmmgr file to import mods from (reads from StdIn if not specified)')
    p.add_argument('destination', default='.', nargs='?', help='Where the mods are (defaults to ".", AKA current directory')
def import_command(ns: argparse.Namespace):
    installs = {}
    for m,rs in Mod.multiget_upstream_releases(
            (m for m in Mod.import_list(json.load(ns.import_file)) if m.id not in ns.exclude),
            nthreads=ns.threads, url=ns.api_url,
            callback_start=lambda m: eprint(f'Fetching mod info for {m.id}'), callback_done=lambda m: eprint(f'Got mod info for {m.id}')):
        eprint(m)
        if ns.release in {'auto', 'auto_ask'}:
            if m.version is None: eprint('Mod has no version, cannot auto')
            else:
                for r in rs:
                    if m.version == Version(r['modversion']):
                        eprint(f'Release {r["releaseid"]} matches version {m.version}')
                        installs[m] = r
                        break
                if m in installs: continue
        if ns.release in {'auto', 'latest'}:
            installs[m] = rs[0]
            eprint(f'Selected release {installs[m]["releaseid"]} on latest version {installs[m]["modversion"]}')
        for i,r in reversed(tuple(enumerate(rs))):
            eprint(f' [{i}] {r["modversion"]} (VS version(s) {" ".join(r["tags"])})')
        eprint(f'Enter version to install (0-{len(rs)-1}), or "q" to ignore (0 is default) >', end='')
        v = input()
        if v.startswith('q'): continue
        try:
            v = int(v)
            if not (0 <= v < len(cs)): raise ValueError
        except ValueError:
            eprint('Illegal or no value entered, selecting 0 (most recent)')
            v = 0
        installs[m] = rs[0]
    if ns.interactive:
        for m,r in installs.items():
            eprint(f'Install {ns.file_url.format(r["mainfile"])} to {os.path.join(ns.path, r["filename"])}? (y/N) >', end='')
            if input().lower() != 'y': del installs[m]
    if not len(installs):
        eprint('Nothing to do - no mods were selected'); return
    eprint(f'{len(installs)} mods to install')
    Mod.multidownload(tuple(r['mainfile'] for r in installs.values()), ns.file_url, os.path.join(ns.destination, '{}'), nthreads=ns.threads, callback_done=lambda f,d: eprint(f'Downloaded {f} to {d}'))

# Export
def add_export_arguments(p: argparse.ArgumentParser):
    p.add_argument('-o', '--output', default=sys.stdout, metavar='path', help='Where to write the .vsmmgr file to (writes to StdOut if not given)')
    p.add_argument('-e', '--exclude', metavar='modid', default=[], action='append', help='Add a mod ID to not be exported (can be used multiple times)')
    p.add_argument('--overwrite', action='store_true', help='Overwrite the output file if it already exists')
    p.add_argument('--strip-version', action='store_true', help='Don\'t include version numbers')
    p.add_argument('--error-behavior', metavar='mode', choices=('ask', 'ignore', 'fail'), default='ask', help='How to behave when an error is encountered (default: "ask")')
    p.add_argument('--minimize', action='store_true', help='Make the output as small (smaller when combined with --strip-version) as possible (AKA not pretty-printing) and single-lined')
    p.add_argument('path', default='.', nargs='?', help='Where the mods are (defaults to ".", AKA current directory')

def export_command(ns: argparse.Namespace):
    out = ns.output
    if isinstance(out, str):
        if os.path.isdir(out):
            print(out)
            out = os.path.join(out, f'{os.path.basename(os.path.abspath(ns.path))}.vsmmgr')
        if (not ns.overwrite) and os.path.exists(out):
            eprint(f'Destination "{out}" already exists, use --overwrite to overwrite')
            exit(1)
        out = open(out, 'w')
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
    json.dump(tuple(Mod.export_list(mods, ns.minimize, ns.strip_version)), out,
        **({'indent': 4} if not ns.minimize else {
            'indent': None,
            'separators': (',', ':'),
        })
    )
