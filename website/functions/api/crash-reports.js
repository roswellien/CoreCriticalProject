const MAX_REQUEST_BYTES = 256 * 1024;
const MAX_ISSUE_BODY_CHARS = 48_000;
const MAX_FULL_LOG_REPEATS = 3;
const DEFAULT_DAILY_ISSUE_LIMIT = 20;
const GENERIC_FAILURES = [
  "The launch or game ended unexpectedly. Open Logs for details.",
  "No launch details were recorded."
];

function redactPaths(value) {
  return value
    .replace(/\b[A-Za-z]:[\\/][^\r\n\t"<>|]*/g, "<local-path>")
    .replace(/\\\\[^\s"<>|]+/g, "<network-path>");
}

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" }
  });
}

function boundedText(value, maxLength) {
  return typeof value === "string" ? redactPaths(value.slice(0, maxLength)) : null;
}

function boundedCount(value) {
  return Number.isSafeInteger(value) && value >= 0 && value <= 1_000_000 ? value : null;
}

function boundedBytes(value) {
  return Number.isSafeInteger(value) && value >= 0 ? value : null;
}

function validateHardware(hardware) {
  const source = hardware && typeof hardware === "object" && !Array.isArray(hardware) ? hardware : {};
  const processors = Array.isArray(source.Processors) ? source.Processors.slice(0, 8).map(processor => ({
    Manufacturer: boundedText(processor?.Manufacturer, 120),
    Model: boundedText(processor?.Model, 200),
    PhysicalCores: boundedCount(processor?.PhysicalCores),
    LogicalProcessors: boundedCount(processor?.LogicalProcessors)
  })) : [];
  const sourceMemory = source.Memory && typeof source.Memory === "object" && !Array.isArray(source.Memory)
    ? source.Memory : {};
  const modules = Array.isArray(sourceMemory.Modules) ? sourceMemory.Modules.slice(0, 32).map(module => ({
    CapacityBytes: boundedBytes(module?.CapacityBytes),
    Type: boundedText(module?.Type, 80),
    ConfiguredSpeedMhz: boundedCount(module?.ConfiguredSpeedMhz)
  })) : [];
  const graphicsAdapters = Array.isArray(source.GraphicsAdapters) ? source.GraphicsAdapters.slice(0, 8).map(adapter => ({
    Name: boundedText(adapter?.Name, 200) ?? "Unknown graphics adapter",
    DedicatedVideoMemoryBytes: boundedBytes(adapter?.DedicatedVideoMemoryBytes),
    SharedSystemMemoryBytes: boundedBytes(adapter?.SharedSystemMemoryBytes),
    DriverVersion: boundedText(adapter?.DriverVersion, 120),
    DriverDate: boundedText(adapter?.DriverDate, 40)
  })) : [];

  return {
    Processors: processors,
    Memory: {
      TotalBytes: boundedBytes(sourceMemory.TotalBytes),
      Modules: modules
    },
    GraphicsAdapters: graphicsAdapters
  };
}

function validateEnvironment(env) {
  const repository = env.CRASH_REPORT_REPOSITORY;
  const token = env.GITHUB_TOKEN;
  const overflowIssueNumber = Number(env.CRASH_REPORT_OVERFLOW_ISSUE_NUMBER);
  const configuredLimit = Number(env.CRASH_REPORT_DAILY_ISSUE_LIMIT || DEFAULT_DAILY_ISSUE_LIMIT);
  if (!repository || !/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(repository) ||
      !token ||
      !Number.isSafeInteger(overflowIssueNumber) || overflowIssueNumber < 1 ||
      !Number.isSafeInteger(configuredLimit) || configuredLimit < 1 || configuredLimit > 1000 ||
      !env.CRASH_REPORT_DB?.prepare) {
    throw new Error("Crash reporting is not configured on the server.");
  }
  return {
    owner: repository.split("/")[0],
    name: repository.split("/")[1],
    token,
    overflowIssueNumber,
    dailyIssueLimit: configuredLimit,
    database: env.CRASH_REPORT_DB
  };
}

function validateReport(report) {
  if (!report || report.format_version !== 1 || typeof report.failure_summary !== "string" ||
      report.failure_summary.trim().length === 0 || report.failure_summary.length > 2000 ||
      typeof report.mode !== "string" || report.mode.trim().length === 0 || report.mode.length > 80 ||
      !Number.isInteger(report.exit_code) || report.exit_code === 0 || report.exit_code < -255 || report.exit_code > 255 ||
      !report.logs || typeof report.logs !== "object" || Array.isArray(report.logs)) {
    throw new Error("The crash report format is invalid.");
  }

  const settings = {};
  for (const key of ["EngineMode", "WindowMode", "AntiAliasing", "D7VkResolution",
    "D7VkAntiAliasing", "D7VkAnisotropicFiltering"]) {
    if (typeof report.settings?.[key] === "string") settings[key] = report.settings[key].slice(0, 80);
  }
  for (const key of ["Width", "Height", "AnisotropicFiltering", "DrawDistance", "FogDistance"]) {
    if (Number.isInteger(report.settings?.[key])) settings[key] = report.settings[key];
  }
  for (const key of ["LocalCdAudio", "InstantReplay", "PerformanceMonitor", "D7VkAiTextures"]) {
    if (typeof report.settings?.[key] === "boolean") settings[key] = report.settings[key];
  }

  const logs = {};
  for (const name of ["launcher", "native_stderr", "native_stdout"]) {
    const value = report.logs[name];
    if (value !== undefined && typeof value !== "string") throw new Error("The crash report logs are invalid.");
    if (value) logs[name] = redactPaths(value.slice(-64 * 1024));
  }
  const packs = Array.isArray(report.packs) ? report.packs.slice(0, 64).map(pack => ({
    id: typeof pack?.Id === "string" ? redactPaths(pack.Id.slice(0, 120)) : "",
    version: typeof pack?.Version === "string" ? pack.Version.slice(0, 80) : "",
    schema_version: Number.isInteger(pack?.SchemaVersion) ? pack.SchemaVersion : 0,
    enabled: pack?.IsEnabled === true,
    priority: Number.isInteger(pack?.Priority) ? pack.Priority : 0
  })) : [];
  const reportId = typeof report.report_id === "string" && /^[a-zA-Z0-9-]{1,64}$/.test(report.report_id)
    ? report.report_id
    : crypto.randomUUID();
  return {
    format_version: 1,
    report_id: reportId,
    created_utc: typeof report.created_utc === "string" ? report.created_utc.slice(0, 40) : "",
    launcher_version: typeof report.launcher_version === "string" ? report.launcher_version.slice(0, 80) : "",
    runtime_version: typeof report.runtime_version === "string" ? report.runtime_version.slice(0, 80) : "",
    mode: redactPaths(report.mode.slice(0, 80)),
    exit_code: report.exit_code,
    os: typeof report.os === "string" ? report.os.slice(0, 200) : "",
    architecture: typeof report.architecture === "string" ? report.architecture.slice(0, 80) : "",
    dotnet_runtime: typeof report.dotnet_runtime === "string" ? report.dotnet_runtime.slice(0, 120) : "",
    hardware: validateHardware(report.hardware),
    failure_summary: redactPaths(report.failure_summary.slice(0, 2000)),
    settings,
    packs,
    logs
  };
}

function normalizeReason(reason) {
  return reason.toLowerCase()
    .replace(/0x[0-9a-f]+/gi, "<address>")
    .replace(/\s+/g, " ")
    .trim();
}

function isGenericFailure(report) {
  const message = normalizeReason(report.failure_summary).replace(/[.!?]+$/, "");
  return GENERIC_FAILURES.some(summary => message === normalizeReason(summary).replace(/[.!?]+$/, ""));
}

async function fingerprint(report) {
  const signature = JSON.stringify([
    normalizeReason(report.mode), report.exit_code, normalizeReason(report.failure_summary)
  ]);
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(signature));
  return [...new Uint8Array(digest)].map(value => value.toString(16).padStart(2, "0")).join("");
}

