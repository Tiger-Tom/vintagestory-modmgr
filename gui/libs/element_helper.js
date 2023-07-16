globalThis.set_all_by_cname = function(classname, key, value) {
    for (let e of document.getElementsByClassName(classname)) e[key] = value;
};
globalThis.set_all_by_attr = function(attr, key, value) {
    for (let e of document.querySelectorAll(`[${attr}]`)) e[key] = value;
}

globalThis.$e = id => document.getElementById(id);
$e._load = function(el) {
    for (let e of el.children) {
        if (!e.id?.startsWith("_")) $e[e.id] = e;
        if (e.hasChildNodes()) $e._load(e);
    }
};
$e._load(document);