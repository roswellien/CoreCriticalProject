"use strict";
const $ = (id) => document.getElementById(id);
const FONT = "Arial, sans-serif";
const resourceImages = {};
const telemetry = () => ({
    heat: Number($("heat").value),
    speed: Number($("speed").value),
    heading: Number($("heading").value),
});

// Source 640x480 positions are retained as logical distances from recovered anchors.
function layout(width, height, userScale = 1) {
    if (
        ![width, height, userScale].every(Number.isFinite) ||
        width < 640 ||
        height < 480 ||
        userScale < 0.75 ||
        userScale > 1
    )
        throw Error("Unsupported viewport");
    const scale = Math.min(width / 640, height / 480) * userScale;
    const gauge = HUD_DATA.layouts.V640x480.GAUGES;
    const positions = {};
    for (const [name, pos] of Object.entries(gauge)) {
        const [x, y] = pos;
        positions[name] = [x >= 320 ? width - (640 - x) * scale : x * scale, y * scale];
    }
    return {
        width,
        height,
        scale,
        positions,
        reticle: [width / 2, height / 2],
        weapons: [width - 110 * scale, 30 * scale],
        target: [10 * scale, height - 110 * scale],
        mfd: [width - 110 * scale, height - 110 * scale],
        compass: [width / 2 - 75 * scale, 11 * scale],
    };
}

function vector(ctx, name, x, y, scale) {
    const model = HUD_DATA.vectors[name];
    if (!model) return false;
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(scale, scale);
    for (const shape of model.shapes) {
        ctx.fillStyle = ctx.strokeStyle = shape.color;
        if (shape.kind === "line") {
            ctx.lineWidth = shape.width;
            ctx.beginPath();
            ctx.moveTo(...shape.points.slice(0, 2));
            ctx.lineTo(...shape.points.slice(2));
            ctx.stroke();
        } else if (shape.kind === "polygon") {
            ctx.beginPath();
            ctx.moveTo(...shape.points.slice(0, 2));
            for (let i = 2; i < shape.points.length; i += 2)
                ctx.lineTo(shape.points[i], shape.points[i + 1]);
            ctx.closePath();
            ctx.fill();
        } else if (shape.kind === "rect") ctx.fillRect(shape.x, shape.y, shape.width, shape.height);
        else if (shape.kind === "text") {
            ctx.font = `${shape.size}px ${FONT}`;
            ctx.fillText(shape.value, shape.x, shape.y);
        }
    }
    ctx.restore();
    return true;
}

function sprite(ctx, name, x, y, s, enhanced) {
    if (enhanced && vector(ctx, name, x, y, s)) return;
    const resource = HUD_DATA.resources[name];
    if (!resource) throw Error("Missing " + name);
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(resourceImages[name], x, y, resource.width * s, resource.height * s);
}

function text(ctx, value, x, y, s, enhanced, size = 10, color = "#00eb00") {
    ctx.fillStyle = color;
    if (enhanced) {
        ctx.font = `${size * s}px ${FONT}`;
        ctx.fillText(value, x, y);
        return;
    }
    const small = document.createElement("canvas");
    small.width = 400;
    small.height = 24;
    const low = small.getContext("2d");
    low.font = `${size}px ${FONT}`;
    low.fillStyle = color;
    low.fillText(value, 0, size + 2);
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(small, x, y - (size + 2) * s, 400 * s, 24 * s);
}

