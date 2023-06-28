# Graphical User / Application Protocol Interface

#> Imports
import os, sys   # basic system libraries
import inspect   # introspection
import uuid      # generate unique identifiers
import functools # partials
import json      # Python <> JS bridge
import typing    # typehints
import packaging # version comparison
#</Imports

#> Hooks
def hook_factory(basehook: type):
    class Hook(basehook):
        def pre_window_created(self):
            return super().pre_window_created() | {
                'title': 'vintagestory-modmgr GUI',
                'confirm_close': True,
            }
        def post_window_created(self, w: 'webview.Window'):
            super().post_window_created(w)
            self.guapi.windows['main'] = w
        def pre_webview_start(self, wv: 'webview'):
            self.guapi.webview = wv
            return super().pre_webview_start(wv) | {
                'private_mode': False,
            }
    return Hook
#</Hooks

#> Eprint
eprint = lambda *a, **kw: print(*a, file=sys.stderr, **kw)
try: eprint(end='')
except: eprint = lambda *a, **kw: None
#</Eprint

#> Exceptions
class VariableNotFound(KeyError): pass
class WindowNotFound(KeyError): pass
class MagicNotFound(KeyError): pass
#</Exceptions

#> Bases
class GUAPI_Layout:
    __slots__ = (
        'webview', 'Mod',          # base
        'store',                   # Variables
        'windows',                 # Windows
        'magic', #'magic_claimed', # Magic
    )
class GUAPI_Base(GUAPI_Layout):
    __slots__ = ()
    def __init__(self, mod: 'Mod'):
        self.Mod = mod; self.webview = None
    # Introspection
    @classmethod
    def _get_exposed_methods(cls):
        return dict(inspect.getmembers(cls, predicate=
            lambda m: inspect.isroutine(m) and not m.__name__.startswith('_')))
    # Exposed base methods
    @classmethod
    def uuid(_): return str(uuid.uuid4())

class GUAPI_BaseVariables(GUAPI_Base):
    __slots__ = ()
    def _vars_Store(dict):
        def __getitem__(self, key):
            if key not in self: raise VariableNotFound(f'Variable {key} does not exist')
            return super().__getitem__(key)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs); self.store = self._vars_Store()

class GUAPI_BaseWindows(GUAPI_BaseVariables):
    __slots__ = ()
    class _win_Windows(dict):
        def __getitem__(self, key):
            if key not in self: raise WindowNotFound(f'Window {key} does not exist')
            return super().__getitem__(key)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs); self.windows = self._win_Windows()

class GUAPI_BaseMagic(GUAPI_BaseVariables):
    __slots__ = ()
    class _magic_Magic(dict):
        def __getitem__(self, key):
            if key not in self: raise MagicNotFound(f'Magic method {key} does not exist')
            return super().__getitem__(key)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.magic = self._magic_Magic() #; self.magic_claimed = set()
    def _magic_cleanup(self, obj: dict, id: str):
        def cleanup():
            for k,v in obj.items():
                if not isinstance(v, str) or not v.startswith(f'{id}.') or (v not in self.magic): continue
                del self.magic[v]; eprint(f'{id}.cleanup() on {k}: {v}')
        obj['cleanup()'] = f'{id}.cleanup'; self.magic[obj['cleanup()']] = cleanup
    def _magic_idpfx(self, pfx: str, obj: str | object): # absolutely prevent name collisions* (*maybe) in a small(ish) amount of space
        # magic_claimed code removed, testing shows that checking if item in dict.keys is barely slower than in set
        #if self.magic_claimed != (ks := set(self.magic.keys())):
        #    eprint('Discrepency between magic function keys and claimed magic function IDs, cleaning up')
        #    if d := self.magic_claimed.difference(ks):
        #        eprint(f'Stale claims detected:\n {d!r}')
        #        self.magic_claimed.difference_update(d)
        #    if i := self.magic_claimed.intersection(ks):
        #        eprint(f'Unclaimed registered IDs detected:\n {i!r}')
        #        self.magic_claimed.intersection_update(i)
        nprefix = obj if isinstance(obj, str) else f'{(obj if isinstance(obj, type) else obj.__class__).__module__}.{(obj if isinstance(obj, type) else obj.__class__).__name__}'
        suff = 0; idpfx = f'{pfx}:{nprefix}~%d'
        while True:
            for k in self.magic:
                if k.startswith(idpfx % suff): break
            else: break
            suff += 1
        idpfx %= suff #; self.magic_claimed.add(idpfx)
        eprint(f'Generated ID for {obj!r}: {idpfx}')
        return idpfx #, lambda: self.magic_claimed.remove(idpfx))
    def _magic_iter(self, it: iter):
        itero = {}; idpfx = self._magic_idpfx('_magic_iter', it)
        def _magic_iter_fn(itero, method, *a, **kw):
            try: return method(*a, **kw)
            except StopIteration as e:
                self.magic[itero['cleanup()']]()
                raise e
        for meth in ('__next__', 'send'):
            if not hasattr(it, meth): continue
            k = f'{meth}()'; itero[k] = f'{idpfx}.{meth}'
            self.magic[itero[k]] = functools.partial(_magic_iter_fn, itero, getattr(it, meth))
        for n,vs in {'len': ('__length_hint__', '__len__')}.items():
            for v in vs:
                if not hasattr(it, v): continue
                itero[n] = getattr(it, v)(); break
        self._magic_cleanup(itero, idpfx); return itero
    def _magic_all(self, obj: typing.Any, filtr = lambda o,k: ((not k.startswith('_')) and inspect.isroutine(getattr(o, k)))):
        objo = {}; idpfx = self._magic_idpfx('_magic_all', obj)
        for n in dir(obj):
            if not filtr(obj, n): continue
            k = f'{n}()'; objo[k] = f'{idpfx}.{n}'
            self.magic[objo[k]] = getattr(obj, n)
        self._magic_cleanup(objo, idpfx); return objo
