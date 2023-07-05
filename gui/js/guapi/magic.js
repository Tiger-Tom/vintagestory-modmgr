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
        return (await this.reflect()).type === "js";
    }
    static async list_all() {
        /* returns a list of every magic function ID */
        return await $bridge.magic_ls();
    }
    async reflect(refresh=false) {
        /* returns information about the magic function, caching it to be used again */
        if ((this.__reflection === undefined) || refresh)
            this.__reflection = await $bridge.magic_reflect(this.id);
        return this.__reflection;
    }
    
    static convert_object(obj, auto_iter=true) {
        /* converts any of the objects keys that end with () into magic methods */
        let o = {...obj};
        for (let k in o)
            if ((typeof(k) === "string") && (typeof(o[k]) === "string"))
                if (k.endsWith("()")) o[k.slice(0, -2)] = new MagicMethod(o[k]);
        return o;
    }
    static ITER_NEXT = 0b001;
    static ITER_SEND = 0b010;
    static ITER_ITER = 0b100;
    static object_can_be_iterable(obj) {
        /* Returns 0...
            +ITER_NEXT if it can __next__
            +ITER_SEND if in can send,
            +ITER_ITER if it already has Symbol.asyncIterator */
        let val = (obj.__next__ instanceof Function) ? MagicMethod.ITER_NEXT : 0;
        if (obj.send instanceof Function) val += MagicMethod.ITER_SEND;
        if (obj[Symbol.asyncIterator]) val += MagicMethod.ITER_ITER;
        return val;
    }
    static convert_object_to_iterable(obj, track_vals=false, relaxed_send=true) {
        let o = MagicMethod.convert_object(obj), can = MagicMethod.object_can_be_iterable(o);
        o._is_consumed = false;
        o[Symbol.asyncIterator] = function() {
            if (!can)
                throw "Supposed \"iterator\" object has neither a __next__ nor a send function!";
            let tracked = track_vals ? [] : undefined;
            let body = `
                if (o._is_consumed) return true;
                try {
                    let v = await o.${(can & MagicMethod.ITER_SEND) ? "send(nval)" : "__next__()"};
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
                next: (can & MagicMethod.ITER_SEND) ? af(`nval=${relaxed_send ? "null" : "undefined"}`, body) : af(body),
            };
        }; return o;
    }
};
export default MagicMethod;