function scene(ctx, width, height, mode, userScale, values) {
    const enhanced = mode === "enhanced",
        l = layout(width, height, userScale),
        s = l.scale;
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = "#030907";
    ctx.fillRect(0, 0, width, height);
    // Abstract background, deliberately no invented world scene or game telemetry.
    ctx.strokeStyle = "#13261c";
    ctx.lineWidth = 1;
    for (let y = height * 0.35; y < height; y += height * 0.08) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
    }
    for (let x = -width; x < width * 2; x += width * 0.12) {
        ctx.beginPath();
        ctx.moveTo(width / 2, height * 0.35);
        ctx.lineTo(x, height);
        ctx.stroke();
    }
    const p = l.positions;
    for (const n of ["speed_frame", "fuel_frame", "coolant_frame", "heat_meter"])
        sprite(ctx, "hud_" + n, ...p[n], s, enhanced);
    // The heat fill is a procedural value display, not a rebuilt source texture.
    const [hx, hy] = p.heat_bar,
        filled = (120 * values.heat) / 100;
    const gradient = ctx.createLinearGradient(hx, hy, hx, hy + 120 * s);
    gradient.addColorStop(0, "#f00018");
    gradient.addColorStop(0.45, "#ffc400");
    gradient.addColorStop(0.7, "#00bb00");
    gradient.addColorStop(1, "#0017b0");
    ctx.fillStyle = gradient;
    ctx.fillRect(hx, hy + (120 - filled) * s, 12 * s, filled * s);
    text(ctx, values.heat + "%", ...p.heat_text, s, enhanced);
    text(ctx, String(values.speed) + " KPH", width - 108 * s, 348 * s, s, enhanced);
    const [wx, wy] = l.weapons;
    text(ctx, "WEAPONS", wx, wy, s, enhanced);
    ["PPC", "LRM 20", "MED LASER"].forEach((v, i) => {
        text(ctx, v, wx + 8 * s, wy + (16 + i * 16) * s, s, enhanced);
        sprite(
            ctx,
            i === 0 ? "hud_weapon_select" : "hud_weapon_chain",
            wx,
            wy + (7 + i * 16) * s,
            s,
            enhanced,
        );
    });
    const [cx, cy] = l.compass;
    ctx.save();
    ctx.beginPath();
    ctx.rect(cx, cy, 150 * s, 20 * s);
    ctx.clip();
    for (let i = -3; i <= 3; i++) {
        const angle = (Math.floor(values.heading / 10) * 10 + i * 10 + 360) % 360;
        const x = width / 2 + (i * 30 - (values.heading % 10) * 3) * s;
        text(ctx, angle === 0 ? "N" : String(angle), x - 8 * s, cy + 10 * s, s, enhanced, 8);
        ctx.strokeStyle = "#00bb00";
        ctx.lineWidth = s;
        ctx.beginPath();
        ctx.moveTo(x, cy + 13 * s);
        ctx.lineTo(x, cy + 18 * s);
        ctx.stroke();
    }
    ctx.restore();
    ctx.strokeStyle = "#00bb00";
    ctx.lineWidth = s;
    ctx.beginPath();
    ctx.moveTo(width / 2 - 4 * s, cy + 22 * s);
    ctx.lineTo(width / 2, cy + 18 * s);
    ctx.lineTo(width / 2 + 4 * s, cy + 22 * s);
    ctx.stroke();
    sprite(ctx, "sensor_reticule", l.reticle[0] - 10.5 * s, l.reticle[1] - 10.5 * s, s, enhanced);
    sprite(ctx, "hud_enarrow_left", width - 35 * s, height / 2 - 12.5 * s, s, enhanced);
    sprite(ctx, "hud_allyarrow_right", 21 * s, height / 2 - 12.5 * s, s, enhanced);
    for (const [name, position] of [
        ["TARGET", l.target],
        ["MFD", l.mfd],
    ]) {
        const [x, y] = position;
        ctx.strokeStyle = "#006a28";
        ctx.lineWidth = s;
        ctx.strokeRect(x, y, 75 * s, 100 * s);
        text(ctx, name, x + 4 * s, y + 12 * s, s, enhanced, 8);
        text(ctx, name === "TARGET" ? "MAD CAT" : "NAV 01", x + 4 * s, y + 28 * s, s, enhanced, 8);
        if (name === "MFD") {
            ctx.strokeStyle = "#006a28";
            ctx.beginPath();
            ctx.arc(x + 37.5 * s, y + 64 * s, 25 * s, 0, Math.PI * 2);
            ctx.stroke();
            sprite(ctx, "hud_mech_enemy_sm", x + 43 * s, y + 54 * s, s, enhanced);
            sprite(ctx, "hud_mech_ally_sm", x + 25 * s, y + 68 * s, s, enhanced);
        }
    }
    text(ctx, "SYSTEMS NOMINAL", width / 2 - 60 * s, height - 12 * s, s, enhanced, 10);
    return l;
}

