import assert from "node:assert/strict";
import { afterEach, test } from "node:test";
import { onRequestPost } from "../functions/api/crash-reports.js";
import { onRequestGet as getAdminCrashReports } from "../functions/admin/crash-reports.js";
import { webcrypto } from "node:crypto";

const originalFetch = globalThis.fetch;
globalThis.crypto ??= webcrypto;
const archivedReports = [];
const database = {
    prepare(query) {
        if (query.includes("INSERT OR IGNORE INTO crash_report_archive")) {
            return {
                bind: (...values) => ({
                    run: async () => {
                        archivedReports.push(values);
                    },
                }),
            };
        }
        return {
            bind: (_day, limit) => ({ first: async () => (limit > 0 ? { issue_count: 1 } : null) }),
        };
    },
};
const environment = {
    CRASH_REPORT_REPOSITORY: "roswellien/corecritical-crash-reports",
    CRASH_REPORT_OVERFLOW_ISSUE_NUMBER: "1",
    CRASH_REPORT_DAILY_ISSUE_LIMIT: "20",
    CRASH_REPORT_DB: database,
    GITHUB_TOKEN: "test-token",
};

afterEach(() => {
    globalThis.fetch = originalFetch;
    archivedReports.length = 0;
});

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
            ...overrides,
        }),
    });
}

function githubResponder({ matches = [] } = {}) {
    const calls = [];
    globalThis.fetch = async (_url, options) => {
        const body = JSON.parse(options.body);
        calls.push(body.query);
        if (body.query.includes("issue(number:"))
            return Response.json({
                data: {
                    repository: {
                        issue: {
                            id: "I_overflow",
                            url: "https://github.com/roswellien/corecritical-crash-reports/issues/1",
                            state: "OPEN",
                        },
                    },
                },
            });
        if (body.query.includes("repository(owner:"))
            return Response.json({
                data: {
                    repository: { id: "R_repo", isPrivate: true },
                    ...(body.query.includes("matched: search")
                        ? { matched: { nodes: matches } }
                        : {}),
                },
            });
        if (body.query.includes("createIssue"))
            return Response.json({
                data: {
                    createIssue: {
                        issue: {
                            id: "I_issue",
                            url: "https://github.com/roswellien/corecritical-crash-reports/issues/42",
                            state: "OPEN",
                        },
                    },
                },
            });
        if (body.query.includes("updateIssue"))
            return Response.json({
                data: { updateIssue: { issue: { id: "I_issue", state: "OPEN" } } },
            });
        if (body.query.includes("addComment"))
            return Response.json({
                data: { addComment: { commentEdge: { node: { id: "IC_comment" } } } },
            });
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
    assert.ok(calls.some((query) => query.includes("createIssue")));
    assert.ok(!JSON.stringify(result).includes("github.com"));
    assert.equal(archivedReports.length, 1);
    assert.equal(archivedReports[0][0], "abcdef1234567890");
    assert.equal(
        JSON.parse(archivedReports[0][7]).failure_summary,
        "ERROR: access violation at 0x123456",
    );
});

test("keeps an archived report and returns a clear accepted status when GitHub is unavailable", async () => {
    globalThis.fetch = async () => {
        throw new Error("GitHub temporarily unavailable");
    };
    const response = await onRequestPost({ request: crashRequest(), env: environment });
    assert.equal(response.status, 202);
    assert.deepEqual(await response.json(), {
        report_id: "abcdef12",
        duplicate: false,
        overflow: false,
        archived_only: true,
    });
    assert.equal(archivedReports.length, 1);
});

