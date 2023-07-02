globalThis.$guapi = {};
globalThis.$g = $guapi; // shortcut
$guapi.ready = new Promise((resolve) => $guapi._resolve = resolve);
$guapi.and_dom_ready = Promise.all([$guapi.ready, 
    new Promise(resolve =>
        document.readyState !== "loading" ? resolve() 
        : document.addEventListener("DOMContentLoaded", resolve)
    )
]);

await import("./guapi/api_bind.js").catch(e => $error(
    "import",
    $error.code_from_error(e),
    `An error occured whilst binding api through api_bind.js:\n ${e.message}`,
));
await $bridge.$ready.catch(e => $error(
    "pywebview",
    $error.code_from_error(e),
    `An error occured whilst attempting to bridge pywebview API:\n ${e.message}`,
));

Object.assign(globalThis.$guapi, {
    /* submodules */
    Var: null,    V: null,
    Window: null, W: null,
    Magic: null,  M: null,
    mods: null,   m: null,
    /* submodule initialization */
    _add: function(longname, shortname, module) {
        let _catch = promise => e => $error(
            "load_guapi_module",
            `${shortname}${promise ? ">promise" : ""}:${$error._formaterrev(e)}`,
            `An error occured while ${promise ? "resolving promises for" : "loading"} the GU/API module "${longname}":\n ${e.message}`,
        );
        this._promises.push(
            new Promise((resolve) => 
                module.then(m => {
                    this[longname] = m.default;
                    this[shortname] = m.default;
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
    flag: (key) => $guapi.flags.has(key),
    flags: undefined,
    /** functions **/
    uuid: $bridge.uuid,
    open_dialog: async function(window_id=$wid, dtype /*one of "file", "save", or "folder"*/ = "file", kwargs={}) {
        /* dtype: one of "file", "save", or "folder" */
        return await $bridge.open_dialog(window_id, dtype, kwargs);
    },
});

// add submodules
$guapi._add("Var",    "V", import("./guapi/vars.js"));
$guapi._add("Window", "W", import("./guapi/windows.js"));
$guapi._add("Magic",  "M", import("./guapi/magic.js"));
$guapi._add("mods",   "m", import("./guapi/mods.js"));

// final promise
Promise.all($guapi._promises).then(async function() {
    $guapi.debug = await $bridge.is_debug(); // resolve whether or not we are running debug
    $guapi.flags = new Set(await $bridge.get_flags());
    if (($guapi.debug && !$guapi.flag("nodebug")) || $guapi.flag("debug")) {
        let ifr = document.createElement("iframe"); ifr.src = "./debug.html";
        document.body.appendChild(ifr); document.body.insertBefore(ifr, document.body.firstChild);
        ifr.addEventListener("load", function() {
            ifr.style.height = ifr.contentDocument.documentElement.scrollHeight+"px";
        }); ifr.style.width = "100%";
    }
    $guapi._resolve();
});