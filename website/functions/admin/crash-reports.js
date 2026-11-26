import { authorizeCrashReportAdmin } from "../_lib/crash-report-admin-auth.js";
import { LOG_LABELS, LOG_ORDER } from "../_lib/crash-report-logs.js";

const PAGE_HEADERS = {
    "content-type": "text/html; charset=utf-8",
    "cache-control": "no-store, private",
    "content-security-policy":
        "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; frame-ancestors 'none'",
    "referrer-policy": "no-referrer",
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
};

function escapeHtml(value) {
    return String(value ?? "").replace(
        /[&<>"']/g,
        (character) =>
            ({
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#39;",
            })[character],
    );
}

function page(content, status = 200) {
    return new Response(
        `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Crash report archive · Core Critical</title><style>
        :root{color-scheme:dark;--bg:#101312;--panel:#191e1c;--line:#39413d;--text:#edf0ed;--muted:#aeb7b1;--amber:#f3a43b;--red:#f18b72}
        *{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:16px/1.55 system-ui,Segoe UI,sans-serif}
        main{max-width:1120px;margin:auto;padding:36px 24px 72px}h1,h2,h3{line-height:1.2}h1{font-size:clamp(1.8rem,4vw,2.7rem);margin:0 0 8px}h2{margin-top:32px}h3{color:var(--amber);margin:22px 0 8px}
        a{color:var(--amber)}.top{display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:12px}.muted{color:var(--muted)}
        .card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:18px;margin:16px 0}
        table{width:100%;border-collapse:collapse}th,td{text-align:left;vertical-align:top;border-bottom:1px solid var(--line);padding:12px 10px}th{color:var(--muted);font-size:.85rem;text-transform:uppercase}
        .failure{max-width:600px;overflow-wrap:anywhere}.summary-banner{border-left:4px solid var(--red);overflow-wrap:anywhere}.summary-text{font-size:1.08rem;margin:6px 0 0;font-weight:600}
        .tag{color:var(--amber);white-space:nowrap}.code{font-family:ui-monospace,Consolas,monospace;font-size:.92em;color:var(--text)}
        .details{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
        .details div{background:var(--panel);border:1px solid var(--line);padding:12px;border-radius:8px;overflow-wrap:anywhere}.details strong{display:block;color:var(--muted);font-size:.83rem;margin-bottom:2px}
        .stack-list{list-style:none;padding:0;margin:8px 0 0;display:grid;gap:10px}.stack-item{background:#131715;border:1px solid var(--line);border-radius:8px;padding:12px}
        details.pane{background:var(--panel);border:1px solid var(--line);border-radius:10px;margin:14px 0;padding:14px 18px}
        details.pane>summary{cursor:pointer;color:var(--amber);font-weight:600;font-size:1.02rem;list-style:revert}
        pre{white-space:pre-wrap;overflow-wrap:anywhere;overflow:auto;max-height:75vh;background:#0b0e0d;border:1px solid var(--line);border-radius:8px;padding:16px;margin:12px 0 0;font:13px/1.5 ui-monospace,Consolas,monospace}
        .log{border-left:3px solid var(--amber)}.error{color:var(--red)}
        @media(max-width:700px){main{padding:24px 12px 48px}table,tbody,tr,td{display:block}thead{display:none}td{border:0;padding:5px 10px}.card,details.pane{padding:12px}}
      </style></head><body><main>${content}</main></body></html>`,
        { status, headers: PAGE_HEADERS },
    );
}

function failurePage(status, message) {
    return page(`<h1>Crash report archive</h1><p class="error">${escapeHtml(message)}</p>`, status);
}

function readField(source, name) {
    if (!source || typeof source !== "object") return undefined;
    const camel = name[0].toLowerCase() + name.slice(1);
    const snake = name.replace(/([a-z0-9])([A-Z])/g, "$1_$2").toLowerCase();
    return source[name] ?? source[camel] ?? source[snake];
}

function formatExitStatus(exitCode) {
    const number = Number(exitCode);
    if (!Number.isInteger(number)) return String(exitCode ?? "Unknown");
    const unsignedHex = (number >>> 0).toString(16).toUpperCase().padStart(8, "0");
    if (number === -1) return `${number} (0x${unsignedHex} · launcher stage failure)`;
    return `${number} (0x${unsignedHex})`;
}

function formatGiB(bytesValue) {
    const bytes = Number(bytesValue);
    if (!Number.isFinite(bytes) || bytes <= 0) return null;
    const gib = bytes / (1024 * 1024 * 1024);
    const formatted =
        gib >= 10 || Number.isInteger(Math.round(gib * 10) / 10)
            ? gib.toFixed(1).replace(/\.0$/, "")
            : gib.toFixed(2);
    return `${formatted} GiB`;
}

function formatModeLabel(mode) {
    if (mode === "remaster") return "MW3-RE Native (remaster)";
    if (mode === "d7vk") return "Original Mech3 (d7vk)";
    return String(mode || "Unknown");
}

function listPage(reports) {
    const rows = reports
        .map(
            (report) => `<tr>
    <td><a href="/admin/crash-reports?id=${encodeURIComponent(report.report_id)}">${escapeHtml(report.report_id)}</a></td>
    <td>${escapeHtml(report.created_utc || report.stored_utc)}</td>
    <td><span class="tag">${escapeHtml(report.mode)}</span><br><span class="code">Exit ${escapeHtml(formatExitStatus(report.exit_code))}</span></td>
    <td class="failure">${escapeHtml(report.failure_summary)}</td>
  </tr>`,
        )
        .join("");
    return page(`<header class="top"><div><h1>Crash report archive</h1><p class="muted">Admin-only reports · newest 100</p></div></header>
    ${
        reports.length
            ? `<section class="card"><table><thead><tr><th>Report ID</th><th>Reported</th><th>Mode / exit</th><th>Failure summary</th></tr></thead><tbody>${rows}</tbody></table></section>`
            : `<section class="card"><p>No crash reports have been archived.</p></section>`
    }`);
}

const SETTING_LABELS = [
    ["EngineMode", "Engine mode"],
    ["Width", "Resolution width"],
    ["Height", "Resolution height"],
    ["WindowMode", "Window mode"],
    ["AntiAliasing", "Anti-aliasing"],
    ["AnisotropicFiltering", "Anisotropic filtering"],
    ["DrawDistance", "Scenery draw distance"],
    ["FogDistance", "Fog distance"],
    ["RenderThread", "Render thread"],
    ["LocalCdAudio", "Local CD audio"],
    ["InstantReplay", "Instant replay"],
    ["PerformanceMonitor", "Performance monitor"],
    ["D7VkResolution", "D7VK resolution"],
    ["D7VkAntiAliasing", "D7VK anti-aliasing"],
    ["D7VkAnisotropicFiltering", "D7VK anisotropic filtering"],
    ["D7VkAiTextures", "D7VK AI-upscaled textures"],
];

function formatSettingValue(key, value) {
    if (typeof value === "boolean") return value ? "On" : "Off";
    if (key === "AnisotropicFiltering" && Number.isInteger(value)) return `${value}x`;
    if ((key === "DrawDistance" || key === "FogDistance") && Number.isInteger(value))
        return `${value}m`;
    return String(value);
}

function renderHardwareSection(hardware) {
    if (!hardware || typeof hardware !== "object") {
        return `<section class="card"><h2>Hardware inventory</h2><p class="muted">No hardware inventory was recorded in this report.</p></section>`;
    }
    const processors = Array.isArray(readField(hardware, "Processors"))
        ? readField(hardware, "Processors")
        : [];
    const memory = readField(hardware, "Memory");
    const memoryModules =
        memory && typeof memory === "object" && Array.isArray(readField(memory, "Modules"))
            ? readField(memory, "Modules")
            : [];
    const totalMemoryGiB =
        memory && typeof memory === "object" ? formatGiB(readField(memory, "TotalBytes")) : null;
    const adapters = Array.isArray(readField(hardware, "GraphicsAdapters"))
        ? readField(hardware, "GraphicsAdapters")
        : [];

    const cpuItems = processors.length
        ? `<ul class="stack-list">${processors
              .map((cpu) => {
                  const manufacturer = readField(cpu, "Manufacturer");
                  const model = readField(cpu, "Model") || "Unknown processor";
                  const label =
                      manufacturer &&
                      !String(model).toLowerCase().startsWith(String(manufacturer).toLowerCase())
                          ? `${manufacturer} ${model}`
                          : model;
                  const physical = readField(cpu, "PhysicalCores");
                  const logical = readField(cpu, "LogicalProcessors");
                  const coreParts = [];
                  if (Number.isInteger(physical)) coreParts.push(`${physical} physical cores`);
                  if (Number.isInteger(logical)) coreParts.push(`${logical} logical processors`);
                  const coresText = coreParts.length ? ` · ${coreParts.join(", ")}` : "";
                  return `<li class="stack-item"><strong>${escapeHtml(label)}</strong><span>${escapeHtml(coresText ? coresText.slice(3) : "Core count unavailable")}</span></li>`;
              })
              .join("")}</ul>`
        : `<p class="muted">No processor details reported.</p>`;

    const moduleItems = memoryModules.length
        ? `<ul class="stack-list">${memoryModules
              .map((mod) => {
                  const cap = formatGiB(readField(mod, "CapacityBytes")) || "Unknown capacity";
                  const type = readField(mod, "Type") || "Unknown type";
                  const speed = readField(mod, "ConfiguredSpeedMhz");
                  const speedText = Number.isInteger(speed) && speed > 0 ? ` @ ${speed} MHz` : "";
                  return `<li class="stack-item">${escapeHtml(`${cap} · ${type}${speedText}`)}</li>`;
              })
              .join("")}</ul>`
        : `<p class="muted">No memory module details reported.</p>`;

    const gpuItems = adapters.length
        ? `<ul class="stack-list">${adapters
              .map((gpu) => {
                  const name = readField(gpu, "Name") || "Unknown graphics adapter";
                  const vram = formatGiB(readField(gpu, "DedicatedVideoMemoryBytes"));
                  const shared = formatGiB(readField(gpu, "SharedSystemMemoryBytes"));
                  const driver = readField(gpu, "DriverVersion");
                  const driverDate = readField(gpu, "DriverDate");
                  const meta = [];
                  if (vram) meta.push(`VRAM: ${vram}`);
                  if (shared) meta.push(`Shared: ${shared}`);
                  if (driver) meta.push(`Driver: ${driver}`);
                  if (driverDate) meta.push(`Date: ${String(driverDate).slice(0, 10)}`);
                  return `<li class="stack-item"><strong>${escapeHtml(name)}</strong><span>${escapeHtml(meta.length ? meta.join(" · ") : "Adapter details unavailable")}</span></li>`;
              })
              .join("")}</ul>`
        : `<p class="muted">No graphics adapters reported.</p>`;

    return `<section class="card">
      <h2>Hardware inventory</h2>
      <div class="details">
        <div><strong>Processors (${processors.length})</strong>${cpuItems}</div>
        <div><strong>Installed memory${totalMemoryGiB ? ` (${escapeHtml(totalMemoryGiB)} total)` : ""}</strong>${moduleItems}</div>
        <div><strong>Graphics adapters (${adapters.length})</strong>${gpuItems}</div>
      </div>
    </section>`;
}

function renderSettingsSection(settings) {
    if (!settings || typeof settings !== "object" || Array.isArray(settings)) {
        return `<section class="card"><h2>Graphics &amp; engine settings</h2><p class="muted">No settings were recorded in this report.</p></section>`;
    }
    const items = [];
    const seen = new Set();
    const width = readField(settings, "Width");
    const height = readField(settings, "Height");
    if (Number.isInteger(width) && Number.isInteger(height)) {
        items.push(`<div><strong>Resolution</strong>${escapeHtml(`${width} × ${height}`)}</div>`);
        seen.add("Width");
        seen.add("Height");
    }
    for (const [key, label] of SETTING_LABELS) {
        if (seen.has(key)) continue;
        const val = readField(settings, key);
        if (val === undefined || val === null || val === "") continue;
        seen.add(key);
        items.push(
            `<div><strong>${escapeHtml(label)}</strong>${escapeHtml(formatSettingValue(key, val))}</div>`,
        );
    }
    for (const [rawKey, val] of Object.entries(settings)) {
        const matched = SETTING_LABELS.some(
            ([k]) =>
                k.toLowerCase() === rawKey.toLowerCase() ||
                k.replace(/([a-z0-9])([A-Z])/g, "$1_$2").toLowerCase() === rawKey.toLowerCase(),
        );
        if (
            matched ||
            rawKey === "Width" ||
            rawKey === "width" ||
            rawKey === "Height" ||
            rawKey === "height"
        )
            continue;
        if (val === undefined || val === null || val === "") continue;
        items.push(`<div><strong>${escapeHtml(rawKey)}</strong>${escapeHtml(String(val))}</div>`);
    }
    if (items.length === 0) {
        return `<section class="card"><h2>Graphics &amp; engine settings</h2><p class="muted">No settings were recorded in this report.</p></section>`;
    }
    return `<section class="card"><h2>Graphics &amp; engine settings</h2><div class="details">${items.join("")}</div></section>`;
}

function renderPacksSection(packs) {
    if (!Array.isArray(packs) || packs.length === 0) {
        return `<section class="card"><h2>Installed content packs</h2><p class="muted">No content packs were installed or reported.</p></section>`;
    }
    const rows = packs
        .map((pack) => {
            const id = readField(pack, "Id") ?? pack?.id ?? "Unknown";
            const version = readField(pack, "Version") ?? pack?.version ?? "—";
            const schema = readField(pack, "SchemaVersion") ?? pack?.schema_version ?? "—";
            const enabled = (readField(pack, "IsEnabled") ?? pack?.enabled) === true;
            const priority = readField(pack, "Priority") ?? pack?.priority ?? 0;
            return `<tr>
          <td class="code">${escapeHtml(id)}</td>
          <td>${escapeHtml(version)}</td>
          <td><span class="tag">${enabled ? "Enabled" : "Disabled"}</span></td>
          <td>${escapeHtml(priority)}</td>
          <td>v${escapeHtml(schema)}</td>
        </tr>`;
        })
        .join("");
    return `<section class="card">
      <h2>Installed content packs (${packs.length})</h2>
      <table>
        <thead><tr><th>Pack ID</th><th>Version</th><th>Status</th><th>Priority</th><th>Schema</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </section>`;
}

function renderLogsSection(logs) {
    const sourceLogs = logs && typeof logs === "object" && !Array.isArray(logs) ? logs : {};
    const orderedKeys = [
        ...LOG_ORDER.filter(
            (key) => typeof sourceLogs[key] === "string" && sourceLogs[key].length > 0,
        ),
        ...Object.keys(sourceLogs).filter(
            (key) =>
                !LOG_ORDER.includes(key) &&
                typeof sourceLogs[key] === "string" &&
                sourceLogs[key].length > 0,
        ),
    ];
    if (orderedKeys.length === 0) {
        return `<p class="muted">No log files were included.</p>`;
    }
    return orderedKeys
        .map((name, index) => {
            const openAttr = name === "native_crash" || index === 0 ? " open" : "";
            return `<details class="pane"${openAttr}><summary>${escapeHtml(LOG_LABELS[name] ?? name)}</summary><pre class="log">${escapeHtml(sourceLogs[name])}</pre></details>`;
        })
        .join("");
}

function detailPage(row) {
    let report;
    try {
        report = JSON.parse(row.report_json);
    } catch {
        return failurePage(500, "The archived report could not be read.");
    }
    const { logs = {}, ...details } = report;
    const summaryText =
        row.failure_summary || report.failure_summary || "No specific failure was recorded.";
    const modeValue = row.mode || report.mode || "Unknown";
    const exitValue = row.exit_code ?? report.exit_code;
    const launcherVersion = report.launcher_version || "Unknown";
    const runtimeVersion = report.runtime_version || "Unknown";
    const runtimeCommit = report.runtime_source_commit;
    const runtimeDisplay =
        runtimeCommit && !String(runtimeVersion).includes(String(runtimeCommit).slice(0, 7))
            ? `${runtimeVersion} (${runtimeCommit})`
            : runtimeVersion;
    const osValue = report.os || "Unknown";
    const archValue = report.architecture || "Unknown";
    const dotnetValue = report.dotnet_runtime || "Unknown";
    const reportedUtc = row.created_utc || report.created_utc || "Unknown";
    const archivedUtc = row.stored_utc || "Unknown";
    const fingerprintValue = row.crash_fingerprint || "Not grouped";

    return page(`<header class="top"><div><h1>Crash report</h1><p class="muted">ID ${escapeHtml(row.report_id)}</p></div><a href="/admin/crash-reports">← All reports</a></header>
    <section class="card summary-banner">
      <strong>Failure summary</strong>
      <p class="summary-text">${escapeHtml(summaryText)}</p>
    </section>
    <section class="details">
      <div><strong>Exit status</strong><span class="code">${escapeHtml(formatExitStatus(exitValue))}</span></div>
      <div><strong>Engine mode</strong>${escapeHtml(formatModeLabel(modeValue))}</div>
      <div><strong>Launcher version</strong>${escapeHtml(launcherVersion)}</div>
      <div><strong>Runtime version</strong>${escapeHtml(runtimeDisplay)}</div>
      <div><strong>Operating system</strong>${escapeHtml(osValue)}</div>
      <div><strong>Architecture / .NET</strong>${escapeHtml(`${archValue} · ${dotnetValue}`)}</div>
      <div><strong>Reported (UTC)</strong>${escapeHtml(reportedUtc)}</div>
      <div><strong>Archived (UTC)</strong>${escapeHtml(archivedUtc)}</div>
      <div><strong>Failure fingerprint</strong><span class="code">${escapeHtml(fingerprintValue)}</span></div>
    </section>
    ${renderHardwareSection(report.hardware)}
    ${renderSettingsSection(report.settings)}
    ${renderPacksSection(report.packs)}
    <h2>Recent log excerpts</h2>
    ${renderLogsSection(logs)}
    <details class="pane">
      <summary>Raw report metadata (JSON)</summary>
      <pre>${escapeHtml(JSON.stringify(details, null, 2))}</pre>
    </details>`);
}

export async function onRequestGet({ request, env }) {
    const authorization = await authorizeCrashReportAdmin(request, env);
    if (!authorization.ok) return failurePage(authorization.status, authorization.message);
    if (!env.CRASH_REPORT_DB?.prepare)
        return failurePage(503, "The report archive database is unavailable.");
    const reportId = new URL(request.url).searchParams.get("id");
    try {
        if (reportId !== null) {
            if (!/^[a-zA-Z0-9-]{1,64}$/.test(reportId))
                return failurePage(404, "Report not found.");
            const report = await env.CRASH_REPORT_DB.prepare(
                "SELECT report_id, created_utc, stored_utc, mode, exit_code, failure_summary, crash_fingerprint, report_json FROM crash_report_archive WHERE report_id = ?",
            )
                .bind(reportId)
                .first();
            return report ? detailPage(report) : failurePage(404, "Report not found.");
        }
        const reports = await env.CRASH_REPORT_DB.prepare(
            "SELECT report_id, created_utc, stored_utc, mode, exit_code, failure_summary FROM crash_report_archive ORDER BY stored_utc DESC LIMIT 100",
        ).all();
        return listPage(reports.results ?? []);
    } catch {
        return failurePage(503, "The report archive could not be read.");
    }
}