#</Bases

#> Higher-Level Exposed Methods
class GUAPI_Variables(GUAPI_BaseVariables):
    __slots__ = ()
    def vars_store(self, id: str, val: typing.Any = None, behavior_if_exists: typing.Literal['fail', 'ignore', 'change'] = 'fail') -> bool:
        '''Creates a new variable and stores the given value (or None), returns success

            If the variable already exists, then we act based on the value of behavior_if_exists:
                'fail': raise an AttributeError
                'ignore': Does nothing, no value is changed
                'change': Change the value of the variable as if it didn't already exist
            any other value of behavior_if_exists results in:
                an AssertionError (assuming assert is enabled) immediately, or
                a ValueError when a value that already exists is encountered'''
        assert (behavior_if_exists in {'fail', 'ignore', 'change'}), f'Illegal value for behavior_if_exists: {behavior_if_exists}'
        if id in self.store:
            match behavior_if_exists:
                case 'fail': raise AttributeError('Variable {id} already exists')
                case 'ignore': return False
                case 'change': pass
                case _: raise ValueError(f'Illegal value for behavior_if_exists: {behavior_if_exists}')
        self.store[id] = val; eprint(f'Stored var {id} as {val!r}')
        return True
    def vars_recall(self, id: str, deflt = None) -> typing.Any:
        '''Gets a variable; returns deflt (or None) if it does not exist'''
        return self.store.get(id, deflt)
    def vars_remove(self, id: str, fail_if_not_exists = True) -> bool:
        '''Deletes a variable, raising VariableNotFound if it doesn't exist if fail_if_not_exists is truthy, and returns whether or not anything was deleted'''
        if (not fail_if_not_exists) and (id not in self.store): return False
        del self.store[id]; return True
    def vars_exists(self, id: str) -> bool:
        '''Returns whether or not a variable exists'''
        return id in self.store

