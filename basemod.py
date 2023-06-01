#> Imports
import glob, os                       # finding mods & path handling
import requests, urllib               # get info from ModDB and download mods
import re, hjson, zipfile             # read modinfo (JSON/zip and C#)
import functools, multiprocessing     # optimizations
import multiprocessing.pool
from packaging.version import Version # compare mod versions
import typing                         # better type hinting
#</Imports

#> Header
class Mod:
    __slots__ = ('name', 'desc', 'modid', 'version', 'raw_version', 'source')
    cs_modinfo_outer_pattern = re.compile(r'\[assembly:\s*ModInfo\((.*?)\)\s*\]', re.DOTALL)
    cs_modinfo_inner_patterns = {k: re.compile(v, re.IGNORECASE) for k,v in {
        'name': r'name:\s*"([^"]*)"',
        'desc': r'description\s*=\s*"([^"]*)"',
        'modid': r'modid:\s*"([^"]*)"',
        'version': r'version\s*=\s*"([^"]*)"',
    }.items()}
    def __repr__(self): return f'{self.modid}@{self.version}'
    def __str__(self, noversion=False, nodesc=False):
        t = []
        return  \
            (self.modid if (self.name is None) else f'{self.name} [{self.modid}]') +  \
            (f' v{self.version}' if (self.version is not None) and (not noversion) else '') +  \
            ('' if (self.desc is None) or nodesc else f': {self.desc}')
        if self.name is not None: t.append(f'{self.name} [{self.modid}]')
        return f'{self.name} [{self.modid}] v{self.version}: {self.desc}'
    # Initializers
    def __init__(self, *, name: str = None, desc: str = None, modid: str = None, version: Version = None, source: str = None):
        if isinstance(version, str):
            self.raw_version = version
            self.version = Version(version)
        else: self.version = version
        self.name, self.desc, self.modid, self.source = name, desc, modid, source # ugly code, sorry
    #  From files
    @classmethod
    def from_file(cls, file: str):
        if not os.path.exists(file): raise FileNotFoundError('Cannot read from a mod that does not exist')
        if zipfile.is_zipfile(file):
            with zipfile.ZipFile(file) as zf:
                self = cls.from_json(hjson.load(zf.open('modinfo.json')))
        elif file.endswith('.cs'):
            with open(file) as cs:
                self = cls.from_cs_source(cs.read())
        elif file.endswith('.json'):
            with open(file) as j:
                self = cls.from_json(hjson.load(f))
        else: raise ValueError(f'Cannot parse mod file {file}, it is not a zip file or .cs/.json file')
        self.source = file
        return self
    @classmethod
    def from_directory(cls, path: str):
        for p in glob.glob(os.path.join(path, '*.zip')) + glob.glob(os.path.join(path, '*.cs')):
            while True:
                try:
                    yield (cls.from_file(p),p)
                    break
                except Exception as e:
                    cont = yield (e,p)
                    yield
                    if not cont: break
    #   Specific file types
    @classmethod
    def from_json(cls, data: dict):
        d = requests.structures.CaseInsensitiveDict(data)
        return cls(name=d.get('name', None), desc=d.get('description', None), modid=d['modid'], version=d['version'])
    @classmethod
    def from_cs_source(cls, code: str, *, pattern_outer=cs_modinfo_outer_pattern, patterns_inner=cs_modinfo_inner_patterns):
        if m := pattern_outer.search(code):
            return cls(**{k: v.search(m.group(1)).group(1) for k,v in patterns_inner.items()})
        else: raise ValueError('Cannot parse code')
    # Helper/upstream functions
    def get_upstream_releases(self, *, url='https://mods.vintagestory.at/api/mod/{}', callback_start=lambda m: None, callback_done=lambda m: None):
        callback_start(self)
        r = requests.get(url.format(self.modid))
        if r.status_code == 404: raise FileNotFoundError('Mod information couldn\'t be found, perhaps it is not in the DB?')
        elif r.status_code != 200: raise Exception(f'Mod information couldn\'t be fetched, status code {r.status_code}')
        callback_done(self)
        return sorted(r.json()['mod']['releases'], key=lambda r: r['releaseid'], reverse=True)
    @classmethod
    def multiget_upstream_releases(cls, mods: tuple[typing.Self], *, nthreads=0, url='https://mods.vintagestory.at/api/mod/{}', callback_alldone=lambda: None, callback_start=lambda m: None, callback_done=lambda m: None):
        m = list(mods)
        rels = []
        if nthreads < 1: nthreads = len(m)
        with multiprocessing.pool.ThreadPool(nthreads) as p:
            while m:
                mp = [m.pop() for _ in range(max(nthreads, len(m)))]
                rels.extend(zip(mp, p.map(functools.partial(cls.get_upstream_releases, url=url, callback_start=callback_start, callback_done=callback_done), mp)))
        callback_alldone(rels)
        return rels
    # Downloading
    @staticmethod
    def download(url_base, filename, destination, *, callback_start=lambda f: None, callback_done=lambda f: None):
        callback_start(filename)
        urllib.request.urlretrieve(url_base.format(urllib.parse.quote(filename)), destination)
        callback_done(filename)
    @classmethod
    def multidownload(cls, filenames, url_base, destination_base, *, nthreads=0, callback_alldone=lambda: None, callback_start=lambda f: None, callback_done=lambda f: None):
        fs = list(filenames)
        if nthreads < 1: nthreads = len(fs)
        with multiprocessing.pool.ThreadPool(nthreads) as p:
            while fs:
                fp = [fs.pop() for _ in range(max(nthreads, len(fs)))]
                ds = [destination_base.format(os.path.basename(f)) for f in fp]
                p.starmap(functools.partial(cls.download, url_base, callback_start=callback_start, callback_done=callback_done), zip(fp, ds))
        callback_alldone()
    # Import/Export-ing
    @staticmethod
    def export_list(mods: tuple[typing.Self], minimize: bool, strip_version: bool):
        return ({
            'i' if minimize else 'id': m.modid,
            'v' if minimize else 'version': None if strip_version else m.raw_version,
        } | ({} if minimize else {
            'name': m.name,
            'desc': m.desc,
        }) for m in mods)
    @classmethod
    def import_list(cls, mods: tuple[dict]):
        return (cls(
            name=m.get('name', None),
            desc=m.get('desc', None),
            modid=m.get('id', m.get('i')),
            version=m.get('version', m.get('v')),
        ) for m in mods)
#</Header

#> Main >/
