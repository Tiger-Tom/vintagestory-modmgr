/*
    This allows potential future migration to different APIs
*/

globalThis.$wid ??=
    ((location.href === "about:blank") ?
        null : (location.search === "") ?
            "main" : location.search.substring(1));

globalThis.$bridge = {
    $pwv: undefined,
    $_load: function() {
        $bridge.$pwv = pywebview;
        Object.assign($bridge, $bridge.$pwv.api);
    },
    $ready: undefined,
};

$bridge.$ready = new Promise(resolve => {
    if (globalThis.pywebview?.api) return resolve();
    globalThis.addEventListener("pywebviewready", resolve);
}).then($bridge.$_load);