class GUAPI_Windows(GUAPI_BaseMagic, GUAPI_BaseWindows, GUAPI_BaseVariables):
    __slots__ = ()
    # Creation and Destruction
    def win_create(self, title: str, kwargs: dict[str, typing.Any] = {}) -> str:
        '''Creates a new window, generating and returning a unique UUID for it'''
        id = self.uuid(); eprint(f'Creating window {id}')
        self.windows[id] = self.webview.create_window(title, js_api=self, **kwargs)
        self.windows[id].evaluate_js(f'globalThis.$wid = "{id}";')
        return id
    def win_close(self, id: str):
        '''Destroys a window of the given ID (proceeding regardless of whether or not it was already destroyed), then deletes it'''
        try: self.windows[id].destroy()
        except KeyError: pass # if the user manually destroyed it
        del self.windows[id]
    # Executing Javascript
    def win_execute(self, id: str, js: str, store: str | None, callback: str | None) -> typing.Any:
        '''Executes Javascript inside of the specified window, returning the result (WITHOUT resolving promises). Raises AttributeError if the window doesn't exist

            If store is not None, then the result (WITH resolving promises) is stored inside of the ID specified by store (overwriting existing values)
            If callback is not None, then the magic function with the ID specified in callback is called with the result (WITH resolving promises) as the first parameter'''
        cb_func = (lambda v: None) if (callback is None) else self.magic[callback]
        def cb(v):
            if store is not None: self.store[store] = v
            cb_func(v)
        return self.windows[id].evaluate_js(js, cb)
    def win_call(self, wid: str, mid: str, *args: tuple[typing.Any]):
        '''Calls a magic Javascript function inside of the specified window, overriding whichever target ID it was created with unless the specified window ID is None


            Raises MagicNotFound if the magic function does not exist
            Raises WindowNotFound if the window does not exist
            Raises ValueError if the magic function is not a JS function'''
        eprint(f'magic[{mid}] in {wid} on {args!r}')
        if not getattr(self.magic[mid], '_is_magic_js', False): raise ValueError(f'Magic function {mid} is not a magic JS function')
        return self.magic[mid](*args, _overridden_id=wid)
    # Getting information
    def win_cookies(self, wid: str) -> ...:
        '''Gets the cookies from a window'''
        return self.windows[wid].get_cookies()
    def win_elements(self, wid: str, selector: str) -> typing.Never | None:
        '''Gets the serialized DOM element by the selector'''
        return self.windows[wid].get_elements(selector)
    # Modifying the window
    def win_show(self, wid: str, show: bool = True):
        '''Toggles whether or not a window is visible, depending on the "show" parameter'''
        if show: self.windows[wid].show()
        else: self.windows[wid].hide()
    def win_size(self, wid: str, size: typing.Literal['minimized', 'restored', 'fullscreen'] | tuple[int, int]):
        '''Changes the size of a window

            Size can either be a tuple of ints, width and height, or one of "minimized", "restored", or "fullscreen" (any other value results in ValueError)
                minimized will minimize the window, restore will unminimize the window
                fullscreen will toggle the state of fullscreen -- if the window is fullscreen, it is un-fullscreened, and if it isn't fullscreen, it will become fullscreen'''
        match size:
            case 'minimized': self.windows[wid].minimize()
            case 'restored': self.windows[wid].restore()
            case 'fullscreen': self.windows[wid].toggle_fullscreen()
            case [w, h]: self.windows[wid].resize(w, h)
            case _: raise ValueError(f'Cannot get resize value from {size!r}')
    def win_load(self, wid: str, type: typing.Literal['css', 'html'], value: str):
        '''Load a type into the window, with type being "css" or "html" (any other value results in ValueError)'''
        match type:
            case 'css': self.windows[wid].load_css(value)
            case 'html': self.windows[wid].load_html(value)
            case _: raise ValueError(f'Unknown type {type}')
    def win_move(self, wid: str, x: int, y: int):
        '''Moves the window to the given x and y points'''
        self.windows[wid].move(x, y)
    def win_set_title(self, wid: str, title: str):
        '''Sets the title of a window'''
        self.windows[wid].set_title(title)
    # Getting and modifying
    def win_url(self, wid: str, url: str | None = None) -> str | None:
        '''Either gets (if url is None) or sets the window's URL'''
        if url is None: return self.windows[wid].get_current_url()
        self.windows[wid].load_url(url)
    # Events
    def win_register_eventhandler(self, wid: str, event: str, mid: str):
        '''Registers an event handler on the window to fire the magic function when the event is fired

            See: https://pywebview.flowrl.com/guide/api.html#events'''
        getattr(self.windows[wid], event).__iadd__(self.magic[mid])
    def win_remove_eventhandler(self, wid: str, event: str, mid: str):
        '''Removes a previously registered event handler'''
        getattr(self.windows[wid], event).__isub__(self.magic[mid])

