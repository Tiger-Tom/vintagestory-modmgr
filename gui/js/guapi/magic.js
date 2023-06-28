const MagicMethod = class extends (async()=>{}).constructor {
    constructor(id) {
        super(["...args"], `return $bridge.magic_call("${id}", ...args);`);
        this.id = id;
    }
    toString() { return this.id; }
    static async from_js(js, target_window=$wid,
            store /* the result will be placed in this variable after promises are resolved */ = null,
            callback /* the magic method to be called with the result after promises are resolved */ = null,
            argrepl /* a list of strings, where each string in "js" will be replaced with the JSON representation of the argument at that index passed to the function */ = [],
            strict_arguments /* whether or not to fail when the given arguments are shorter or longer than argrepl */ = true) {
        /* register a magic Javascript method that runs Javascript in a specific window
           returns the result (as much as it can be JSON serialized), but without resolving promises */
        return new MagicMethod(await $bridge.magic_register_js(target_window.toString(), js, store, callback, argrepl, strict_arguments));
    }
    static convert_object(obj) {
        /* converts any of the objects keys that end with () into magic methods */
        let o = {...obj};
        for (let k in o)
            if ((typeof(k) === "string") && (typeof(o[k]) === "string"))
                if (k.endsWith("()")) o[k.slice(0, -2)] = new MagicMethod(o[k]);
        return o;
    }
    static convert_object_to_iterable(obj, track_vals=false, relaxed_send=true) {
        let o = MagicMethod.convert_object(obj);
        o._is_consumed = false;
        o[Symbol.asyncIterator] = function() {
            let hass = typeof o.send === "function";
            if (!((typeof o.__next__ === "function") || hass))
                throw "Supposed \"iterator\" object has neither a __next__ nor a send function!";
            let tracked = track_vals ? [] : undefined;
            let body = `
                if (o._is_consumed) return true;
                try {
                    let v = await o.${hass ? "send(nval)" : "__next__()"};
                    ${track_vals ? "tracked.push(v);" : ""}
                    return {value: v, done: false};
                }
                catch (e) {
                    if (e.name === "StopIteration" || e.name === "MagicNotFound") {
                        o._is_consumed = true;
                        return {value: tracked, done: true};
                    }
                    throw e;
                }`, af = async function(){}.constructor;
            return {
                next: hass ? af(`nval=${relaxed_send ? "null" : "undefined"}`, body) : af(body),
            };
        }; return o;
    }
    async unregister(fail_if_not_exists=true) {
        /* unregisters this magic method in the backend */
        return await $bridge.magic_unregister(this.id, fail_if_not_exists);
    }
    async is_registered() {
        /* returns whether or not the magic method is registered */
        return await $bridge.magic_is_registered(this.id);
    }
    async is_javascript() {
        /* returns whether or not the magic method is a Javascript method */
        return await $bridge.magic_is_js(this.id);
    }
    static async list_all() {
        /* returns a list of every magic function ID */
        return await $bridge.magic_ls();
    }
};
export default MagicMethod;