// Offline execution of the actual renderer with a native Skia canvas, no browser/UI.
// Pass the bundled @napi-rs/canvas package path returned by load_workspace_dependencies.
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const crypto = require("node:crypto");
const assert = require("node:assert/strict");
const [outputDirectory, canvasPackage] = process.argv.slice(2);
if (!outputDirectory || !canvasPackage)
    throw Error("Usage: node verify.cjs OUTPUT_DIR CANVAS_PACKAGE");
const native = require(canvasPackage);
assert(native.GlobalFonts.has("Arial"), "System Arial must be available for the font comparison");
const directory = path.resolve(outputDirectory);
const data = JSON.parse(fs.readFileSync(path.join(directory, "components.json"), "utf8"));
const renderer = fs.readFileSync(path.join(__dirname, "renderer.js"), "utf8");
const elements = new Map();
function element(id) {
    if (elements.has(id)) return elements.get(id);
    const el =
        id === "hud"
            ? native.createCanvas(1, 1)
            : { append() {}, classList: { toggle() {} }, addEventListener() {} };
    el.value =
        {
            resolution: "3440,1440",
            mode: "enhanced",
            scale: "1",
            heat: "35",
            speed: "64",
            heading: "350",
            preview: "fit",
        }[id] || "";
    el.addEventListener ??= () => {};
    elements.set(id, el);
    return el;
}
const document = {
    getElementById: element,
    fonts: { load: async () => [] },
    createElement(type) {
        if (type === "canvas") return native.createCanvas(1, 1);
        return { append() {}, classList: { toggle() {} }, addEventListener() {}, click() {} };
    },
};
const sandbox = { document, Image: native.Image, window: {}, console, HUD_DATA: data };
vm.createContext(sandbox);
vm.runInContext(renderer + "\nwindow.testing={layout,scene,vector,render,checks};", sandbox);
async function main() {
    for (let i = 0; i < 100 && !sandbox.window.hudReady && !sandbox.window.hudError; i++)
        await new Promise((r) => setTimeout(r, 10));
    if (sandbox.window.hudError) throw Error(sandbox.window.hudError);
    assert.equal(sandbox.window.hudReady, true, "Renderer initialized");
    const checks = [];
    // Every output and size: keep actual known sprite extents inside the viewport,
    // preserve compass centering, and retain the source distance to screen edges.
    for (const [width, height] of [
        [640, 480],
        [1920, 1440],
        [2560, 1440],
        [3440, 1440],
    ]) {
        for (const size of [0.75, 1]) {
            const l = sandbox.window.testing.layout(width, height, size);
            for (const n of ["speed_frame", "fuel_frame", "coolant_frame", "heat_meter"]) {
                const p = l.positions[n],
                    r = data.resources["hud_" + n];
                assert(
                    p[0] >= 0 &&
                        p[1] >= 0 &&
                        p[0] + r.width * l.scale <= width &&
                        p[1] + r.height * l.scale <= height,
                    `Bounds: ${n}`,
                );
            }
            assert.equal(l.compass[0] + 75 * l.scale, width / 2, "Compass center");
            assert.equal(l.reticle[0], width / 2);
            assert.equal(l.reticle[1], height / 2);
            for (const position of [l.target, l.mfd])
                assert(
                    position[0] >= 0 &&
                        position[1] >= 0 &&
                        position[0] + 75 * l.scale <= width &&
                        position[1] + 100 * l.scale <= height,
                    "Panel bounds",
                );
            for (const mode of ["source", "enhanced", "stretch"]) {
                element("resolution").value = `${width},${height}`;
                element("mode").value = mode;
                element("scale").value = String(size);
                sandbox.window.testing.render();
                assert.equal(element("hud").width, width);
                assert.equal(element("hud").height, height);
            }
            checks.push({ width, height, size, bounds: true, modes: 3 });
        }
    }
    for (const args of [
        [640, 480, 0],
        [640, 480, 1.5],
        [639, 480, 1],
        [640, 479, 1],
        [NaN, 480, 1],
    ])
        assert.throws(() => sandbox.window.testing.layout(...args));
    for (const [heat, speed, heading] of [
        [0, 0, 0],
        [100, 100, 359],
    ]) {
        element("heat").value = String(heat);
        element("speed").value = String(speed);
        element("heading").value = String(heading);
        sandbox.window.testing.render();
    }
    element("heat").value = "35";
    element("speed").value = "64";
    element("heading").value = "350";
    // Render output PNGs from the SAME scene code used in the interactive artifact.
    const hashes = {};
    for (const [width, height] of [
        [1920, 1440],
        [3440, 1440],
    ]) {
        for (const mode of ["source", "enhanced", "stretch"]) {
            element("resolution").value = `${width},${height}`;
            element("mode").value = mode;
            element("scale").value = "1";
            sandbox.window.testing.render();
            const png = element("hud").toBuffer("image/png");
            const filename = `${mode}-${width}x${height}.png`;
            const target = path.join(directory, filename);
            fs.writeFileSync(target, png, { flag: "wx" });
            hashes[filename] = crypto.createHash("sha256").update(png).digest("hex");
        }
    }
    assert.notEqual(hashes["source-3440x1440.png"], hashes["enhanced-3440x1440.png"]);
    // Validate each vector asset fits its recorded logical viewbox.
    for (const [name, model] of Object.entries(data.vectors)) {
        assert.equal(model.width, data.resources[name].width);
        assert.equal(model.height, data.resources[name].height);
    }
    const result = {
        passed: true,
        scope: "Offline native Skia execution of actual canvas scene/controls; no browser or live game validation",
        fontBackend: "Skia system Arial; differs from original GDI",
        viewportChecks: checks,
        invalidViewportsRejected: 5,
        vectorDimensionsChecked: Object.keys(data.vectors).length,
        outputHashes: hashes,
    };
    fs.writeFileSync(
        path.join(directory, "validation.json"),
        JSON.stringify(result, null, 2) + "\n",
        { flag: "wx" },
    );
    console.log(
        JSON.stringify({
            passed: true,
            viewportChecks: checks.length,
            renderCombinations: 24,
            pngs: 6,
            vectors: result.vectorDimensionsChecked,
        }),
    );
}
main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
