export default {
    async default_directory() {
        /* the default directory for mod installation */
        return await $bridge.mods_default_directory();
    },
    async from_directory(path) {
        /* returns a magic iterable of mods in a path */
        return $guapi.M.convert_object_to_iterable(await $bridge.mods_from_directory(path));
    },
    async get_metadatas(mods, callback_start, callback_stop) {
        /* gets metadatas from mods, running magic callback_start and callback_stop for each modid */
        return await $bridge.mods_get_metadatas(mods, callback_start.toString(), callback_stop.toString());
    },
    async compare_versions(v0, v1) {
        /* compares two versions, returns 0 if they are the same, -1 if v0 < v1, or v1 if v0 > v1 */
        return await $bridge.mods_compare_versions(v0, v1);
    }
};