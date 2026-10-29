import { authorizeCrashReportAdmin } from "../_lib/crash-report-admin-auth.js";

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
    .muted{color:var(--muted)}.top{display:flex;justify-content:space-between;align-items:center;gap:18px;flex-wrap:wrap;border-bottom:1px solid var(--line);padding-bottom:22px}
    a{color:var(--amber)}.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:18px;margin:16px 0}
    table{width:100%;border-collapse:collapse}th,td{text-align:left;vertical-align:top;border-bottom:1px solid var(--line);padding:12px 10px}th{color:var(--muted);font-size:.85rem;text-transform:uppercase}
    .failure{max-width:600px;overflow-wrap:anywhere}.tag{color:var(--amber);white-space:nowrap}.details{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
    .details div{background:var(--panel);border:1px solid var(--line);padding:12px;border-radius:8px}.details strong{display:block;color:var(--muted);font-size:.83rem}
    pre{white-space:pre-wrap;overflow-wrap:anywhere;overflow:auto;max-height:75vh;background:#0b0e0d;border:1px solid var(--line);border-radius:8px;padding:16px;font:13px/1.5 ui-monospace,Consolas,monospace}
    .log{border-left:3px solid var(--amber)}.error{color:var(--red)}
    @media(max-width:700px){main{padding:24px 12px 48px}table,tbody,tr,td{display:block}thead{display:none}td{border:0;padding:5px 10px}.card{padding:12px}}
  </style></head><body><main>${content}</main></body></html>`,
        { status, headers: PAGE_HEADERS },
    );
}

function failurePage(status, message) {
    return page(`<h1>Crash report archive</h1><p class="error">${escapeHtml(message)}</p>`, status);
}

function listPage(reports) {
    const rows = reports
        .map(
            (report) => `<tr>
    <td><a href="/admin/crash-reports?id=${encodeURIComponent(report.report_id)}">${escapeHtml(report.report_id)}</a></td>
    <td>${escapeHtml(report.created_utc || report.stored_utc)}</td>
    <td><span class="tag">${escapeHtml(report.mode)}</span><br>Exit ${escapeHtml(report.exit_code)}</td>
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

function detailPage(row) {
    let report;
    try {
        report = JSON.parse(row.report_json);
    } catch {
        return failurePage(500, "The archived report could not be read.");
    }
    const { logs = {}, ...details } = report;
    const logLabels = {
        launcher: "Launcher log",
        native_stderr: "Native standard error",
        native_stdout: "Native standard output",
    };
    const logSections = Object.entries(logs)
        .map(
            ([name, text]) =>
                `<section><h3>${escapeHtml(logLabels[name] ?? name)}</h3><pre class="log">${escapeHtml(text)}</pre></section>`,
        )
        .join("");
    return page(`<header class="top"><div><h1>Crash report</h1><p class="muted">ID ${escapeHtml(row.report_id)}</p></div><a href="/admin/crash-reports">← All reports</a></header>
    <section class="details card">
      <div><strong>Reported</strong>${escapeHtml(row.created_utc || "Unknown")}</div>
      <div><strong>Archived</strong>${escapeHtml(row.stored_utc)}</div>
      <div><strong>Engine mode</strong>${escapeHtml(row.mode)}</div>
      <div><strong>Exit code</strong>${escapeHtml(row.exit_code)}</div>
      <div><strong>Failure fingerprint</strong>${escapeHtml(row.crash_fingerprint || "Not grouped")}</div>
    </section>
    <h2>Report details</h2><pre>${escapeHtml(JSON.stringify(details, null, 2))}</pre>
    <h2>Recent log excerpts</h2>${logSections || `<p class="muted">No log files were included.</p>`}`);
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
                `
        SELECT report_id, created_utc, stored_utc, mode, exit_code, failure_summary, crash_fingerprint, report_json
        FROM crash_report_archive WHERE report_id = ?
      `,
            )
                .bind(reportId)
                .first();
            return report ? detailPage(report) : failurePage(404, "Report not found.");
        }
        const reports = await env.CRASH_REPORT_DB.prepare(
            `
      SELECT report_id, created_utc, stored_utc, mode, exit_code, failure_summary
      FROM crash_report_archive ORDER BY stored_utc DESC LIMIT 100
    `,
        ).all();
        return listPage(reports.results ?? []);
    } catch {
        return failurePage(503, "The report archive could not be read.");
    }
}
