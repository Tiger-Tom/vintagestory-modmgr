function set_all_by_cname(classname, key, value) {
    for (let e of document.getElementsByClassName(classname)) e[key] = value;
}

$e = id => document.getElementById(id);
$e._load = function(el) {
    for (let e of el.children) {
        if (e.id && !e.id.startsWith("_")) $e[e.id] = e;
        if (e.hasChildNodes()) $e._load(e);
    }
}
$e._load(document);