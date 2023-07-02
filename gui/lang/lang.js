globalThis.$lang = {
    /** sorta-config **/
    key_split_char: ".",
    /* text to replace */
    look_seq: /\[([\w\.$]+?);/g, // [key;
    /* parsing the lang file */
    escaped_linebreak: /[^\S\r\n]*[^\\]\\([^\r\n]*)\r?\n[^\S\r\n]*/g,
    line_pattern: /^[^\S\n]*([\w\.$]+)[^\S\n]*=[^\S\n]*(.*?)[^\S\n]*$/gm,
    /* parsing the pack file */
    pack_id: /^[^\S\n]*_pack\.id[^\S\n]*=[^\S\n]*(.*?)[^\S\n]*$/m,
    pack_name: /^[^\S\n]*_pack\.name[^\S\n]*=[^\S\n]*(.*?)[^\S\n]*$/m,
    pack_cred: /^[^\S\n]*_pack\.credit[^\S\n]*=[^\S\n]*(.*?)[^\S\n]*$/m,
    /* modified fields */
    fields_lenient: [ // element can have children (feels kind of wrong to write)
        "alt", "cite", "label", "placeholder", "title", ],
    fields_strict: [ // only if element does not have children (also feels wrong to write)
        "textContent", ],
    /* formatting */
    do_not_format: [
        "_pack", "_flags", "_config", ],
    /* backup and restore */
    backup_attr: "$_LANG_BACKUP",
    /** end of sorta-config **/
    /* functions (unset) */
    loads: undefined, load: undefined,
    apply: undefined, applyALL: undefined,
    /* mutation observer (unset) */
    observer: undefined,
    ocallback: undefined,
    /* for errors */
    _err: (key, s) => $error("language", `${key}:${s}`, `[${s}] TRANSLATION NOT FOUND: ${key}`) || `!${s}{${key}}`,
    /* unbuilt lang */
    trans: {}, _trans: new Set(), packs: {},
    _trans_subobject_toString: function() {
        if (this.$VALUE === undefined) return $lang._err(this.$INDEX, 7 /* 7 looks sorta like t, for toString */);
        /*let str = "";
        if ($lf.debug$attach_src)     str += this.$SOURCE+">";
        if ($lf.debug$attach_key)     str += this.$INDEX+"=";
        if ($lf.decode_as_uri) return str +  decodeURI(this.$VALUE);
        else                   return str +  this.$VALUE;*/
        return this.$VALUE;
    },
};

// apply langs to text
globalThis.$l = function(text) {
    if (typeof text !== "string") return text;
    let t = text;
    while (t.match($lang.look_seq))
        t = t.replaceAll($lang.look_seq, function(m, key) {
            if (!$lang._trans.has(key)) return $lang._err(key, 5 /* 5 looks like S, for Set */);
            //console.debug(`Replacing ${key}`);
            let o = $l;
            for (let k of key.split($lang.key_split_char)) o = o[k];
            return $l(o);
        });
    return t;
}; Object.assign($l, $lang.trans);
$lang.trans = $l;
// get flags / config
globalThis.$lf = k => parseInt($l._flags?.[k]?.$VALUE);
globalThis.$lc = k => parseInt($l._config?.[k]?.$VALUE);
// loading language files / packs
$lang.loads = async function(langs, sync=true, applyall=true) {
    if (sync)
        for (let l of langs)
            await $lang.load(l, false);
    else
        await Promise.all(langs.map(l => $lang.load(l, false)));
    if (applyall) return $lang.applyALL();
};
$lang.load = async function(lang, applyall=false, resetflags=true, already_fetched=false) {
    if (resetflags) Object.keys($lf).forEach(p => delete $lf[p]);
    let text = lang;
    if (!already_fetched) {
        let uri = `lang/${lang}.lang`;
        console.info(`Fetching lang at ${uri}`);
        text = (await (await fetch(uri)).text());
    }
    text = text.replaceAll($lang.escaped_linebreak, "$1");
    for (let [_,key,val] of text.matchAll($lang.line_pattern)) {
        let o = $l,
            ks = key.split($lang.key_split_char);
        for (let k in ks)
            o = (o[ks[k]] = o[ks[k]] || {
                toString: $lang._trans_subobject_toString,
                /*k is a string for some reason... probably a "key", not an index?*/
                $INDEX: ks.slice(0, ++k).join($lang.key_split_char),
            });
        o.$SOURCE = lang;
        $lang._trans.add(o.$INDEX);
        /* format it! */ // it's 030300, not fun // now 042113
        //console.debug(`Setting ${key}...; Formatting "${val}" with flags, config:`);
        //console.table($lf); console.table($lc);
        if ($lang.do_not_format.includes(ks[0])) o.$VALUE = val;
        else {
            o.$VALUE = "";
            if ($lc("debug$attach_src")) o.$VALUE += o.$SOURCE+">";
            if ($lc("debug$attach_key")) o.$VALUE += o.$INDEX+"=";
            o.$VALUE += ($lc("decode_as_uri")) ? decodeURI(val) : val;
        }
        //console.debug(`Formatting complete: ${o.$VALUE}`);
    }
    if (resetflags) Object.keys($lf).forEach(p => delete $lf[p]);
    if (applyall) return $lang.applyALL();
};
/// packs
$lang.loadpacks = async function(packs) {
    let ploaded = {};
    await Promise.all(packs.map(p => fetch(`lang/packs/${p}.langp`)
        .then(r => r.text())
        .then(function(t) {
            let id = t.match($lang.pack_id)[1];
            ploaded[id] = {
                id: id, data: t,
                name: t.match($lang.pack_name)[1],
                credits: t.match($lang.pack_cred)[1],
            };
        })
    ));
    Object.assign($lang.packs, ploaded);
};
$lang.select_pack = async function(id) {
    $lang.packs[id]
    $lang.load($lang.packs[id].data, false, true, true);
    $lang.strip(); $lang.applyALL();
};
// applying languages to elements
$lang.applyALL = async function() {
    if (document.readyState === "loading")
        await new Promise(resolve => window.addEventListener("DOMContentLoaded", resolve));
    $lang.apply(document.body);
};
$lang.apply = async function(elem=document.body) {
    function mutate_field(elem, field) {
        if ((elem[field] === undefined) || (elem[field] === "")) return;
        if (elem[$lang.backup_attr] === undefined) elem[$lang.backup_attr] = {};
        if (elem[$lang.backup_attr][field] === undefined)
            elem[$lang.backup_attr][field] = elem[field];
        elem[field] = $l(elem[field]);
    }
    let p = Promise.all(Array.from(elem.children || []).map($lang.apply));
    for (let r = 0; r < ($lc("passes") || 1); r++)
        $lang.fields_lenient.forEach(f => mutate_field(elem, f));
    if (elem.children.length) {
        await p; return;
    }
    for (let r = 0; r < ($lc("passes") || 1); r++)
        $lang.fields_strict.forEach(f => mutate_field(elem, f));
    await p;
};
$lang.strip = async function(elem=document.body, recurse=true) {
    if (elem[$lang.backup_attr] !== undefined) {
        Object.assign(elem, elem[$lang.backup_attr]);
        elem[$lang.backup_attr] = undefined;
    }
    if (recurse && elem.hasChildNodes())
        await Promise.all(Array.from(elem.children || []).map(e => $lang.strip(e, true)));
}