test("stores only the disclosed hardware inventory fields and redacts hardware paths", async () => {
    githubResponder();
    const baseFetch = globalThis.fetch;
    let issueBody;
    globalThis.fetch = async (url, options) => {
        const body = JSON.parse(options.body);
        if (body.query.includes("createIssue")) issueBody = body.variables.body;
        return baseFetch(url, options);
    };
    const response = await onRequestPost({
        request: crashRequest({
            hardware: {
                processors: [
                    {
                        manufacturer: "AMD",
                        model: "Ryzen Example C:\\Users\\private\\computer",
                        physicalCores: 8,
                        logicalProcessors: 16,
                        serialNumber: "MUST_NOT_BE_STORED",
                    },
                ],
                memory: {
                    totalBytes: 34359738368,
                    modules: [
                        {
                            capacityBytes: 17179869184,
                            type: "DDR5",
                            configuredSpeedMhz: 5600,
                            partNumber: "MUST_NOT_BE_STORED",
                        },
                    ],
                },
                graphicsAdapters: [
                    {
                        name: "Example GPU",
                        dedicatedVideoMemoryBytes: 12884901888,
                        sharedSystemMemoryBytes: 8589934592,
                        driverVersion: "1.2.3",
                        driverDate: "2026-01-01T00:00:00Z",
                        pnpDeviceId: "MUST_NOT_BE_STORED",
                    },
                ],
                extraField: "MUST_NOT_BE_STORED",
            },
            logs: { launcher: "Network: \\\\nas01\\users\\Jane Doe\\private-game\\file.bin\n" },
        }),
        env: environment,
    });

    assert.equal(response.status, 200);
    assert.ok(issueBody.includes('"Model": "Ryzen Example <local-path>"'));
    assert.ok(issueBody.includes('"Type": "DDR5"'));
    assert.ok(issueBody.includes('"DedicatedVideoMemoryBytes": 12884901888'));
    assert.ok(issueBody.includes('"DriverVersion": "1.2.3"'));
    assert.ok(issueBody.includes("<local-path>"));
    assert.ok(issueBody.includes("<network-path>"));
    assert.ok(!issueBody.includes("Jane Doe") && !issueBody.includes("private-game"));
    assert.ok(!issueBody.includes("MUST_NOT_BE_STORED"));
});

test("formats each log as readable, line-preserving issue text", async () => {
    githubResponder();
    const baseFetch = globalThis.fetch;
    let issueBody;
    globalThis.fetch = async (url, options) => {
        const body = JSON.parse(options.body);
        if (body.query.includes("createIssue")) issueBody = body.variables.body;
        return baseFetch(url, options);
    };
    const response = await onRequestPost({
        request: crashRequest({
            logs: { launcher: "first diagnostic line\nsecond diagnostic line\n" },
        }),
        env: environment,
    });

    assert.equal(response.status, 200);
    assert.ok(
        issueBody.includes(
            "#### Launcher log\n\n```text\nfirst diagnostic line\nsecond diagnostic line\n```",
        ),
    );
    assert.ok(!issueBody.includes('"logs": {}'));
});

test("groups by mode, exit code, and message; reopens closed matches", async () => {
    const report = JSON.parse(await crashRequest().text());
    const { webcrypto } = await import("node:crypto");
    globalThis.crypto ??= webcrypto;
    const digest = await webcrypto.subtle.digest(
        "SHA-256",
        new TextEncoder().encode(
            JSON.stringify(["remaster", 7, "error: access violation at <address>"]),
        ),
    );
    const marker = [...new Uint8Array(digest)]
        .map((value) => value.toString(16).padStart(2, "0"))
        .join("");
    const calls = githubResponder({
        matches: [
            {
                id: "I_issue",
                state: "CLOSED",
                body: `<!-- crash-fingerprint:${marker} -->`,
                comments: { totalCount: 0 },
            },
        ],
    });
    const response = await onRequestPost({ request: crashRequest(), env: environment });
    assert.deepEqual(await response.json(), {
        report_id: "abcdef12",
        duplicate: true,
        overflow: false,
    });
    assert.ok(calls.some((query) => query.includes("updateIssue") && query.includes("state:OPEN")));
    assert.ok(calls.some((query) => query.includes("addComment")));
    assert.ok(!calls.some((query) => query.includes("createIssue")));
    assert.equal(report.mode, "remaster");
});

