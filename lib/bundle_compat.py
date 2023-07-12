#!/bin/python

#> Imports
import os, sys                    # PathLike; if frozen + stderr
import pathlib                    # fancy path manipulation
from types import SimpleNamespace # SimpleNamespace
import functools                  # optimizations
#</Imports

#> Header
eprint = lambda *a, **kw: print(*a, **kw, file=sys.stderr)

is_frozen = getattr(sys, 'frozen', False)
is_zipapp = __loader__.__module__ == 'zipimport'
is_bundle = is_frozen or is_zipapp
if is_frozen and is_zipapp:
    raise NotImplemented('Cannot handle an application that is both frozen and zipapped')
bundle = SimpleNamespace(
    is_frozen = is_frozen,
    is_zipapp = is_zipapp,
    is_bundle = is_bundle,
    zipapp_attrs = SimpleNamespace(
        archive_path = getattr(__loader__, 'archive', None),
        temp_directory = None,
        populated_tops = set(),
    ) if is_zipapp else None,
    frozen_attrs = SimpleNamespace(
        data_dir = getattr(sys, '_MEIPASS', None),
    ) if is_frozen else None,
)

class _BundleableMeta(type):
    def __instancecheck__(cls, inst):
        print(cls, inst)
        for typ in {_PathlibPathBase, pathlib.Path, BundleablePath}:
            if type.__instancecheck__(typ, inst): return True
        return False

class _PathlibPathBase(os.PathLike):
    __slots__ = ('_pathlib_path', '__str__')
    def __init__(self, *a, **kw):
        self._pathlib_path = pathlib.Path(*a, **kw)
        self.__str__ = self._pathlib_path.__str__
    def __truediv__(self, subpath):
        return self.__class__(self._pathlib_path.__truediv__(subpath))
    def __hook(self, hook, *args, **kwargs):
        try: hooko = object.__getattribute__(self, hook)
        except AttributeError: return False
        if callable(hooko):
            print(f'{self!r} hook called: {hook}')
            return hooko
        else: return False
    def __getattr__(self, attr):
        if (h := self.__hook('_getattr_hook')): return h(attr)
        return self._pathlib_path.__getattribute__(attr)
    def __repr__(self): return f'{type(self).__name__}({self._pathlib_path!r})'
    def __fspath__(self):
        if (h := self.__hook('_fspath_hook')): return h()
        return str(self._pathlib_path)
class _ZipAppTempPath(_PathlibPathBase):
    __slots__ = ('_getattr_hook', '_fspath_hook', '__top')
    def __init__(self, top, *path, _subpath=False, **kw):
        if not is_zipapp: raise SyntaxError('not a chance')
        self._getattr_hook = self.__getattr_hook; self._fspath_hook = self.__fspath_hook
        self.__top = top
        if _subpath: return super().__init__(*path, **kw)
        self.__create_temporary_dir()
        super().__init__(bundle.zipapp_attrs.temp_directory.name, top, *path, **kw)
    def __truediv__(self, subpath):
        return self.__class__(self.__top, self._pathlib_path / subpath, _subpath=True)
    def __getattr_hook(self, attr):
        val = getattr(self._pathlib_path, attr)
        self._getattr_hook = None; self._fspath_hook = None
        eprint(f'{self!r}._populate_directory triggered by getting attr {attr}: {self._populate_directory()}')
        return val
    def __fspath_hook(self):
        self._getattr_hook = None; self._fspath_hook = None
        eprint(f'{self!r}._populate_directory triggered by getting __fspath__: {self._populate_directory()}')
        return self._pathlib_path.__fspath__()
    def _populate_directory(self):
        if self.__top in bundle.zipapp_attrs.populated_tops: return False
        bundle.zipapp_attrs.populated_tops.add(self.__top)
        from zipfile import ZipFile
        with ZipFile(bundle.zipapp_attrs.archive_path) as zf:
            zf.extractall(bundle.zipapp_attrs.temp_directory.name, (f for f in zf.namelist() if f.startswith(f'{self.__top}/')))
        return True
    @classmethod
    @functools.cache
    def __create_temporary_dir(cls):
        if bundle.zipapp_attrs.temp_directory is None:
            import atexit, tempfile
            bundle.zipapp_attrs.temp_directory= tempfile.TemporaryDirectory(prefix='vintagestory-modmgr.')
            atexit.register(bundle.zipapp_attrs.temp_directory.cleanup)
        return bundle.zipapp_attrs.temp_directory
    @functools.cache
    def exists(self):
        from zipfile import Path
        pathbase = str(pathlib.Path(*self._pathlib_path.parts[len(pathlib.Path(bundle.zipapp_attrs.temp_directory.name).parts):]))
        return Path(bundle.zipapp_attrs.archive_path, pathbase).exists() or Path(bundle.zipapp_attrs.archive_path, f'{pathbase}/').exists()
class _FrozenAppPath(_PathlibPathBase):
    __slots__ = ()
    def __init__(self, base, *a, **kw):
        if not is_frozen: raise SyntaxError('not a chance')
        super().__init__(bundle.frozen_attrs.data_dir, base, *a, **kw)

class BundleablePath(metaclass=_BundleableMeta):
    def __new__(cls, top, *path, **kw):
        return cls.real()(top, *path, **kw)
    @staticmethod
    def real():
        if is_zipapp: return _ZipAppTempPath
        if is_frozen: return _FrozenAppPath
        return pathlib.Path
#</Header

#> Main >/
__all__ = ('bundle', 'BundleablePath', 'is_frozen', 'is_zipapp')
