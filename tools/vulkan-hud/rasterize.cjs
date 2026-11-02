// Private v3 vectors become padded straight-alpha RGBA textures, never guest sizes.
const fs = require("node:fs"),
    path = require("node:path"),
    vm = require("node:vm");
const crypto = require("node:crypto");
const [components, requestFile, output, canvasPackage] = process.argv.slice(2);
const native = require(canvasPackage),
    data = JSON.parse(fs.readFileSync(components, "utf8"));
if (!native.GlobalFonts.has("Arial"))
    throw Error("Arial unavailable; explicit font resolution required");
const renderer = fs.readFileSync(path.join(__dirname, "../hud-prototype/renderer.js"), "utf8");
const sandbox = { HUD_DATA: data, document: {}, window: {} };
vm.createContext(sandbox);
vm.runInContext(
    renderer.slice(0, renderer.indexOf("function sprite(")) + "\nwindow.vector=vector;",
    sandbox,
);
const request = JSON.parse(fs.readFileSync(requestFile, "utf8")),
    textures = [];
(async () => {
    for (const [index, item] of request.entries.entries()) {
        let width,
            height,
            advance = null;
        if (item.text !== undefined) {
            if (item.observed) {
                width = item.observed.logicalWidth;
                height = item.observed.logicalHeight;
                advance = null;
            } else {
                const font = data.fonts[item.fontId];
                if (!font || font.face[0] !== "Arial" || font.height[0] !== -10)
                    throw Error("Unrecovered font measurement contract");
                const measure = native.createCanvas(1, 1).getContext("2d");
                measure.font = "10px Arial";
                advance = measure.measureText(item.text).width;
                width = Math.ceil(advance) + 2;
                height = 14;
            }
        } else {
            const model = item.useBitmap
                ? data.resources[item.componentId]
                : (data.vectors[item.componentId] ?? data.resources[item.componentId]);
            if (!model) throw Error("Unknown component");
            const logicalScale = item.logicalScale ?? 1;
            if (!(logicalScale > 0 && logicalScale <= 1))
                throw Error("Invalid component logical scale");
            width = model.width * logicalScale;
            height = model.height * logicalScale;
        }
        const density = request.density,
            padding = 2;
        const physicalWidth = Math.ceil(width * density) + 2 * padding,
            physicalHeight = Math.ceil(height * density) + 2 * padding;
        const canvas = native.createCanvas(physicalWidth, physicalHeight),
            ctx = canvas.getContext("2d");
        if (item.observed) {
            // LOGFONT FW_DONTCARE (0) requests normal weight; CSS does not accept 0.
            const o = item.observed,
                weight = o.fontWeight === 0 ? 400 : o.fontWeight;
            ctx.font = `${weight} ${Math.abs(o.fontHeight) * density}px Arial`;
            ctx.fillStyle = `rgb(${o.textColor & 255},${(o.textColor >> 8) & 255},${(o.textColor >> 16) & 255})`;
            // Output-density coverage; original GDI baseline/line metrics remain unproven.
            item.text
                .split("\n")
                .forEach((line, i) =>
                    ctx.fillText(
                        line,
                        padding,
                        padding + (Math.abs(o.fontHeight) + i * o.logicalLineHeight) * density,
                    ),
                );
        } else if (item.text !== undefined) {
            ctx.font = `${10 * density}px Arial`;
            ctx.fillStyle = "#00eb00";
            ctx.fillText(item.text, padding, padding + 10 * density);
        } else if (item.useBitmap || !data.vectors[item.componentId]) {
            const bitmap = await native.loadImage(data.resources[item.componentId].source);
            ctx.drawImage(bitmap, padding, padding, width * density, height * density);
        } else {
            const original = data.vectors[item.componentId];
            if (item.vectorColor) {
                if (!/^#[0-9a-f]{6}$/i.test(item.vectorColor))
                    throw Error("Invalid vector color override");
                data.vectors[item.componentId] = {
                    ...original,
                    shapes: original.shapes.map((shape) => ({ ...shape, color: item.vectorColor })),
                };
            }
            try {
                sandbox.window.vector(
                    ctx,
                    item.componentId,
                    padding,
                    padding,
                    density * (item.logicalScale ?? 1),
                );
            } finally {
                data.vectors[item.componentId] = original;
            }
        }
        const bytes = Buffer.from(ctx.getImageData(0, 0, physicalWidth, physicalHeight).data);
        const file = `texture-${index}.rgba`;
        fs.writeFileSync(path.join(output, file), bytes);
        textures.push({
            componentId: item.componentId ?? null,
            fontId: item.fontId ?? null,
            text: item.text ?? null,
            logicalWidth: width,
            logicalHeight: height,
            logicalAdvance: advance,
            logicalBaseline: item.observed
                ? Math.abs(item.observed.fontHeight)
                : item.text !== undefined
                  ? 10
                  : null,
            physicalWidth,
            physicalHeight,
            density,
            padding,
            file,
            sha256: crypto.createHash("sha256").update(bytes).digest("hex"),
        });
    }
    fs.writeFileSync(
        path.join(output, "textures.json"),
        JSON.stringify(
            {
                alpha: "straight",
                colorSpace: "encoded RGB in UNORM; no sRGB conversion",
                font: "system Arial; original GDI metrics unproven",
                textures,
            },
            null,
            2,
        ),
    );
})().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