test("never groups generic unexpected-exit reports", async () => {
    const calls = githubResponder();
    const generic = {
        failure_summary: "The launch or game ended unexpectedly. Open Logs for details.",
    };
    const response = await onRequestPost({ request: crashRequest(generic), env: environment });
    assert.equal(response.status, 200);
    assert.ok(!calls.some((query) => query.includes("matched: search")));
    assert.ok(calls.some((query) => query.includes("createIssue")));
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
        prepare(query) {
            if (query.includes("INSERT OR IGNORE INTO crash_report_archive"))
                return {
                    bind: (...values) => ({
                        run: async () => {
                            archivedReports.push(values);
                        },
                    }),
                };
            return { bind: () => ({ first: async () => null }) };
        },
    };
    const response = await onRequestPost({ request: crashRequest(), env: cappedEnvironment });
    assert.deepEqual(await response.json(), {
        report_id: "abcdef12",
        duplicate: true,
        overflow: true,
    });
    assert.ok(calls.some((query) => query.includes("addComment")));
    assert.ok(!calls.some((query) => query.includes("createIssue")));
    assert.ok(
        overflowBody.includes("Log excerpts were omitted for overflow or repeat-report limits."),
    );
    assert.ok(!overflowBody.includes("FULL_LOG_SENTINEL"));
});

test("returns archive-only success when the daily cap is exhausted and the overflow issue is missing", async () => {
    globalThis.fetch = async (_url, options) => {
        const body = JSON.parse(options.body);
        if (body.query.includes("issue(number:")) {
            return Response.json({ data: { repository: { issue: null } } });
        }
        return Response.json({
            data: {
                repository: { id: "R_repo", isPrivate: true },
                matched: { nodes: [] },
            },
        });
    };
    const cappedEnvironment = {
        ...environment,
        CRASH_REPORT_DB: {
            prepare(query) {
                if (query.includes("INSERT OR IGNORE INTO crash_report_archive")) {
                    return {
                        bind: (...values) => ({
                            run: async () => {
                                archivedReports.push(values);
                            },
                        }),
                    };
                }
                return { bind: () => ({ first: async () => null }) };
            },
        },
    };

    const response = await onRequestPost({ request: crashRequest(), env: cappedEnvironment });

    assert.equal(response.status, 202);
    assert.deepEqual(await response.json(), {
        report_id: "abcdef12",
        duplicate: false,
        overflow: false,
        archived_only: true,
    });
    assert.equal(archivedReports.length, 1);
});

test("caps full logs on later matching reports", async () => {
    const { webcrypto } = await import("node:crypto");
    globalThis.crypto ??= webcrypto;
    const digest = await webcrypto.subtle.digest(
        "SHA-256",
        new TextEncoder().encode(
            JSON.stringify(["remaster", 7, "error: access violation at <address>"]),
        ),
    );
    const marker = [...new Uint8Array(digest)]
        .map((value) => value.toString(16).padStart(2, "0"))
        .join("");
    let commentBody;
    globalThis.fetch = async (_url, options) => {
        const body = JSON.parse(options.body);
        if (body.query.includes("matched: search"))
            return Response.json({
                data: {
                    repository: { id: "R_repo", isPrivate: true },
                    matched: {
                        nodes: [
                            {
                                id: "I_issue",
                                state: "OPEN",
                                body: `<!-- crash-fingerprint:${marker} -->`,
                                comments: { totalCount: 3 },
                            },
                        ],
                    },
                },
            });
        if (body.query.includes("addComment")) {
            commentBody = body.variables.body;
            return Response.json({
                data: { addComment: { commentEdge: { node: { id: "IC_comment" } } } },
            });
        }
        throw new Error("Unexpected GraphQL operation: " + body.query);
    };
    await onRequestPost({ request: crashRequest(), env: environment });
    assert.ok(
        commentBody.includes("Log excerpts were omitted for overflow or repeat-report limits."),
    );
    assert.ok(!commentBody.includes("FULL_LOG_SENTINEL"));
});

