globalThis.$error = function(where, code, msg) {
    console.debug(`$error on ("${where}", "${code}", "${msg}")`);
    let m = $error._formatmsg(where, code, msg);
    for (let b of $error.config[where].split("+"))
        $error._behavior_handlers[b](m);
};

$error._formatmsg = (where, code, msg) => `--An error occured in "${where}"--\n${msg}\n--Error Code "${where}:${code}"--`;
$error._error_is_error = mbye => (mbye instanceof Error) || (Error.isPrototypeOf(mbye)) || (mbye?.stack && mbye?.message);
$error._ask_copy_to_clipboard = async function(text) {
    if (navigator?.clipboard?.writeText) {
        if (confirm(`${text}\n\nPress OK to copy error message to clipboard`))
            navigator.clipboard.writeText(text);
    } else alert(text); // if it's unsupported, just alert
};
$error._remove_own_base = url => url?.startsWith(location.origin) ? url.slice(location.origin.length) : url;

$error.code_from_event = e => $error.code_from_error(e?.error || e?.reason);
$error.code_from_error = e => $error._error_is_error(e)
    ? `${e?.sourceURL && $error._remove_own_base(e?.sourceURL) || "source?"}#L${e?.line || "_"}C${e?.column || "_"}:${e?.name}`
    : `?unknown_type=${e?.constructor?.name}`;

$error._behavior_handlers = {
    "log_info": console.info,
    "log_warn": console.warn,
    "log_error": console.error,
    "annoy_user": alert.bind(window),
    "offer_copy": $error._ask_copy_to_clipboard,
};

$error.config = {
// generic
    "global_error_event":      "log_error+offer_copy",
    "global_promise_uhreject": "log_error+offer_copy",
//  "global_promise_hreject":  "log_info",
    "import":                  "log_error+offer_copy",
// language
    "language":                "log_warn+annoy_user",
    "lang_pack":               "log_warn+annoy_user",
// GU/API + mods
    "load_guapi_module":       "log_error+offer_copy",
    "pywebview":               "log_error+offer_copy",
    "formatting_mod":          "log_warn",
};

globalThis.addEventListener("error", function(e) {
    $error("global_error_event", // where
        $error.code_from_event(e), // code
        `The global object raised an error event:\n ${e.message}\n--Stack--\n${e?.error?.stack}`, // msg
    );
});
globalThis.addEventListener("unhandledrejection", function(e) {
    $error("global_promise_uhreject", // where
        $error.code_from_event(e), // code
        `A rejected promise wasn't handled:\n ${e.reason}\n--Stack (if present)--\n${e?.reason?.stack}`, // msg
    );
});