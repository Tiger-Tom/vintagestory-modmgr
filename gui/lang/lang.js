globalThis.$lang = {
    /** sorta-config **/
    key_split_char: ".",
    /* text to replace */
    look_seq: /\[([\w\.$]+?);/g, // [key;
    /* parsing the lang file */
    escaped_linebreak: /[^\S\n]*[^\\]\\([^\n]*)\n[^\S\n]*/g,
    line_pattern: /^[^\S\n]*([\w\.$]+)[^\S\n]*=[^\S\n]*(.*?)[^\S\n]*$/gm,
    /* modified fields */
    fields_lenient: [ // element can have children (feels kind of wrong to write)
        "alt", "cite", "label", "placeholder", "title", ],
    fields_strict: [ // only if element does not have children (also feels wrong to write)
        "textContent", ],
    /* formatting */
    do_not_format: [
        "_flags", "_config", ],
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
    trans: {_flags: undefined, _config: undefined, mg: {}}, _trans: new Set(),
    _trans_subobject_toString: function() {
        if (this.$VALUE === undefined) return $lang._err(this.$INDEX, 7 /* 7 looks sorta like t, for toString */);
        /*let str = "";
        if ($lf.debug$attach_src)     str += this.$SOURCE+">";
        if ($lf.debug$attach_key)     str += this.$INDEX+"=";
        if ($lf.decode_as_uri) return str +  decodeURI(this.$VALUE);
        else                   return str +  this.$VALUE;*/
        return this.$VALUE;
    },
    _trans_subobject_valueOf: () => parseInt(this.$VALUE),
};

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

globalThis.$lf = $l._flags = k => $l._flags[k]?.valueOf();
globalThis.$lc = $l._config = k => $l._config[k]?.valueOf();

$lang.loads = async function(langs, sync=true, applyall=true) {
    if (sync)
        for (let l of langs)
            await $lang.load(l, false);
    else
        await Promise.all(langs.map(l => $lang.load(l, false)));
    if (applyall) return $lang.applyALL();
};

$lang.load = async function(lang, applyall=true, resetflags=true) {
    if (resetflags) Object.keys($lf).forEach(p => delete $lf[p]);
    let uri = `lang/${lang}.lang`;
    console.info(`Fetching lang at ${uri}`);
    let text = (await (await fetch(uri)).text()).replaceAll($lang.escaped_linebreak, "$1");
    for (let [_,key,val] of text.matchAll($lang.line_pattern)) {
        //console.log(key); console.log(val);
        let o = $l,
            ks = key.split($lang.key_split_char);
        for (let k in ks)
            o = (o[ks[k]] = o[ks[k]] || {
                toString: $lang._trans_subobject_toString,
                valueOf: $lang._trans_subobject_valueOf,
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

$lang.applyALL = async function() {
    if (document.readyState === "loading")
        await new Promise(resolve => window.addEventListener("DOMContentLoaded", resolve));
    $lang.apply(document.body);
};
$lang.apply = async function(elem=document.body) {
    let p = Promise.all(Array.from(elem.children || []).map($lang.apply));
    for (let r = 0; r < ($lc("passes") || 1); r++)
        $lang.fields_lenient.forEach(f => elem[f] && (elem[f] = $l(elem[f])));
    if (elem.children.length) return p;
    for (let r = 0; r < ($lc("passes") || 1); r++)
        $lang.fields_strict.forEach(f => elem[f] && (elem[f] = $l(elem[f])));
};