test("keeps oversized escaped metadata within GitHub's issue-body limit", async () => {
    githubResponder();
    const baseFetch = globalThis.fetch;
    let issueBody;
    globalThis.fetch = async (url, options) => {
        const body = JSON.parse(options.body);
        if (body.query.includes("createIssue")) issueBody = body.variables.body;
        return baseFetch(url, options);
    };
    const packs = Array.from({ length: 64 }, () => ({
        Id: "`".repeat(120),
        Version: "`".repeat(80),
        SchemaVersion: 1,
        IsEnabled: true,
        Priority: 1,
    }));
    const report = { packs, logs: { launcher: "`".repeat(64 * 1024) } };
    const response = await onRequestPost({ request: crashRequest(report), env: environment });

    assert.equal(response.status, 200);
    assert.ok(issueBody.length <= 48_000);
    assert.ok(
        issueBody.includes("Some report details were omitted to fit GitHub's issue size limit."),
    );
    assert.ok(
        issueBody.includes("Additional log excerpts omitted") ||
            issueBody.includes("Earlier log lines omitted"),
    );
});

test("bounds issue bodies when logs are omitted or absent", async () => {
    githubResponder();
    const baseFetch = globalThis.fetch;
    let issueBody;
    globalThis.fetch = async (url, options) => {
        const body = JSON.parse(options.body);
        if (body.query.includes("createIssue") || body.query.includes("addComment"))
            issueBody = body.variables.body;
        return baseFetch(url, options);
    };
    const packs = Array.from({ length: 64 }, () => ({
        Id: "`".repeat(120),
        Version: "`".repeat(80),
        SchemaVersion: 1,
        IsEnabled: true,
        Priority: 1,
    }));
    await onRequestPost({ request: crashRequest({ packs, logs: {} }), env: environment });
    assert.ok(issueBody.length <= 48_000);

    const exhaustedEnvironment = {
        ...environment,
        CRASH_REPORT_DB: {
            prepare(query) {
                if (query.includes("INSERT OR IGNORE INTO crash_report_archive"))
                    return { bind: () => ({ run: async () => ({ success: true }) }) };
                return { bind: () => ({ first: async () => null }) };
            },
        },
    };
    await onRequestPost({ request: crashRequest({ packs, logs: {} }), env: exhaustedEnvironment });
    assert.ok(issueBody.length <= 48_000);
});

test("rejects reports with missing server configuration", async () => {
    globalThis.fetch = async () => {
        throw new Error("GitHub should not be contacted.");
    };
    const response = await onRequestPost({ request: crashRequest(), env: {} });
    assert.equal(response.status, 503);
    assert.deepEqual(await response.json(), {
        error: "Crash reporting is not configured on the server.",
    });
});

test("refuses to send crash logs to a public repository", async () => {
    globalThis.fetch = async () =>
        Response.json({ data: { repository: { id: "R_repo", isPrivate: false } } });
    const response = await onRequestPost({ request: crashRequest(), env: environment });
    assert.equal(response.status, 202);
    assert.deepEqual(await response.json(), {
        report_id: "abcdef12",
        duplicate: false,
        overflow: false,
        archived_only: true,
    });
    assert.equal(archivedReports.length, 1);
});

const adminEnvironment = {
    ...environment,
    CRASH_REPORT_ACCESS_ISSUER: "https://corecritical.cloudflareaccess.com",
    CRASH_REPORT_ACCESS_AUD: "crash-report-admin-audience",
    CRASH_REPORT_ADMIN_EMAIL: "admin@example.com",
};

function base64Url(bytes) {
    return Buffer.from(bytes).toString("base64url");
}

async function makeAccessToken(privateKey, overrides = {}) {
    const header = base64Url(JSON.stringify({ alg: "RS256", kid: "test-key" }));
    const payload = base64Url(
        JSON.stringify({
            iss: adminEnvironment.CRASH_REPORT_ACCESS_ISSUER,
            aud: [adminEnvironment.CRASH_REPORT_ACCESS_AUD],
            email: adminEnvironment.CRASH_REPORT_ADMIN_EMAIL,
            iat: Math.floor(Date.now() / 1000),
            exp: Math.floor(Date.now() / 1000) + 300,
            ...overrides,
        }),
    );
    const input = `${header}.${payload}`;
    const signature = new Uint8Array(
        await crypto.subtle.sign("RSASSA-PKCS1-v1_5", privateKey, new TextEncoder().encode(input)),
    );
    return `${input}.${base64Url(signature)}`;
}

