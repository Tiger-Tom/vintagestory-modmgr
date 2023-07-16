globalThis.bt = {};

// top bar buttons
bt.new_window = function() {
    new $guapi.Window().duplicate();
};
bt.tutorial = function() {
    for (let m of ["thanks", "infotutor", "infotutor.2", "infotutor.3"])
        $l.alert(`[mg.${m};`);
};
bt.reload = function() {
    if ($l.confirm("[mg.confirm.rel;")) location.reload();
};

// mods-dir bar buttons
bt.change_dir = async function() {
    set_all_by_attr("d_w_chdir", "disabled", true);
    let mdir = await $g.open_dialog($wid, "folder", {
        directory: await $g.m.default_directory(),
    });
    if (mdir !== null) $e.mod_dir.value = mdir;
    set_all_by_attr("d_w_chdir", "disabled", false);
};
bt.find_mods = async function() {
    set_all_by_attr("d_w_fmods", "disabled", true);
    $mod_h.get_insert_mods($e.mod_container, $e.mod_dir.value);
    set_all_by_attr("d_w_fmods", "disabled", false);
};

// mods container container buttons
bt.sort_mods = function() { $mod_h.sort($e.mod_container, "name"); };
bt.clear_mods = function() {
    if (!$l.confirm("[mg.confirm.cmods;")) return;
    for (let m of [...$e.mod_container.getElementsByTagName("li")])
        m.remove();
}

// details box close button
bt.close_details = function() {
    $e.details.contentWindow.location.replace("about:blank");
    $e.details_container.style.display = "none";
};

// upon ready
$g.and_dom_ready.then(async function() {
    let lr = $lang.__ready.then(_ => set_all_by_attr("d_u_lang", "disabled", false));
    set_all_by_attr("d_u_guapi", "disabled", false);
    $e.details_container.resizable_frame = new ResizableFrame($e.details, $e.details_handle, false, true, {h: [12, Infinity]});
    if (!$sto.set("message.shown.first", true)) {
        $l.alert("[mg.first;"); $l.alert("[mg.thanks;");
    }
    await lr; $lang.assign_config($e.lang_conf);
    if ($guapi.f("autostart")) {
        $e.mod_dir.value = await $g.m.default_directory();
        bt.find_mods();
    } else if (!($g.debug || $g.f("noinitialchdir"))) bt.change_dir();
    (new MutationObserver((r,o) => {
        if (r.reduce((n,mr) => n+mr.addedNodes.length-mr.removedNodes.length, 0))
            $e.mod_container_container.style.display = $e.mod_container.children.length ? "block" : "none";
    })).observe($e.mod_container, {childList:true});
});