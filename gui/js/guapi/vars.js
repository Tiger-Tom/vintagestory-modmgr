export default class {
    constructor(id) { this.id = id; }
    toString() { return this.id; }
    async store(val,
                behavior_if_exists /* one of "fail", "ignore" (don't change the value), or "change" */ = "fail") {
        return await $bridge.vars_store(this.id, val, behavior_if_exists);
    }
    async recall(deflt /* returned if the variable does not exist */ = null) {
        return await $bridge.vars_recall(this.id, deflt);
    }
    async remove(fail_if_not_exists = true) {
        return await $bridge.vars_remove(this.id, fail_if_not_exists);
    }
    async exists() { return await $bridge.vars_exists(this.id); }
};