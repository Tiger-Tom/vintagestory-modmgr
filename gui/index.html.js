// top bar buttons
function new_window() {
    new $guapi.Window().duplicate();
}
function tutorial() {
    for (let m of ["thanks", "infotutor", "infotutor.2", "infotutor.3"])
        $l.alert(`[mg.${m};`);
}
function reload() {
    if ($l.confirm("[mg.confirm.rel;")) location.reload();
}

// mods-dir bar buttons
async function change_dir() {
    set_all_by_attr("d_w_chdir", "disabled", true);
    let mdir = await $g.open_dialog($wid, "folder", {
        directory: await $g.m.default_directory(),
    });
    if (mdir !== null) $e.mod_dir.value = mdir;
    set_all_by_attr("d_w_chdir", "disabled", false);
}
async function find_mods() {
    set_all_by_attr("d_w_fmods", "disabled", true);
    $mod_h.get_insert_mods($e.mod_container, $e.mod_dir.value);
    set_all_by_attr("d_w_fmods", "disabled", false);
}

// details box close button
function close_details() {
    $e.details.contentWindow.location.replace("about:blank");
    $e.details_container.style.display = "none";
}

// upon ready
$g.and_dom_ready.then(async function() {
    let lr = $lang.__ready.then(_ => set_all_by_attr("d_u_lang", "disabled", false));
    set_all_by_attr("d_u_guapi", "disabled", false);
    $e.details_container.resizable_frame = new ResizableFrame($e.details, $e.details_handle, false, true, {h: [12, Infinity]});
    if (!$sto.set("message.shown.first", true)) {
        lalert("[mg.first;"); lalert("[mg.thanks;");
    }
    await lr; $lang.assign_config($e.lang_conf);
    if (!($guapi.debug || $guapi.f("noinitialchdir"))) change_dir();
});