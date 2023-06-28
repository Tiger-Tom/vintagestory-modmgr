// adapted from htmldom.dev/make-a-resizable-element
class ResizableFrame {
    constructor(frame, handle, resizeW=true, resizeH=true, constraints={w: [0, Infinity], h: [0, Infinity]}) {
        this.onmousedown = this.onmousedown.bind(this);
        this.onmouseup = this.onmouseup.bind(this);
        this.onmousemove = this.onmousemove.bind(this);
        
        this.c = constraints;
        
        this.mw = resizeW; this.mh = resizeH;
        this.f = frame; this.han = handle;
        
        this.han.addEventListener("mousedown", this.onmousedown);
        document.addEventListener("mouseup", this.onmouseup);
        this.f.contentDocument.addEventListener("mouseup", this.onmouseup);
        
        this.x = null; this.y = null; this.w = null; this.h = null;
    }
    onmousedown(e) {
        let style = getComputedStyle(this.f);
        this.w = parseInt(style.width, 10); this.h = parseInt(style.height, 10);
        this.x = e.clientX; this.y = e.clientY;
        document.addEventListener("mousemove", this.onmousemove);
        this.f.contentDocument.addEventListener("mousemove", this.onmousemove);
    }
    onmouseup(e) {
        document.removeEventListener("mousemove", this.onmousemove);
        this.f.contentDocument.removeEventListener("mousemove", this.onmousemove);
        this.x = null; this.y = null; this.w = null; this.h = null;
    }
    onmousemove(e) {
        if (this.mw)
            this.f.style.width = `${this.constrain(this.w + e.clientX - this.x, this.c.w)}px`;
        if (this.mh)
            this.f.style.height = `${this.constrain(this.h + e.clientY - this.y, this.c.h)}px`;
    }
    constrain(v, c) { return (v < c[0] ? c[0] : v > c[1] ? c[1] : v); }
}

/*
class _Abstract_ResizableFrameBase extends HTMLElement {
    constructor() {
        super();
        if (this.constructor === _Abstract_ResizableFrameBase)
            throw new Error("_Abstract_ResizableFrameBase cannot be instantiated -- it's abstract!");
    }
    /* attributes *\/
    verifyAttributes(attrs=null) {
        ((attrs === null)
            ? this.constructor.required_attributes
            : this.constructor.required_attributes.filter(attr => attrs.includes(attr))
        ).forEach(attr => {
            if (!this.hasAttribute(attr))
                throw new Error(`Required attribute ${attr} not supplied`);
        });
    }
    static get observedAttributes() {
        return this.required_attributes;
    }
    attributeChangedCallback(name) {
        verifyAttributes([name]);
    }
}

class ResizableFrame extends _Abstract_ResizableFrameBase {
    static stored_frames = {};
    static required_attributes = ["frame-id", "allowed-directions"];
    constructor() {
        super();
        this.attachShadow({ mode: "open", });
    }
    /* attributes *\/
    attributeChangedCallback(name, oldval, newval) {
        super.attributeChangedCallback(name);
    }
    /* element initialization *\/
    connectedCallback() {
        super.connectedCallback();
    }
}
window.customElements.define("resizable-frame", ResizableFrame);

class ResizableFrameHandle extends _Abstract_ResizableFrameBase {
    static required_attributes = ["frame-id", "pull-directions"];
    constructor() {
        super();
    }
    /* attributes *\/
    attributeChangedCallback(name, oldval, newval) {
        super.attributeChangedCallback(name);
    }
    /* element initialization *\/
    connectedCallback() {
        super.connectedCallback();
    }
}
window.customElements.define("frame-handle", ResizableFrameHandle);*/