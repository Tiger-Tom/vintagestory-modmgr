#> Imports
import glob, os                       # finding mods & path handling
import requests, urllib               # get info from ModDB and download mods
import re, hjson, zipfile             # read modinfo (JSON/zip and C#)
import functools, multiprocessing     # optimizations
import multiprocessing.pool
from packaging.version import Version # compare mod versions
import typing                         # better type hinting
#</Imports

#> Header >/
class Mod(dict): # dict makes it JSON serializable
    __slots__ = ('name', 'desc', 'id', 'version', 'raw_version', 'source')
    CS_MODINFO_OUTER_PATTERN = re.compile(r'\[assembly:\s*ModInfo\((.*?)\)\s*\]', re.DOTALL)
    CS_MODINFO_INNER_PATTERNS = {k: re.compile(v, re.IGNORECASE) for k,v in {
        'name': r'name:\s*"([^"]*)"',
        'desc': r'description\s*=\s*"([^"]*)"',
        'id': r'id:\s*"([^"]*)"',
        'version': r'version\s*=\s*"([^"]*)"',
    }.items()}
    VINTAGESTORY_MOD_PATH = os.path.join('VintagestoryData', 'Mods')
    VINTAGESTORY_DATA_ROOT_LINUX_FALLBACK = os.path.expanduser('~/.config/')
    VINTAGESTORY_DATA_ROOT_FALLBACK = '.'
    # Object Output Types
    def __repr__(self): return f'{self.id}@{self.version}'
    def __str__(self, noversion=False, nodesc=False):
        t = []
        return  \
            (self.id if (self.name is None) else f'{self.name} [{self.id}]') +  \
            (f' v{self.version}' if (self.version is not None) and (not noversion) else '') +  \
            ('' if (self.desc is None) or nodesc else f': {self.desc}')
        if self.name is not None: t.append(f'{self.name} [{self.id}]')
        return f'{self.name} [{self.id}] v{self.version}: {self.desc}'
    def __hash__(self): return hash((self.name, self.desc, self.id, self.version, self.source))
    # Initializers
    def __init__(self, *, name: str = None, desc: str = None, id: str = None, version: Version = None, source: str = None):
        if isinstance(version, str):
            self.raw_version = version
            self.version = Version(version)
        else:
            self.version = version
            self.raw_version = str(version)
        self.name, self.desc, self.id, self.source = name, desc, id, source # ugly code, sorry
        dict.__init__(self, name=name, desc=desc, id=id, version=self.raw_version, source=source)
    def __setattr__(self, i, v):
        if dict.__contains__(self, i): dict.__setitem__(self, i, v)
        object.__setattr__(self, i, v)
    #  From files
    @classmethod
    def from_file(cls, file: str):
        if not os.path.exists(file): raise FileNotFoundError('Cannot read from a mod that does not exist')
        if zipfile.is_zipfile(file):
            with zipfile.ZipFile(file) as zf, zf.open('modinfo.json') as f:
                self = cls.from_json(f.read())
        elif file.endswith('.cs'):
            with open(file) as cs:
                self = cls.from_cs_source(cs.read())
        elif file.endswith('.json'):
            with open(file) as j:
                self = cls.from_json(**hjson.load(f))
        else: raise ValueError(f'Cannot parse mod file {file}, it is not a zip file or .cs/.json file')
        self.source = file
        return self
    @classmethod
    def from_directory(cls, path: str, *, hashable=False):
        for p in glob.glob(os.path.join(path, '*.zip')) + glob.glob(os.path.join(path, '*.cs')):
            while True:
                try:
                    yield (cls.from_file(p),p)
                    break
                except Exception as e:
                    if hashable:
                        cont = yield ({
                            'exception': type(e).__name__,
                            'message': str(e),
                            'self': repr(e),
                        }, p)
                    else: cont = yield (e,p)
                    yield
                    if not cont: break
    #   Specific file types
    @classmethod
    @functools.cache
    def from_json(cls, data: str):
        d = requests.structures.CaseInsensitiveDict(hjson.loads(data))
        return cls(name=d.get('name', None), desc=d.get('description', None), id=d['modid'], version=d['version'])
    @classmethod
    @functools.cache
    def from_cs_source(cls, code: str, *, pattern_outer=CS_MODINFO_OUTER_PATTERN, patterns_inner=CS_MODINFO_INNER_PATTERNS):
        if m := pattern_outer.search(code):
            return cls(**{k: v.search(m.group(1)).group(1) for k,v in patterns_inner.items()})
        else: raise ValueError('Cannot parse code')
    # Helper/upstream functions
    @staticmethod
    @functools.cache
    def _get_upstream_metadata(url):
        return requests.get(url)
    def get_upstream_metadata(self, *, url='https://mods.vintagestory.at/api/mod/{}', callback_start=lambda m: None, callback_done=lambda m: None):
        callback_start(self)
        r = self._get_upstream_metadata(url.format(self.id))
        if r.status_code == 404: raise FileNotFoundError('Mod information couldn\'t be found, perhaps it is not in the DB?')
        elif r.status_code != 200: raise Exception(f'Mod information couldn\'t be fetched, status code {r.status_code}')
        callback_done(self)
        return r.json()
    def get_upstream_releases(self, *, url='https://mods.vintagestory.at/api/mod/{}', callback_start=lambda m: None, callback_done=lambda m: None):
        return sorted(self.get_upstream_metadata(url=url, callback_start=callback_start, callback_done=callback_done)['mod']['releases'], key=lambda r: r['releaseid'], reverse=True)
    @staticmethod
    def _multiget_(fn, mods, kwargs={}, nthreads=0):
        print(nthreads)
        m = tuple(mods); vals = []
        if nthreads < 1: nthreads = len(mods)
        with multiprocessing.pool.ThreadPool(min(nthreads, len(mods))) as p:
            return zip(m, p.map(functools.partial(fn, **kwargs), m))
        return vals
    @classmethod
    def multiget_upstream_metadata(cls, mods: tuple[typing.Self], *, nthreads=0, callback_alldone=lambda ms: None, **kwargs):
        metas = cls._multiget_(cls.get_upstream_metadata, mods, kwargs, nthreads)
        callback_alldone(metas); return metas
    @classmethod
    def multiget_upstream_releases(cls, mods: tuple[typing.Self], *, nthreads=0, callback_alldone=lambda rs: None, **kwargs):
        rels = cls._multiget_(cls.get_upstream_releases, mods, kwargs, nthreads)
        callback_alldone(rels); return rels
    # Downloading
    @staticmethod
    @functools.cache
    def _download(url):
        with urllib.request.urlopen(url) as r:
            return r.read()
    @classmethod
    def download(cls, url_base, filename, destination, *, callback_start=lambda f, d: None, callback_done=lambda f, d: None):
        callback_start(filename, destination)
        with open(destination, 'wb') as f:
            f.write(cls._download(url_base.format(urllib.parse.quote(filename))))
        callback_done(filename, destination)
    @classmethod
    def multidownload(cls, filenames, url_base, destination_base, *, nthreads=0, callback_alldone=lambda: None, callback_start=lambda f: None, callback_done=lambda f: None):
        fs = tuple(filenames)
        if nthreads < 1: nthreads = len(fs)
        with multiprocessing.pool.ThreadPool(min(nthreads, len(fs))) as p:
            p.starmap(functools.partial(cls.download, url_base, callback_start=callback_start, callback_done=callback_done), zip(fs, (destination_base.format(os.path.basename(f)) for f in fs)))
        callback_alldone()
    # Import/Export-ing
    @staticmethod
    def export_list(mods: tuple[typing.Self], minimize: bool, strip_version: bool):
        return ({
            'i' if minimize else 'id': m.id,
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
            id=m.get('id', m.get('i')),
            version=m.get('version', m.get('v')),
        ) for m in mods)
    # Path helpers
    @classmethod
    @functools.cache
    def default_mod_directory(cls):
        if os.name == 'nt':
            if os.path.exists(d := os.path.join(os.getenv('APPDATA'), cls.VINTAGESTORY_MOD_PATH)):
                return d
            return cls.VINTAGESTORY_DATA_ROOT_FALLBACK
        if os.getenv('XDG_CONFIG_HOME'):
            if os.path.exists(d := os.path.join(os.getenv('XDG_CONFIG_HOME'), cls.VINTAGESTORY_MOD_PATH)):
                return d
        if os.path.exists(d := os.path.join(cls.VINTAGESTORY_DATA_ROOT_LINUX_FALLBACK, cls.VINTAGESTORY_MOD_PATH)):
            return d
        return cls.VINTAGESTORY_DATA_ROOT_FALLBACK
