// reused elements
let br = () => document.createElement("br");
function debtext() {
    /* <div style="width: 100%; display: flex; flex-flow: row;"> */
    let d = document.createElement("div"); d.style.width = "100%";
    d.style.display = "flex"; d.style.flexFlow = "row";
    /* <hr style="width: 100%;"> */
    let h0 = document.createElement("hr"); h0.style.width = "100%"; let h1 = h0.cloneNode();
    /* <b>|DEBUG|</b> */
    let b = document.createElement("b"); b.innerText = "|DEBUG|";
    /* </div> */
    d.appendChild(h0); d.appendChild(b); d.appendChild(h1);
    return d;
}
function key_value(key, value) {
    /* <div> */
    let d = document.createElement("div");
    /* <b>...: </b> */
    let k = document.createElement("b"); k.innerText = `${key}: `;
    /* <code>...</code> */
    let v = document.createElement("code"); v.innerText = value;
    /* </div> */
    d.appendChild(k); d.appendChild(v);
    return d;
}
function bt(name, func) {
    let b = document.createElement("a");
    b.onclick = func; //b.classList.add("clickable");
    b.innerText = `>${name} `; b.appendChild(br()); return b;
}


/* <div style=...> */
let div = document.createElement("div");
div.style = "color: #00FF00; background-color: #000000;";
// [devtxt]
div.appendChild(debtext());
/* <div><b>WID: </b><code>...</code></div> */
div.appendChild(key_value("WID", $wid));
/* <div><b>URL: </b><code>...</code></div> */
div.appendChild(key_value("URL", location.href));
/* <a ...>...</a><br> */
div.appendChild(bt("Unapply Languages", () => $lang.unapply()));
/* <a ...>...</a><br> */
div.appendChild(bt("Apply Languages", () => $lang.applyALL()));
/* <a ...>...</a><br> */
div.appendChild(bt("Load New Language Pack", function() { $lang.load(prompt("Enter lang code"), false); }));
/* <a ...>...</a><br> */
div.appendChild(bt("Clear All Language Packs", $lang._trans.clear.bind($lang._trans)));
// [devtxt]
div.appendChild(debtext());
/* </div> */
document.body.appendChild(div); document.body.insertBefore(div, document.body.firstChild);