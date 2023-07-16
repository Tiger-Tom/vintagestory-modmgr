globalThis.$sto = {
    get: function(key, deflt=undefined) {
        let v = globalThis.localStorage?.getItem(key);
        return v ?? deflt;
    },
    set: function(key, val) {
        let v = $sto.get(key);
        globalThis.localStorage?.setItem(key, val);
        return v;
    },
};