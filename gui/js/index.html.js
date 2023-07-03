$g.and_dom_ready.then(async function() {
    set_all_by_cname("d_u_guapi", "disabled", false);
    $e.details_container.resizable_frame = new ResizableFrame($e.details, $e.details_handle, false, true, {h: [12, Infinity]});
    if (!$sto.set("message.shown.first", true)) {
        lalert("[mg.first;"); lalert("[mg.thanks;");
    }
    await $lang.__ready;
    $lang.assign_config($e.lang_conf);
    if (!($guapi.debug || $guapi.f("noinitialchdir"))) change_dir();
});