class GUAPI_Magic(GUAPI_BaseMagic, GUAPI_BaseWindows, GUAPI_BaseVariables):
    __slots__ = ()
    def magic_call(self, id: str, *args: tuple[typing.Any]):
        '''Call a registered magic method, with the given arguments'''
        eprint(f'magic[{id}] on {args!r}'); return self.magic[id](*args)
    def magic_register_js(self, target_id: str, js: str, store: str | None = None, callback: str | None = None, argrepl: tuple[str] = (), strict_arguments = True) -> str:
        '''Register a magic Javascript method and return its given ID

            Registers a magic Javascript method that executes Javascript in a target window, to be invoked later via Javascript
            The function acts similarly to GUAPI_Windows.w_call, returning the result without resolving promises

            target_id is the window ID to execute the Javascript in (which can be overridden with the kwarg _overridden_id)
            store is, if not None, the variable ID to store the value after promises are resolved
            callback is, if not None, the magic function to execute with the return value (after promises are resolved) as the first argument
            argrepl is a list of strings. Each string, when found in the Javascript code to execute, is replaced by the JSON representation of the argument at that position
                Take the code `console.table(a); console.log(b); alert(b);` with the argrepl ('a', 'b') as an example, naming the method "magic_method_test":
                    magic_method_test({'a': 0, 'b': 1, 'c': 2}, "test") -> `console.table({"a": 0, "b": 1, "c": 2}); console.log("test"); alert("test");`
                strict_arguments:
                    If it is truthy, then IndexError will be raised if the length of the arguments is not equal to the length of argrepl.
                    If it is falsey, then extra arguments will be ignored and missing arguments will be None'''
        mid = self._magic_idpfx('js', str(hash(js)))
        def magicfn(*args, _overridden_id = None):
            wid = target_id if _overridden_id is None else _overridden_id
            if strict_arguments and (len(args) != len(argrepl)):
                raise IndexError(f'Strict arguments don\'t match, expected {len(argrepl)} argument(s), got {len(args)}')
            cb_func = (lambda v: None) if (callback is None) else self.magic[callback]; code = js
            for i,ar in enumerate(argrepl):
                code = code.replace(ar, json.dumps(None if (i > len(args)) else args[i]))
            if store is None: cb = cb_func
            else:
                def cb(v):
                    self.store[store] = v; cb_func(v)
            return self.windows[wid].evaluate_js(code, cb)
        magicfn._is_magic_js = True
        self.magic[mid] = magicfn; return mid
    def magic_unregister(self, id: str, fail_if_not_exists = True) -> bool:
        '''Deletes the magic function with the given ID, throwing MagicNotFound if the function doesn't exist and fail_if_not_exists is truthy. Returns whether or not anything was deleted'''
        #if id in self.magic_claimed: self.magic_claimed.remove(id)
        if (not fail_if_not_exists) and (id not in self.magic): return False
        del self.magic[id]; return True
    def magic_is_registered(self, id: str) -> bool:
        '''Returns whether or not the function is registered'''
        return id in self.magic
    def magic_is_js(self, id: str) -> bool:
        '''Returns whether or not the function is a magic Javascript function'''
        return getattr(self.magic[id], '_is_magic_js', False)
    def magic_ls(self) -> tuple[str]:
        '''Get a tuple of every magic function ID'''
        return tuple(self.magic.keys())

class GUAPI_Mods(GUAPI_BaseMagic):
    def mods_default_directory(self): return self.Mod.default_mod_directory()
    def mods_from_directory(self, path): return self._magic_iter(self.Mod.from_directory(path, hashable=True))
    def mods_get_metadatas(self, mods: tuple[dict], callback_start: str, callback_done: str, nthreads=8):
        self.magic[callback](m.id)
        return self.Mod.multiget_upstream_metadata((self.Mod(**modd) for modd in mods), nthreads=8,
            callback_start=lambda m: self.magic[callback_start](m.id),
            callback_done=lambda m: self.magic[callback_done](m.id))
    @classmethod
    def mods_compare_versions(_, v0: str, v1: str) -> int:
        v0, v1 = packaging.version.parse(v0), packaging.version.parse(v1)
        return 0 if v0 == v1 else 1 if v0 > v1 else -1
#</Higher-Level Exposed Methods

#> GU/API >/
class GUAPI(GUAPI_Mods, GUAPI_Magic, GUAPI_Windows, GUAPI_Variables, GUAPI_Base):
    __slots__ = ()
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    # Directory / file manipulation
    dialog_types = {'file': 'OPEN_DIALOG', 'save': 'SAVE_DIALOG', 'folder': 'FOLDER_DIALOG'}
    def open_dialog(self, wid: str, dtype: str, kwargs: dict[str, typing.Any] = {}):
        return self.windows[wid].create_file_dialog(getattr(self.webview, self.dialog_types[dtype]), **kwargs)
