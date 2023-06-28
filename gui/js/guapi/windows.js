const Window = class {
    constructor(id) { this.id = id; }
    toString() { return this.id; }
    static async create(title, kwargs={}) { return new Window(await $bridge.win_create(title, kwargs)); }
    async close() { await $bridge.win_close(this.id); }
    
    async execute(js,
            store /* the result will be placed in this variable after promises are resolved */ = null,
            callback /* the magic method to be called with the result after promises are resolved */ = null) {
        /* executes Javascript inside the window, returning the result without resolving promises */ 
        return await $bridge.win_execute(this.id, js, store, callback);
    }
    async call(js, magic, ...args) {
        /* calls the given magic function inside of the window, overriding the target window it was defined with */
        return await $bridge.win_call(this.id, magic.toString(), ...args);
    }
    
    async get_cookies() { return await $bridge.win_cookies(this.id); }
    async get_elements() { return await $bridge.win_elements(this.id); }
    
    async show() { await $bridge.win_show(this.id, true); }
    async hide() { await $bridge.win_show(this.id, false); }
    
    async size(x, y) { await $bridge.win_size(this.id, [x, y]); }
    async minimize() { await $bridge.win_size(this.id, "minimized"); }
    async restore() { await $bridge.win_size(this.id, "restored"); }
    async fullscreen() { await $bridge.win_size(this.id, "fullscreen"); }
    
    async load_html(code) { await $bridge.win_load(this.id, "html", code); }
    async load_css(code) { await $bridge.win_load(this.id, "css", code); }
    
    async move(x, y) { await $bridge.win_move(this.id, x, y); }
    
    async title(text) { await $bridge.win_set_title(this.id, text); }
    
    async url(url /* setting this to null returns the current URL, otherwise sets the URL */ = null) {
        return await $bridge.win_url(url);
    }
    
    async register_event_handler(event /* see https://pywebview.flowrl.com/guide/api.html#events */, magic) {
        await $bridge.win_register_eventhandler(this.id, event, magic.toString());
    }
    async remove_event_handler(event, magic) {
        await $bridge.win_remove_eventhandler(this.id, event, magic.toString());
    }
};
export default Window;