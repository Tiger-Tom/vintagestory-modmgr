globalThis.$error = function(where, code, msg, attach_stack_if_present=true) {
    console.debug(`$error on ("${where}", "${code}", "${msg}")`);
    let m = $error._formatmsg(where, code, msg);
    for (let b of $error.config[where].split("+"))
        $error._behavior_handlers[b](m);
};

$error._formatmsg = (where, code, msg) => `--An error occured in "${where}"--\n${msg}\n--Error Code "${where}/${code}"--`;

$error.code_from_event = e => $error.code_from_error(e.error);
$error.code_from_error = e => `${e?.sourceURL ? e.sourceURL.split("/").slice(-1) : "unknown_source"}#L${e?.line || "_"}C${e?.column || "_"}:${e?.name}`;

$error._behavior_handlers = {
    "silent": () => void(0),
    "log_warn": console.warn,
    "log_error": console.error,
    "annoy_user": alert.bind(window),
};

$error.config = {
    "global_event":      "annoy_user+log_error",
    "language":          "annoy_user+log_warn",
    "lang_pack":         "annoy_user+log_warn",
    "load_guapi_module": "annoy_user+log_error",
    "formatting_mod":    "log_warn",
    "import":            "annoy_user+log_error",
    "pywebview":         "annoy_user+log_error",
};

globalThis.addEventListener("error", function(e) {
    $error("global_event", // where
        $error.code_from_event(e), // code
        `The global object raised an error event:\n ${e.message}`, // msg
    );
});