function render() {
    const [width, height] = $("resolution").value.split(",").map(Number),
        mode = $("mode").value,
        userScale = Number($("scale").value);
    const canvas = $("hud");
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d");
    if (mode === "stretch") {
        const low = document.createElement("canvas");
        low.width = 640;
        low.height = 480;
        scene(low.getContext("2d"), 640, 480, "source", userScale, telemetry());
        ctx.imageSmoothingEnabled = false;
        ctx.drawImage(low, 0, 0, width, height);
    } else scene(ctx, width, height, mode, userScale, telemetry());
    const l = layout(width, height, userScale);
    $("surface").classList.toggle("actual", $("preview").value === "actual");
    $("summary").textContent =
        `${width} × ${height} | uniform HUD scale ${l.scale.toFixed(2)}× | reticle ${width / 2}, ${height / 2} | ${mode === "enhanced" ? "fresh font raster + vectors" : mode === "source" ? "enlarged source components" : "nonuniform stretch control"}`;
}

function checks() {
    const results = [];
    for (const [w, h] of [
        [640, 480],
        [1920, 1440],
        [2560, 1440],
        [3440, 1440],
    ]) {
        const a = layout(w, h);
        const g = HUD_DATA.layouts.V640x480.GAUGES;
        if (a.reticle[0] !== w / 2 || a.reticle[1] !== h / 2) throw Error("Reticle drift");
        if (Math.abs((w - a.positions.speed_frame[0]) / a.scale - (640 - g.speed_frame[0])) > 1e-8)
            throw Error("Right anchor drift");
        if (Math.abs(a.positions.heat_meter[0] / a.scale - g.heat_meter[0]) > 1e-8)
            throw Error("Left anchor drift");
        if (Math.abs((h - a.target[1]) / a.scale - 110) > 1e-8) throw Error("Bottom anchor drift");
        for (const name of ["hud_speed_frame", "hud_heat_meter", "sensor_reticule"]) {
            const m = HUD_DATA.vectors[name],
                r = HUD_DATA.resources[name];
            if (m.width !== r.width || m.height !== r.height) throw Error("Dimension mismatch");
        }
        results.push(`${w}×${h}: center, anchors, dimensions passed`);
    }
    for (const args of [
        [0, 480, 1],
        [640, 0, 1],
        [640, 480, NaN],
    ]) {
        let rejected = false;
        try {
            layout(...args);
        } catch {
            rejected = true;
        }
        if (!rejected) throw Error("Invalid viewport accepted");
    }
    window.hudChecks = { passed: true, results, invalidViewportsRejected: 3 };
    $("checks").textContent = "Layout checks passed at all four output sizes.";
}

async function start() {
    await Promise.all(
        Object.entries(HUD_DATA.resources).map(async ([name, r]) => {
            const im = new Image();
            im.src = r.source;
            await im.decode();
            resourceImages[name] = im;
        }),
    );
    await document.fonts.load(`30px Arial`);
    for (const name of [
        "hud_speed_frame",
        "hud_altitude_frame",
        "hud_fuel_frame",
        "hud_heat_meter",
        "hud_allyarrow_down",
        "sensor_reticule",
    ]) {
        const r = HUD_DATA.resources[name],
            card = document.createElement("div");
        card.className = "card";
        const label = document.createElement("h3");
        label.textContent = `${name} · ${r.width} × ${r.height} logical pixels`;
        card.append(label);
        const cv = document.createElement("canvas");
        cv.width = Math.max(340, r.width * 14 + 30);
        cv.height = Math.max(110, r.height * 6 + 20);
        const c = cv.getContext("2d");
        sprite(c, name, 8, 10, 6, false);
        sprite(c, name, cv.width / 2 + 10, 10, 6, true);
        card.append(cv);
        $("gallery").append(card);
    }
    for (const id of ["resolution", "mode", "scale", "heat", "speed", "heading", "preview"])
        $(id).addEventListener("input", render);
    $("export").addEventListener("click", () => {
        const link = document.createElement("a");
        link.download = `mw3-hud-${$("mode").value}-${$("hud").width}x${$("hud").height}.png`;
        link.href = $("hud").toDataURL("image/png");
        link.click();
    });
    checks();
    render();
    window.hudReady = true;
}
start().catch((error) => {
    $("summary").textContent = "Prototype error: " + error.message;
    window.hudError = error.message;
});