let adminKeyPair;
let adminJwk;
async function createAdminAccess() {
    if (!adminKeyPair) {
        adminKeyPair = await crypto.subtle.generateKey(
            {
                name: "RSASSA-PKCS1-v1_5",
                modulusLength: 2048,
                publicExponent: new Uint8Array([1, 0, 1]),
                hash: "SHA-256",
            },
            true,
            ["sign", "verify"],
        );
        adminJwk = await crypto.subtle.exportKey("jwk", adminKeyPair.publicKey);
        Object.assign(adminJwk, { kid: "test-key", alg: "RS256", use: "sig" });
    }
    const jwk = adminJwk;
    globalThis.fetch = async () => Response.json({ keys: [jwk] });
    return {
        privateKey: adminKeyPair.privateKey,
        token: await makeAccessToken(adminKeyPair.privateKey),
    };
}

test("keeps the report archive inaccessible without a valid admin Access token", async () => {
    const unauthenticated = await getAdminCrashReports({
        request: new Request("https://corecritical.dev/admin/crash-reports"),
        env: adminEnvironment,
    });
    assert.equal(unauthenticated.status, 401);
    assert.ok(!(await unauthenticated.text()).includes("abcdef1234567890"));

    const { token } = await createAdminAccess();
    const unauthorized = await getAdminCrashReports({
        request: new Request("https://corecritical.dev/admin/crash-reports", {
            headers: { "cf-access-jwt-assertion": token },
        }),
        env: { ...adminEnvironment, CRASH_REPORT_ADMIN_EMAIL: "other@example.com" },
    });
    assert.equal(unauthorized.status, 403);
    assert.ok(!(await unauthorized.text()).includes("abcdef1234567890"));

    const tokenParts = token.split(".");
    tokenParts[2] = (tokenParts[2].startsWith("A") ? "B" : "A") + tokenParts[2].slice(1);
    const tamperedToken = tokenParts.join(".");
    const tampered = await getAdminCrashReports({
        request: new Request("https://corecritical.dev/admin/crash-reports", {
            headers: { "cf-access-jwt-assertion": tamperedToken },
        }),
        env: adminEnvironment,
    });
    assert.equal(tampered.status, 403);
    assert.ok(!(await tampered.text()).includes("abcdef1234567890"));
});

test("renders archived reports and log lines only for the configured admin", async () => {
    const { token } = await createAdminAccess();
    const report = {
        report_id: "report-1234",
        created_utc: "2026-10-29T13:00:00Z",
        mode: "remaster",
        exit_code: 7,
        failure_summary: "<script>alert('xss')</script>",
        logs: { launcher: "first line\nsecond line <script>" },
    };
    const row = {
        report_id: report.report_id,
        created_utc: report.created_utc,
        stored_utc: "2026-10-29T13:01:00Z",
        mode: report.mode,
        exit_code: report.exit_code,
        failure_summary: report.failure_summary,
        crash_fingerprint: "deadbeef",
        report_json: JSON.stringify(report),
    };
    const adminDb = {
        prepare(query) {
            return {
                all: async () => ({ results: [row] }),
                bind: () => ({
                    first: async () => (query.includes("WHERE report_id") ? row : null),
                }),
            };
        },
    };
    const response = await getAdminCrashReports({
        request: new Request("https://corecritical.dev/admin/crash-reports", {
            headers: { "cf-access-jwt-assertion": token },
        }),
        env: { ...adminEnvironment, CRASH_REPORT_DB: adminDb },
    });
    const html = await response.text();
    assert.equal(response.status, 200);
    assert.ok(html.includes(report.report_id));
    assert.ok(html.includes("&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;"));
    assert.ok(!html.includes("<script>"));

    const detail = await getAdminCrashReports({
        request: new Request("https://corecritical.dev/admin/crash-reports?id=report-1234", {
            headers: { "cf-access-jwt-assertion": token },
        }),
        env: { ...adminEnvironment, CRASH_REPORT_DB: adminDb },
    });
    assert.equal(detail.status, 200);
    const detailHtml = await detail.text();
    assert.ok(detailHtml.includes("Recent log excerpts"));
    assert.ok(detailHtml.includes("first line\nsecond line &lt;script&gt;"));
    assert.ok(!detailHtml.includes("<script>"));
});
