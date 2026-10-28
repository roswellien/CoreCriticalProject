import assert from "node:assert/strict";
import { afterEach, test } from "node:test";
import { onRequestPost } from "../functions/api/crash-reports.js";

const originalFetch = globalThis.fetch;
const environment = {
  CRASH_REPORT_REPOSITORY: "roswellien/MW3Recomp-Private",
  CRASH_REPORT_PROJECT_ID: "PVT_testproject",
  GITHUB_TOKEN: "test-token"
};

afterEach(() => { globalThis.fetch = originalFetch; });

function crashRequest() {
  return new Request("https://corecritical.dev/api/crash-reports", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      format_version: 1,
      report_id: "test-report",
      failure_summary: "ERROR: access violation at 0x123456",
      logs: { launcher: "ERROR: access violation at 0x123456" }
    })
  });
}

test("creates a GitHub issue and adds it to the configured Project", async () => {
  const calls = [];
  globalThis.fetch = async (_url, options) => {
    const body = JSON.parse(options.body);
    calls.push(body.query);
    if (body.query.includes("repository(owner:"))
      return Response.json({ data: { repository: { id: "R_repo" }, search: { nodes: [] } } });
    if (body.query.includes("createIssue"))
      return Response.json({ data: { createIssue: { issue: { id: "I_issue", url: "https://github.com/roswellien/MW3Recomp-Private/issues/42" } } } });
    return Response.json({ data: { addProjectV2ItemById: { item: { id: "PVTI_item" } } } });
  };

  const response = await onRequestPost({ request: crashRequest(), env: environment });
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), {
    issue_url: "https://github.com/roswellien/MW3Recomp-Private/issues/42", duplicate: false
  });
  assert.equal(calls.length, 3);
});

test("updates the existing issue for a matching crash fingerprint", async () => {
  const calls = [];
  globalThis.fetch = async (_url, options) => {
    const body = JSON.parse(options.body);
    calls.push(body.query);
    if (body.query.includes("repository(owner:")) {
      const marker = body.variables.query.match(/crash-fingerprint:([a-f0-9]+)/)[1];
      return Response.json({ data: { repository: { id: "R_repo" }, search: { nodes: [
        { id: "I_issue", url: "https://github.com/roswellien/MW3Recomp-Private/issues/42", body: `<!-- crash-fingerprint:${marker} -->` }
      ] } } });
    }
    if (body.query.includes("addComment"))
      return Response.json({ data: { addComment: { commentEdge: { node: { id: "IC_comment" } } } } });
    return Response.json({ data: { addProjectV2ItemById: { item: { id: "PVTI_item" } } } });
  };

  const response = await onRequestPost({ request: crashRequest(), env: environment });
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), {
    issue_url: "https://github.com/roswellien/MW3Recomp-Private/issues/42", duplicate: true
  });
  assert.equal(calls.length, 3);
  assert.ok(calls.some(query => query.includes("addComment")));
  assert.ok(!calls.some(query => query.includes("createIssue")));
});

test("rejects a report when the server is not configured", async () => {
  globalThis.fetch = async () => { throw new Error("GitHub should not be contacted."); };
  const response = await onRequestPost({ request: crashRequest(), env: {} });
  assert.equal(response.status, 503);
  assert.deepEqual(await response.json(), { error: "Crash reporting is not configured on the server." });
});
