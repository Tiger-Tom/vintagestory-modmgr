$g.and_dom_ready.then(function() {
    $e.style_no_bg.remove();
    set_all_by_cname("d_u_guapi", "disabled", false);
    $e.details_container.resizable_frame = new ResizableFrame($e.details, $e.details_handle, false, true, {h: [12, Infinity]});
    if (!globalThis.localStorage?.getItem("message.shown.first")) {
        globalThis.localStorage?.setItem("message.shown.first", 1);
        lalert("[mg.first;"); lalert("[mg.thanks;");
    }
    change_dir();
});