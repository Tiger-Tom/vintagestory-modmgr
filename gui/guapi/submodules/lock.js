export default class {
    constructor(id) { this.id = id; }
    toString() { return this.id; }
    async is_set() { return await $bridge.lock_is_set(this.id); }
    obtain(wait=5) {
        /* if wait is truthy, then we return a promise and check every {wait} seconds if the lock is available */
        /* otherwise, returns a promise that contains a boolean of whether or not we obtained the lock */
        if (!wait) return $bridge.lock_obtain(this.id);
        return new Promise(resolve => {
            async function check() {
                if (await $bridge.lock_obtain(id)) resolve();
                else setTimeout(check, wait*1000);
            }; check();
        });
    }
    async release() { return await $bridge.lock_release(this.id); }
};