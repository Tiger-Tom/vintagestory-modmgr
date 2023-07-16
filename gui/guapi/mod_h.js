globalThis.$mod_h = {
    /* elements */
    _element_rm_bt(elem) {
        let bt = document.createElement("span");
        bt.classList.add("mod-element-remove-button");
        bt.onclick = elem.remove.bind(elem);
        bt.title = $l("[bt.modelem.rm.dsc;");
        bt.textContent = $l("[sy.bt.close;");
        return bt;
    },
    element(mod, version=true) {
        let li = document.createElement("li"),
            id = $mod_h.format(mod, "mod:%id%");
        li.classList.add("mod-element");
        li.id = id; li._mod = mod;
        li.textContent = $mod_h.format(mod, version ? $l("[mf.content.withversion;") : $l("[mf.content.withoutvers;"));
        li.title = $mod_h.format(mod, $l("[mf.tooltip;"));
        li.prepend($mod_h._element_rm_bt(li));
        return li;
    },
    apply_description(elem, desc, desc_frame) {
        elem._desc = desc;
        let a = document.createElement("a");
        a.textContent = $l("[sy.generic.info_i;");
        elem.insertBefore(a, elem.firstChild);
        a.onclick = function() {
            desc_frame.contentDocument.body.innerHTML = desc;
            desc_frame.parentNode.style.display = "unset";
        };
    },
    sort(parent, major_attr, reverse=false) {
        let mods = Array.from(parent.children);
        for (let m of mods) parent.removeChild(m);
        mods.sort((a,b) => a._mod[major_attr].localeCompare(b._mod[major_attr]));
        if (reverse) mods.reverse();
        for (let m of mods) parent.appendChild(m);
    },
    *inverse_insert(parent) {
        for (let e of parent.children)
            if (e._mod) yield e._mod;
    },
    async insert(parent, aiter, version=true) {
        for await (let m of aiter) {
            console.debug(`Found mod ${m[1]}`);
            parent.appendChild($mod_h.element(m[0], version));
        }
    },
    /* getting mods */
    async get_insert_mods(parent, path) {
        await $mod_h.insert(parent, await $g.m.from_directory(path));
    },
    /* upstream */
    async fetch(path) {
        
    },
    /* text */
    format(mod, fstring, on_not_found={}, scan_patt=/(?<!%)%(\w+?)%(?!%)/g) {
        let default_on_not_found = {
            id: $l("[mf.default.id;"),
            name: $l("[mf.default.name;"),
            desc: $l("[mf.default.desc;"),
            version: $l("[mf.default.version;"),
            source: $l("[mf.default.source;"),
        }, str = fstring;
        let nf = { ...default_on_not_found, ...on_not_found, };
        while (str.search(scan_patt) !== -1)
            str = str.replaceAll(scan_patt, (m, k, o, s) => nf.hasOwnProperty(k)
                ? (mod[k] ?? nf[k])
                : ($error("formatting_mod", m, `Bad f-string element "${m}" in "${s}"`) || `%%${m}%%`));
        return str.replaceAll("%%", "%"); // allow escapes with %%
    },
};