$sto = {
    get: function(key, deflt=undefined) {
        let v = globalThis.localStorage?.getItem(key);
        if (v === undefined) return deflt;
        return v;
    },
    set: function(key, val) {
        globalThis.localStorage?.setItem(key, val);
    },
    getset: function(key, val, deflt=undefined) {
        let v = $sto.get(key, deflt);
        $sto.set(key, val);
        return v;
    },
};

$g.and_dom_ready.then(async function() {
    $e.style_no_bg.remove();
    set_all_by_cname("d_u_guapi", "disabled", false);
    $e.details_container.resizable_frame = new ResizableFrame($e.details, $e.details_handle, false, true, {h: [12, Infinity]});
    if (!$sto.getset("message.shown.first", true, false)) {
        lalert("[mg.first;"); lalert("[mg.thanks;");
    }
    await $lang.__ready;
    $lang.select_pack
    $lang.applyALL();
    if (!($guapi.debug || $guapi.flags.has("noinitialchdir"))) change_dir();
});