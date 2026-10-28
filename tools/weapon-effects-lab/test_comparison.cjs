// Offline comparison-control and synchronization test; no browser/pixel claims.
const fs = require("node:fs"),
    vm = require("node:vm"),
    assert = require("node:assert/strict");
const html = fs.readFileSync(process.argv[2], "utf8");
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
let draws = 0;
const messages = [],
    nodes = new Map();
const context = new Proxy(
    {},
    {
        get(t, k) {
            return (
                t[k] ||
                ((...args) => {
                    for (const a of args) if (typeof a === "number") assert(Number.isFinite(a));
                    if (k === "drawImage") draws++;
                })
            );
        },
        set(t, k, v) {
            t[k] = v;
            return true;
        },
    },
);
function node(id) {
    if (!nodes.has(id))
        nodes.set(id, {
            value: id === "speed" ? ".5" : "",
            textContent: "",
            clientWidth: 650,
            clientHeight: 500,
            getContext: () => context,
            contentWindow: { postMessage: (d) => messages.push(d) },
        });
    return nodes.get(id);
}
const sandbox = {
    console,
    performance: { now: () => 0 },
    devicePixelRatio: 1,
    requestAnimationFrame() {},
    window: { addEventListener() {} },
    document: {
        hidden: false,
        getElementById: node,
        createElement: () => ({ complete: true, naturalWidth: 512, naturalHeight: 512 }),
    },
};
vm.createContext(sandbox);
vm.runInContext(script, sandbox, { timeout: 10000 });
assert.equal(messages.at(-1).scene, 1);
assert.equal(messages.at(-1).time, 0.79);
assert.match(node("particle").srcdoc, /mw34-comparison/);
assert(!html.includes("/*COMPARISON_DATA*/null"));
assert.equal(vm.runInContext("Object.keys(DATA.references.stock).length", sandbox), 31);
assert.equal(vm.runInContext("Object.keys(DATA.references.current).length", sandbox), 31);
for (const scene of [0, 1, 2])
    for (const bank of ["stock", "current"]) {
        node("effect").onchange({ target: { value: String(scene) } });
        node("bank").onchange({ target: { value: bank } });
        for (const age of [0, 0.05, 0.18, 0.4, 0.65, 0.9, 1.2, 1.6]) {
            node("timeline").oninput({ target: { value: String(age) } });
            const m = messages.at(-1);
            assert.equal(m.scene, scene);
            assert(Number.isFinite(m.time) && m.time <= 4);
        }
    }
node("replay").onclick();
assert.equal(vm.runInContext("age", sandbox), 0);
vm.runInContext("tick(100);", sandbox);
assert(vm.runInContext("age>0", sandbox));
assert(draws > 50, "Reference animations never draw");
// Exercise the actual bridge injected into the native viewer independently.
let handler,
    updates = 0;
const parent = {};
const target = {
    parent,
    scene: 1,
    t: 0,
    playing: true,
    Number,
    window: {
        addEventListener: (name, fn) => {
            if (name === "message") handler = fn;
        },
    },
    playLabel() {},
    draw() {
        updates++;
    },
};
vm.createContext(target);
const native = vm.runInContext("DATA.native", sandbox);
const bridge = native.match(/window.addEventListener\('message',event=>\{([\s\S]*?)\n\}\);/)[0];
vm.runInContext(bridge, target);
handler({ source: {}, data: { type: "mw34-comparison", scene: 0, time: 1.3 } });
assert.equal(updates, 0);
handler({ source: parent, data: { type: "mw34-comparison", scene: 0, time: 1.3 } });
assert.equal(updates, 1);
assert.equal(target.t, 1.3);
assert.equal(target.playing, false);
handler({ source: parent, data: { type: "mw34-comparison", scene: 0, time: Infinity } });
assert.equal(updates, 1);
console.log(
    `Comparison controls and native-frame synchronization passed; ${draws} reference draws. Browser pixels unverified.`,
);
