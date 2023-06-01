#> Imports
try:
    import tkinter as tk  # base graphics UI
    from tkinter import filedialog as tkfd
    from tkinter import messagebox as tkmb
except: tk = False
import argparse           # type hinting
import os, sys            # basic system libraries
import functools          # callback partials
import threading          # concurrency and locking resources
import concurrent.futures # more concurrency
import traceback          # error messages
import json, packaging    # handling mod metadata


sys.path.append('../') ############################


from basemod import Mod
#</Imports

#> Header >/
eprint = lambda *a,**k: print(*a, **k, file=sys.stderr)
class GUI:
    @staticmethod
    def add_arguments(p: argparse.ArgumentParser):
        ...
    @classmethod
    def command(cls, ns: argparse.Namespace, *, chr_manage=9881, chr_import=11147, chr_export=9099, chr_update=11145, chr_quit=8619):
        if tk is False:
            eprint('Cannot use GUI, Tkinter was not imported'); exit(1)
        if os.name == 'nt' and os.getenv('APPDATA') and os.path.exists(d := os.path.join(os.getenv('APPDATA'), 'VintagestoryData', 'Mods')): idir = d
        elif os.getenv('XDG_CONFIG_HOME') and os.path.exists(d := os.path.join(os.getenv('XDG_CONFIG_HOME'), 'VintagestoryData', 'Mods')): idir = d
        elif os.path.exists(d := os.path.expanduser('~/.config/VintagestoryData/Mods')): idir = d
        else: idir = None
        mod_dir = tkfd.askdirectory(title='Mod directory', initialdir=idir)
        if mod_dir is None:
            eprint('Cancelled by user'); return
        if not os.path.exists(mod_dir):
            eprint(f'{mod_dir} does not exist')
            tkmb.showerror(f'{mod_dir} does not exist!'); return
        eprint(f'{mod_dir}')
        r = tk.Tk(); r.title('vintagestory-modmgr')
        eprint('Making buttons')
        tk.Button(text=f'{chr(chr_update)} Update', command=functools.partial(cls.mode_update, mod_dir)).grid(row=0, column=1)
        tk.Button(text=f'{chr(chr_export)} Export', command=functools.partial(cls.mode_export, mod_dir)).grid(row=1, column=0)
        tk.Button(text=f'{chr(chr_manage)} Manage', command=functools.partial(cls.mode_manage, mod_dir)).grid(row=1, column=1)
        tk.Button(text=f'{chr(chr_import)} Import', command=functools.partial(cls.mode_import, mod_dir)).grid(row=1, column=2)
        tk.Button(text=f'{chr(chr_quit)} Exit', command=r.quit).grid(row=2, column=1)
        eprint('r.mainloop'); r.mainloop(); r.destroy(); eprint('quit')
    # Modes
    @classmethod
    def mode_manage(cls, path):
        eprint('mode_manage')
        mods = []
        for m in cls.mods_from_directory(path):
            if m is False: return

                
    @classmethod
    def mode_update(cls, path):
        eprint('mode_update')
        for m in cls.mods_from_directory(path):
            if m is False: return
    @classmethod
    def mode_import(cls, path, *, geometry='720x960', api_url='https://mods.vintagestory.at/api/mod/{}', file_url='https://mods.vintagestory.at/{}', from_list=' [from list]', latest='[latest]', noinstall='[do not install]'):
        eprint('mode_import')
        ifile = tkfd.askopenfile(title='Select file to import from', filetypes=(('Vintage Story Mod Manager files', '*.vsmmgr'), ('JSON files', '*.json'), ('All files', '*')))
        if ifile is None:
            eprint('Cancelled by user'); return
        try:
            mods = tuple(Mod.import_list(json.load(ifile)))
        except Exception as e:
            eprint(traceback.print_tb)
            tkmb.showerror(message=f'Caught critical exception {repr(e)}'); return
        cls.multidownload(file_url, os.path.join(path, '{}'),
            (v['mainfile'] for v in
                cls.mods_version_select(mods, {
                    latest: 0,
                    noinstall: None
                } | {
                    m: m.raw_version for m in mods if (m.raw_version is not None)
                }, geometry=geometry, api_url=api_url, file_url=file_url)
        ))
        tkmb.showinfo(message='Import complete')
    @classmethod
    def mode_export(cls, path):
        eprint('mode_export')
        for m in cls.mods_from_directory(path):
            if m is False: return
    # High helpers
    @classmethod
    def mods_version_select(cls, mods: tuple[Mod], add_options: dict[str,  int | None | dict[Mod, int | None | str | packaging.version.Version]] = {}, *, geometry='720x960', api_url='https://mods.vintagestory.at/api/mod/{}', file_url='https://mods.vintagestory.at/{}'):
        print(add_options)
        # Whether or not to show any version choices that aren't in add_options
        if add_options:
            addit = tkmb.askquestion(message='Show all version choices?')
            if addit is None:
                eprint('Cancelled by user'); return
        else: addit = True
        eprint(('S' if addit else 'Not s')+'howing additional version choices')
        # Get mod upstream releases
        r = tk.Tk(); mf = tk.Frame(r); mf.pack()
        mods = {m: ({v['modversion']: v for v in vs},tk.StringVar(r)) for m,vs in cls.multiget_upstream_releases(mods, root=mf, url=api_url)}
        mf.destroy()
        # Set up scroll bar
        fr,finalize_scrollable = cls.scrollable(r)
        # Set up mod array
        for i,(m,(vers,var)) in enumerate(mods.items()):
            eprint(f'Setup {m} at {i} -> {var}')
            tk.Label(fr, text=m.__str__(noversion=True, nodesc=True)).grid(row=i, column=0)
            options = [k for k,v in add_options.items() if not (isinstance(v, dict) and (m not in v))]
            if addit: options.extend(vers.keys())
            tk.OptionMenu(fr, var, *options).grid(row=i, column=1)
        # Set up buttons
        do_exit = tk.BooleanVar(r, False)
        def cancel():
            do_exit.set(True); r.quit()
        def set_latest():
            for _,var in mods.values(): var.set(latest)
        def set_none():
            for _,var in mods.values(): var.set(noinstall)
        tk.Button(fr, text='Set all to latest', command=set_latest).grid(row=len(mods), column=0); tk.Button(fr, text='Set all to not install', command=set_none).grid(row=len(mods), column=1)
        tk.Button(fr, text='Cancel', command=cancel).grid(row=len(mods)+1, column=0); tk.Button(fr, text='Download', command=r.quit).grid(row=len(mods)+1, column=1)
        # Finalize and run window
        r.geometry(geometry); finalize_scrollable()
        r.mainloop(); r.destroy()
        if do_exit.get():
            eprint('Cancelled by user'); return
        # Get version from values
        ret = {}
        for m,(vers,var) in mods.items():
            val = add_options.get(var.get(), default=var.get())
            if isinstance(val, dict): val = val[m]
            eprint(f'Got value {val} for {m.__str__(noversion=True, nodesc=True)}')
            if isinstance(val, int):
                eprint(f'Selected index {val}')
                ret[m] = vers[val]; continue
            elif val is None:
                eprint('None value selected'); continue
            ver = packaging.version.parse(val)
            for vn,r in vers.items():
                if packaging.version.parse(vn) == ver:
                    ret[m] = r; eprint(f'{vn} for {m.__str__(noversion=True, nodesc=True)}'); break
            else: tkmb.showerror(message=f'Could not find a version matching {ver} for {m.__str__(noversion=True, nodesc=True)}')
        return ret
    @classmethod
    def mods_from_directory(cls, path):
        miter = Mod.from_directory(path)
        for m,p in miter:
            if isinstance(m, Mod): yield m
            else:
                eprint(p, m)
                e = tkmb.askyesnocancel(message=f'Recieved an error while trying to read {p}:\n{m}\nRetry?')
                if e is None:
                    eprint('Cancelled by user'); yield False
                miter.send(e)
    @classmethod
    def multiget_upstream_releases(cls, mods: tuple[Mod], nthreads=12, url='https://mods.vintagestory.at/api/mod/{}', root=None):
        return cls.multi_progress_list('Fetching mod metadatas', tuple((
                {'value': m,
                 'display': m.__str__(noversion=True),
                } for m in mods)
            ), Mod.multiget_upstream_releases, fkwargs={'url': url}, nthreads=nthreads, r=root)
    @classmethod
    def multidownload(cls, url_base, destination_base, filenames, nthreads=12, root=None):
        cls.multi_progress_list('Downloading files', tuple((
                {'value': fn,
                 'display': os.path.basename(fn),
                } for fn in filenames)
            ), Mod.multidownload, fargs=(url_base, destination_base), nthreads=nthreads, r=root)
    # Base helpers
    @staticmethod
    def scrollable(r: tk.Tk):
        sb = tk.Scrollbar(r, orient=tk.VERTICAL); sb.pack(fill=tk.Y, side=tk.RIGHT, expand=tk.FALSE)
        c = tk.Canvas(r, yscrollcommand=sb.set); c.pack(fill=tk.BOTH, expand=tk.TRUE); sb.config(command=c.yview)
        fr = tk.Frame(r); c.create_window(0, 0, window=fr, anchor=tk.NW)
        def finalize():
            c.update_idletasks(); c.config(scrollregion=fr.bbox())
        return fr, finalize
    @staticmethod
    def multi_progress_list(title, items: tuple[dict], func, *, r=None, fargs=(), fkwargs={}, nthreads=8, chr_wait=9209, chr_work=9205, chr_done=10003, **kwargs):
        is_new = False
        if r is None:
            r = tk.Tk(**kwargs); r.title(title); is_new = True
        lwidth = len(max(items, key=lambda i: len(i['display']))['display'])
        lb = tk.Listbox(r, width=0, height=0, font='TkFixedFont'); lb.pack()
        for i,v in enumerate(items): lb.insert(i, f'{v["display"].ljust(lwidth)} {chr(chr_wait)}')
        cb_store = {v['value']: i for i,v in enumerate(items)}; cb_lock = threading.Lock()
        def cb_set(i, t, **c):
            cb_lock.acquire()
            lb.insert(i, t); lb.delete(i+1)
            lb.itemconfig(i, c)
            cb_lock.release()
        def cb_start(v): cb_set(cb_store[v], lb.get(cb_store[v])[:-1]+chr(chr_work), bg='yellow')
        def cb_done(v): cb_set(cb_store[v], lb.get(cb_store[v])[:-1]+chr(chr_done), bg='green')
        def cb_alldone(v=None):
            cb_store['_ret'] = v; r.quit()
        t = threading.Thread(target=func, args=(tuple(i['value'] for i in items),)+fargs,
            kwargs=({'nthreads': nthreads, 'callback_alldone': cb_alldone, 'callback_start': cb_start, 'callback_done': cb_done} | fkwargs))
        t.start(); r.mainloop(); t.join()
        if is_new: r.destroy()
        return cb_store['_ret']
