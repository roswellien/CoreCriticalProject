const MAX_REQUEST_BYTES = 256 * 1024;
const MAX_ISSUE_BODY_CHARS = 48_000;

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

function validateEnvironment(env) {
  const repository = env.CRASH_REPORT_REPOSITORY;
  const projectId = env.CRASH_REPORT_PROJECT_ID;
  const token = env.GITHUB_TOKEN;
  if (!repository || !/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(repository) ||
      !projectId || !/^PVT_/.test(projectId) || !token) {
    throw new Error("Crash reporting is not configured on the server.");
  }
  return { owner: repository.split("/")[0], name: repository.split("/")[1], projectId, token };
}

function validateReport(report) {
  if (!report || report.format_version !== 1 || typeof report.failure_summary !== "string" ||
      report.failure_summary.trim().length === 0 || report.failure_summary.length > 2000 ||
      !report.logs || typeof report.logs !== "object" || Array.isArray(report.logs)) {
    throw new Error("The crash report format is invalid.");
  }

  const settings = {};
  for (const key of ["EngineMode", "WindowMode", "AntiAliasing"]) {
    if (typeof report.settings?.[key] === "string") settings[key] = report.settings[key].slice(0, 80);
  }
  for (const key of ["Width", "Height", "AnisotropicFiltering", "DrawDistance", "FogDistance"]) {
    if (Number.isInteger(report.settings?.[key])) settings[key] = report.settings[key];
  }
  for (const key of ["LocalCdAudio", "InstantReplay", "PerformanceMonitor"]) {
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
  return {
    format_version: 1,
    report_id: typeof report.report_id === "string" ? report.report_id.slice(0, 64) : "",
    created_utc: typeof report.created_utc === "string" ? report.created_utc.slice(0, 40) : "",
    launcher_version: typeof report.launcher_version === "string" ? report.launcher_version.slice(0, 80) : "",
    os: typeof report.os === "string" ? report.os.slice(0, 200) : "",
    architecture: typeof report.architecture === "string" ? report.architecture.slice(0, 80) : "",
    dotnet_runtime: typeof report.dotnet_runtime === "string" ? report.dotnet_runtime.slice(0, 120) : "",
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

async function fingerprint(reason) {
  const bytes = new TextEncoder().encode(normalizeReason(reason));
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map(value => value.toString(16).padStart(2, "0")).join("");
}

async function github(env, token, query, variables) {
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

function issueBody(report, crashFingerprint) {
  const marker = `<!-- crash-fingerprint:${crashFingerprint} -->`;
  const reportText = JSON.stringify(report, null, 2).replace(/```/g, "\\u0060\\u0060\\u0060");
  const boundedReport = reportText.length > MAX_ISSUE_BODY_CHARS
    ? reportText.slice(0, MAX_ISSUE_BODY_CHARS) + "\n[Report truncated to fit GitHub issue limits.]"
    : reportText;
  return `${marker}\n\nCrash report sent with the player's report setting or one-time approval.\n\n` +
    "```json\n" + boundedReport + "\n```";
}

async function addToProject(env, token, projectId, issueId) {
  try {
    await github(env, token, `mutation($project:ID!, $issue:ID!) {
      addProjectV2ItemById(input:{projectId:$project, contentId:$issue}) { item { id } }
    }`, { project: projectId, issue: issueId });
  } catch (error) {
    // GitHub reports a GraphQL error when a retry adds an item already on the board.
    if (!/already exists|already added|duplicate/i.test(error.message)) throw error;
  }
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
    const crashFingerprint = await fingerprint(report.failure_summary);
    const marker = `crash-fingerprint:${crashFingerprint}`;
    const query = `repo:${config.owner}/${config.name} is:issue in:body "${marker}"`;
    const data = await github(env, config.token, `query($query:String!) {
      repository(owner:"${config.owner}", name:"${config.name}") { id }
      search(query:$query, type:ISSUE, first:10) {
        nodes { ... on Issue { id url title body } }
      }
    }`, { query });
    if (!data.repository) return json({ error: "The configured GitHub repository was not found." }, 503);

    const existing = data.search.nodes.find(issue => issue.body?.includes(marker));
    const body = issueBody(report, crashFingerprint);
    let issue;
    if (existing) {
      const comment = await github(env, config.token, `mutation($issue:ID!, $body:String!) {
        addComment(input:{subjectId:$issue, body:$body}) { commentEdge { node { id } } }
      }`, { issue: existing.id, body: "A further report matched this crash signature.\n\n" + body });
      issue = existing;
      if (!comment) return json({ error: "GitHub did not accept the report update." }, 502);
    } else {
      const titleReason = report.failure_summary.replace(/[\r\n\t]+/g, " ").trim().slice(0, 140);
      const created = await github(env, config.token, `mutation($repository:ID!, $title:String!, $body:String!) {
        createIssue(input:{repositoryId:$repository, title:$title, body:$body}) {
          issue { id url title }
        }
      }`, { repository: data.repository.id,
        title: `Crash: ${titleReason} [${crashFingerprint.slice(0, 12)}]`, body });
      issue = created.createIssue.issue;
    }

    await addToProject(env, config.token, config.projectId, issue.id);
    return json({ issue_url: issue.url, duplicate: Boolean(existing) });
  } catch (error) {
    // Keep GitHub details in server logs only; never echo secrets or remote responses to the launcher.
    console.error("Crash report delivery failed:", error.message);
    return json({ error: "The report service could not save this crash report. Try again later." }, 502);
  }
}
