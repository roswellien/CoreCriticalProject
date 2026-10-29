import assert from "node:assert/strict";
import { afterEach, test } from "node:test";
import { onRequestPost } from "../functions/api/crash-reports.js";

const originalFetch = globalThis.fetch;
const database = {
  prepare() {
    return { bind: (_day, limit) => ({ first: async () => limit > 0 ? { issue_count: 1 } : null }) };
  }
};
const environment = {
  CRASH_REPORT_REPOSITORY: "roswellien/corecritical-crash-reports",
  CRASH_REPORT_OVERFLOW_ISSUE_NUMBER: "1",
  CRASH_REPORT_DAILY_ISSUE_LIMIT: "20",
  CRASH_REPORT_DB: database,
  GITHUB_TOKEN: "test-token"
};

afterEach(() => { globalThis.fetch = originalFetch; });

function crashRequest(overrides = {}) {
  return new Request("https://corecritical.dev/api/crash-reports", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      format_version: 1,
      report_id: "abcdef1234567890",
      mode: "remaster",
      exit_code: 7,
      runtime_version: "1.2.3",
      failure_summary: "ERROR: access violation at 0x123456",
      settings: { Width: 2560 },
      logs: { launcher: "FULL_LOG_SENTINEL: access violation at 0x123456" },
      ...overrides
    })
  });
}

function githubResponder({ matches = [] } = {}) {
  const calls = [];
  globalThis.fetch = async (_url, options) => {
    const body = JSON.parse(options.body);
    calls.push(body.query);
    if (body.query.includes("issue(number:"))
      return Response.json({ data: { repository: { issue: { id: "I_overflow", url: "https://github.com/roswellien/corecritical-crash-reports/issues/1", state: "OPEN" } } } });
    if (body.query.includes("repository(owner:"))
      return Response.json({ data: { repository: { id: "R_repo", isPrivate: true }, ...(body.query.includes("matched: search") ? { matched: { nodes: matches } } : {}) } });
    if (body.query.includes("createIssue"))
      return Response.json({ data: { createIssue: { issue: { id: "I_issue", url: "https://github.com/roswellien/corecritical-crash-reports/issues/42", state: "OPEN" } } } });
    if (body.query.includes("updateIssue"))
      return Response.json({ data: { updateIssue: { issue: { id: "I_issue", state: "OPEN" } } } });
    if (body.query.includes("addComment"))
      return Response.json({ data: { addComment: { commentEdge: { node: { id: "IC_comment" } } } } });
    throw new Error("Unexpected GraphQL operation: " + body.query);
  };
  return calls;
}

test("creates a private-repository issue for Project auto-add and returns only a report ID", async () => {
  const calls = githubResponder();
  const response = await onRequestPost({ request: crashRequest(), env: environment });
  assert.equal(response.status, 200);
  const result = await response.json();
  assert.deepEqual(result, { report_id: "abcdef12", duplicate: false, overflow: false });
  assert.equal(calls.length, 2);
  assert.ok(calls.some(query => query.includes("createIssue")));
  assert.ok(!JSON.stringify(result).includes("github.com"));
});

test("groups by mode, exit code, and message; reopens closed matches", async () => {
  const report = JSON.parse(await crashRequest().text());
  const { webcrypto } = await import("node:crypto");
  globalThis.crypto ??= webcrypto;
  const digest = await webcrypto.subtle.digest("SHA-256", new TextEncoder().encode(
    JSON.stringify(["remaster", 7, "error: access violation at <address>"])
  ));
  const marker = [...new Uint8Array(digest)].map(value => value.toString(16).padStart(2, "0")).join("");
  const calls = githubResponder({ matches: [{ id: "I_issue", state: "CLOSED", body: `<!-- crash-fingerprint:${marker} -->`, comments: { totalCount: 0 } }] });
  const response = await onRequestPost({ request: crashRequest(), env: environment });
  assert.deepEqual(await response.json(), { report_id: "abcdef12", duplicate: true, overflow: false });
  assert.ok(calls.some(query => query.includes("updateIssue") && query.includes("state:OPEN")));
  assert.ok(calls.some(query => query.includes("addComment")));
  assert.ok(!calls.some(query => query.includes("createIssue")));
  assert.equal(report.mode, "remaster");
});