async function github(token, query, variables) {
  const response = await fetch("https://api.github.com/graphql", {
    method: "POST",
    headers: {
      "authorization": `Bearer ${token}`,
      "content-type": "application/json",
      "user-agent": "Core-Critical-Crash-Report-Service",
      "x-github-api-version": "2022-11-28"
    },
    body: JSON.stringify({ query, variables })
  });
  const body = await response.json();
  if (!response.ok || body.errors?.length) {
    const detail = body.errors?.map(error => error.message).join("; ") || `GitHub returned HTTP ${response.status}.`;
    throw new Error(detail);
  }
  return body.data;
}

function issueBody(report, crashFingerprint, { includeLogs = true, overflow = false } = {}) {
  const marker = crashFingerprint ? `<!-- crash-fingerprint:${crashFingerprint} -->\n\n` : "";
  const reportLogs = includeLogs ? report.logs : {};
  const safeReport = { ...report, logs: {} };
  const reportText = JSON.stringify(safeReport, null, 2).replace(/```/g, "\\u0060\\u0060\\u0060");
  const note = overflow
    ? "Daily new-issue limit reached. This report is in the overflow queue."
    : "Crash report sent with the player's report setting or one-time approval.";
  const header = `${marker}${note}\nReport ID: ${report.report_id}\n\n### Report details\n\n\`\`\`json\n${reportText}\n\`\`\``;
  if (!includeLogs) return `${header}\n\nLog excerpts omitted for overflow or repeat-report limits.`;

  const logNames = { launcher: "Launcher log", native_stderr: "Native standard error", native_stdout: "Native standard output" };
  const entries = Object.entries(reportLogs).filter(([, content]) => typeof content === "string" && content.length > 0);
  let body = `${header}\n\n### Recent log excerpts\n\n`;
  for (let index = 0; index < entries.length; index++) {
    const [name, content] = entries[index];
    const remainingEntries = entries.length - index;
    const heading = `#### ${logNames[name] ?? name}\n\n`;
    const maxFenceRun = Math.max(0, ...Array.from(content.matchAll(/`+/g), match => match[0].length));
    const fence = "`".repeat(Math.max(3, maxFenceRun + 1));
    const remaining = MAX_ISSUE_BODY_CHARS - body.length - heading.length - fence.length * 2 - 10;
    const perLogBudget = Math.floor(remaining / remainingEntries);
    if (perLogBudget < 128) {
      body += "Additional log excerpts omitted to fit GitHub's issue size limit.\n";
      break;
    }

    const truncationNote = content.length > perLogBudget ? "[Earlier log lines omitted to fit GitHub's issue size limit.]\n" : "";
    const available = Math.max(0, perLogBudget - truncationNote.length);
    let excerpt = content;
    if (excerpt.length > available) {
      excerpt = excerpt.slice(-available);
      const firstNewline = excerpt.indexOf("\n");
      if (firstNewline >= 0) excerpt = excerpt.slice(firstNewline + 1);
    }
    body += `${heading}${fence}text\n${truncationNote}${excerpt.trimEnd()}\n${fence}\n\n`;
  }
  return body.length > MAX_ISSUE_BODY_CHARS ? body.slice(0, MAX_ISSUE_BODY_CHARS) : body;
}

async function reopenIfClosed(token, issue) {
  if (issue.state !== "CLOSED") return;
  await github(token, `mutation($issue:ID!) {
    updateIssue(input:{id:$issue, state:OPEN}) { issue { id state } }
  }`, { issue: issue.id });
}

async function addReportComment(token, issue, report, crashFingerprint,
  { includeLogs = true, overflow = false } = {}) {
  await reopenIfClosed(token, issue);
  await github(token, `mutation($issue:ID!, $body:String!) {
    addComment(input:{subjectId:$issue, body:$body}) { commentEdge { node { id } } }
  }`, {
    issue: issue.id,
    body: issueBody(report, crashFingerprint, { includeLogs, overflow })
  });
}

async function reserveDailyIssueSlot(config) {
  const day = new Date().toISOString().slice(0, 10);
  const row = await config.database.prepare(`
    INSERT INTO crash_issue_daily_limits (utc_day, issue_count)
    VALUES (?, 1)
    ON CONFLICT(utc_day) DO UPDATE SET issue_count = issue_count + 1
      WHERE issue_count < ?
    RETURNING issue_count
  `).bind(day, config.dailyIssueLimit).first();
  return row !== null;
}

async function fetchOverflowIssue(token, owner, name, number) {
  const data = await github(token, `query($owner:String!, $name:String!, $number:Int!) {
    repository(owner:$owner, name:$name) { issue(number:$number) { id url state } }
  }`, { owner, name, number });
  return data.repository?.issue ?? null;
}

export async function onRequestPost({ request, env }) {
  if (Number(request.headers.get("content-length") || 0) > MAX_REQUEST_BYTES) {
    return json({ error: "Crash report is too large." }, 413);
  }

  let raw;
  try {
    raw = await request.text();
    if (new TextEncoder().encode(raw).length > MAX_REQUEST_BYTES) return json({ error: "Crash report is too large." }, 413);
  } catch {
    return json({ error: "Crash report could not be read." }, 400);
  }

  let report;
  try {
    report = validateReport(JSON.parse(raw));
  } catch (error) {
    return json({ error: error.message }, 400);
  }

  let config;
  try {
    config = validateEnvironment(env);
  } catch (error) {
    return json({ error: error.message }, 503);
  }

  try {
    const generic = isGenericFailure(report);
    const crashFingerprint = generic ? null : await fingerprint(report);
    const marker = crashFingerprint ? `crash-fingerprint:${crashFingerprint}` : null;
    const searchQuery = marker ? `repo:${config.owner}/${config.name} is:issue in:body "${marker}"` : null;
    const lookup = await github(config.token, searchQuery
      ? `query($owner:String!, $name:String!, $search:String!) {
          repository(owner:$owner, name:$name) { id isPrivate }
          matched: search(query:$search, type:ISSUE, first:10) {
            nodes { ... on Issue { id url title body state comments { totalCount } } }
          }
        }`
      : `query($owner:String!, $name:String!) {
          repository(owner:$owner, name:$name) { id isPrivate }
        }`,
    searchQuery ? { owner: config.owner, name: config.name, search: searchQuery } : { owner: config.owner, name: config.name });
    if (!lookup.repository?.isPrivate)
      return json({ error: "Crash reports require a configured private GitHub repository." }, 503);

    const existing = marker ? lookup.matched?.nodes.find(issue => issue.body?.includes(marker)) : null;
    if (existing) {
      const includeLogs = (existing.comments?.totalCount ?? 0) < MAX_FULL_LOG_REPEATS;
      await addReportComment(config.token, existing, report, crashFingerprint, { includeLogs });
      return json({ report_id: report.report_id.slice(0, 8), duplicate: true, overflow: false });
    }

    if (!await reserveDailyIssueSlot(config)) {
      const overflow = await fetchOverflowIssue(config.token, config.owner, config.name, config.overflowIssueNumber);
      if (!overflow) return json({ error: "The configured overflow issue was not found." }, 503);
      await addReportComment(config.token, overflow, report, null, { includeLogs: false, overflow: true });
      return json({ report_id: report.report_id.slice(0, 8), duplicate: true, overflow: true });
    }

    const titleReason = report.failure_summary.replace(/[\r\n\t]+/g, " ").trim().slice(0, 120);
    const suffix = crashFingerprint ? ` [${crashFingerprint.slice(0, 12)}]` : ` [${report.report_id.slice(0, 8)}]`;
    const title = `Crash (${report.mode}, exit ${report.exit_code}): ${titleReason}${suffix}`;
    await github(config.token, `mutation($repository:ID!, $title:String!, $body:String!) {
      createIssue(input:{repositoryId:$repository, title:$title, body:$body}) {
        issue { id url state }
      }
    }`, {
      repository: lookup.repository.id,
      title,
      body: issueBody(report, crashFingerprint)
    });
    return json({ report_id: report.report_id.slice(0, 8), duplicate: false, overflow: false });
  } catch (error) {
    console.error("Crash report delivery failed:", error.message);
    return json({ error: "The report service could not save this crash report. Try again later." }, 502);
  }
}
