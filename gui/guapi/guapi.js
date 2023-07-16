globalThis.$guapi = {};
globalThis.$g = $guapi; // shortcut
$guapi.ready = new Promise((resolve) => $guapi._resolve = resolve);
$guapi.and_dom_ready = Promise.all([$guapi.ready, 
    new Promise(resolve =>
        document.readyState !== "loading" ? resolve() 
        : document.addEventListener("DOMContentLoaded", resolve)
    )
]);
await import("./api_bind.js").catch(e => $error(
    "import",
    $error.code_from_error(e),
    `An error occured whilst binding api through api_bind.js:\n ${e.message}`,
));

Object.assign(globalThis.$guapi, {
    /* submodules */
    Var: null,    V: null,
    Window: null, W: null,
    Magic: null,  M: null,
    mods: null,   m: null,
    Lock: null,   L: null,
    /* submodule initialization */
    _callable_class: function(cls) {
        let ccls = function(...args) { return new cls(...args); };
        Object.setPrototypeOf(ccls, cls);
        return ccls;
    },
    _add: function(longname, shortname, module) {
        let _catch = promise => e => $error(
            "load_guapi_module",
            `${shortname}${promise ? ">promise" : ""}:${$error._formaterrev(e)}`,
            `An error occured while ${promise ? "resolving promises for" : "loading"} the GU/API module "${longname}":\n ${e.message}`,
        );
        this._promises.push(
            new Promise((resolve) => 
                module.then(m => {
                    let df = m.default;
                    this[longname] = this[shortname] = (df instanceof Function)
                        ? $guapi._callable_class(df)
                        : df;
                    if ("promises" in m)
                        Promise.all(m.promises).then(resolve).catch(_catch(true));
                    else resolve();
                }).catch(_catch(false))
            ).catch(_catch(false))
        );
    },
    _promises: [],
    /* top-level */
    /** values **/
    debug: undefined,
    flag: (key) => $guapi.flags.has(key), f: undefined,
    flags: undefined,
    /** functions **/
    uuid: async () => await $bridge.uuid(),
    open_dialog: async function(window_id=$wid, dtype /*one of "file", "save", or "folder"*/ = "file", kwargs={}) {
        return await $bridge.open_dialog(window_id, dtype, kwargs);
    },
});

// non-standard functions
$guapi._check_sync_bridge = async function() {
    function check(base, method, name) {
        if (method in base) console.debug(`${method} (${name}) is synchronized with GU/API}`);
        else
            try { check(new base(), method, name); }
            catch(_) { console.error(`${method} (${name}) is not synchronized with GU/API`); }
    }
    for (let m in $bridge) {
        if (m.startsWith("$")) continue;
        let base = $guapi;
        let method = m.slice(m.indexOf("_")+1);
        switch (m.split("_", 1)[0]) {
            case "vars": base = $guapi.Var;break;
            case "win": base = $guapi.Window;break;
            case "magic": base = $guapi.Magic;break;
            case "mods": base = $guapi.mods;break;
            case "lock": base = $guapi.Lock;break;
            default: method = m;
        }
        check(base, method, m);
    }
};

// add submodules
$guapi._add("Var",    "V", import("./submodules/vars.js"));
$guapi._add("Window", "W", import("./submodules/windows.js"));
$guapi._add("Magic",  "M", import("./submodules/magic.js"));
$guapi._add("mods",   "m", import("./submodules/mods.js"));
$guapi._add("Lock",   "L", import("./submodules/lock.js"));

// final promise
Promise.all($guapi._promises).then(async function() {
    await $bridge.$ready.catch(e => $error(
        "pywebview",
        $error.code_from_error(e),
        `An error occured whilst attempting to bridge pywebview API:\n ${e.message}`,
    ));
    $g.flags = new Set(await $bridge.get_flags()); $g.f = $g.flag;
    $g.debug = !$g.f("ignoreguidebug") && await $bridge.is_debug();
    if (!$g.f("nodebug") && ($g.f("debug") || $g.debug)) {
        let ifr = document.createElement("iframe"); ifr.src = "/guapi/debug.html";
        document.body.appendChild(ifr); document.body.insertBefore(ifr, document.body.firstChild);
        ifr.addEventListener("load", function() {
            ifr.style.height = ifr.contentDocument.documentElement.scrollHeight+"px";
        }); ifr.style.width = "100%";
    }
    $guapi._resolve();
});