test("never groups generic unexpected-exit reports", async () => {
  const calls = githubResponder();
  const generic = { failure_summary: "The launch or game ended unexpectedly. Open Logs for details." };
  const response = await onRequestPost({ request: crashRequest(generic), env: environment });
  assert.equal(response.status, 200);
  assert.ok(!calls.some(query => query.includes("matched: search")));
  assert.ok(calls.some(query => query.includes("createIssue")));
});

test("sends new issues beyond the daily cap to one log-free overflow issue", async () => {
  const calls = githubResponder();
  let overflowBody;
  const baseFetch = globalThis.fetch;
  globalThis.fetch = async (url, options) => {
    const body = JSON.parse(options.body);
    if (body.query.includes("addComment")) overflowBody = body.variables.body;
    return baseFetch(url, options);
  };
  const cappedEnvironment = { ...environment, CRASH_REPORT_DAILY_ISSUE_LIMIT: "0" };
  // Zero is invalid configuration; a valid exhausted D1 counter returns no row.
  cappedEnvironment.CRASH_REPORT_DAILY_ISSUE_LIMIT = "20";
  cappedEnvironment.CRASH_REPORT_DB = {
    prepare() { return { bind: () => ({ first: async () => null }) }; }
  };
  const response = await onRequestPost({ request: crashRequest(), env: cappedEnvironment });
  assert.deepEqual(await response.json(), { report_id: "abcdef12", duplicate: true, overflow: true });
  assert.ok(calls.some(query => query.includes("addComment")));
  assert.ok(!calls.some(query => query.includes("createIssue")));
  assert.ok(overflowBody.includes('"logs": {}'));
  assert.ok(!overflowBody.includes("FULL_LOG_SENTINEL"));
});

test("caps full logs on later matching reports", async () => {
  const { webcrypto } = await import("node:crypto");
  globalThis.crypto ??= webcrypto;
  const digest = await webcrypto.subtle.digest("SHA-256", new TextEncoder().encode(
    JSON.stringify(["remaster", 7, "error: access violation at <address>"])
  ));
  const marker = [...new Uint8Array(digest)].map(value => value.toString(16).padStart(2, "0")).join("");
  let commentBody;
  globalThis.fetch = async (_url, options) => {
    const body = JSON.parse(options.body);
    if (body.query.includes("matched: search")) return Response.json({ data: {
      repository: { id: "R_repo", isPrivate: true }, matched: { nodes: [{ id: "I_issue", state: "OPEN",
        body: `<!-- crash-fingerprint:${marker} -->`, comments: { totalCount: 3 } }] }
    } });
    if (body.query.includes("addComment")) {
      commentBody = body.variables.body;
      return Response.json({ data: { addComment: { commentEdge: { node: { id: "IC_comment" } } } } });
    }
    throw new Error("Unexpected GraphQL operation: " + body.query);
  };
  await onRequestPost({ request: crashRequest(), env: environment });
  assert.ok(commentBody.includes('"logs": {}'));
  assert.ok(!commentBody.includes("FULL_LOG_SENTINEL"));
});

test("rejects reports with missing server configuration", async () => {
  globalThis.fetch = async () => { throw new Error("GitHub should not be contacted."); };
  const response = await onRequestPost({ request: crashRequest(), env: {} });
  assert.equal(response.status, 503);
  assert.deepEqual(await response.json(), { error: "Crash reporting is not configured on the server." });
});

test("refuses to send crash logs to a public repository", async () => {
  globalThis.fetch = async () => Response.json({ data: { repository: { id: "R_repo", isPrivate: false } } });
  const response = await onRequestPost({ request: crashRequest(), env: environment });
  assert.equal(response.status, 503);
  assert.deepEqual(await response.json(), { error: "Crash reports require a configured private GitHub repository." });
});
