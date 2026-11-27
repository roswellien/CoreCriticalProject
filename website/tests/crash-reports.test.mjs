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

// A D1 binding whose archive table is missing, as when migration 0002 was never
// applied. The daily issue counter (migration 0001) still works unless told otherwise.
function brokenArchiveEnvironment({ dailySlotAvailable = true } = {}) {
    return {
        ...environment,
        CRASH_REPORT_DB: {
            prepare(query) {
                if (query.includes("INSERT OR IGNORE INTO crash_report_archive")) {
                    return {
                        bind: () => ({
                            run: async () => {
                                throw new Error("D1_ERROR: no such table: crash_report_archive");
                            },
                        }),
                    };
                }
                return {
                    bind: () => ({
                        first: async () => (dailySlotAvailable ? { issue_count: 1 } : null),
                    }),
                };
            },
        },
    };
}

// Records the issue and comment bodies sent to GitHub, on top of githubResponder.
function recordSentBodies() {
    const sentBodies = [];
    const baseFetch = globalThis.fetch;
    globalThis.fetch = async (url, options) => {
        const body = JSON.parse(options.body);
        if (typeof body.variables?.body === "string") sentBodies.push(body.variables.body);
        return baseFetch(url, options);
    };
    return sentBodies;
}

// Collects console.error lines for one request and silences them.
async function withConsoleErrors(run) {
    const lines = [];
    const originalError = console.error;
    console.error = (...parts) => lines.push(parts.join(" "));
    try {
        return { result: await run(), lines };
    } finally {
        console.error = originalError;
    }
}

function archiveFailureLogLines(lines) {
    return lines.filter(
        (line) =>
            line.includes("table crash_report_archive") &&
            line.includes("0002_crash_report_archive.sql"),
    );
}

async function crashFingerprintFor(mode, exitCode, summary) {
    const digest = await crypto.subtle.digest(
        "SHA-256",
        new TextEncoder().encode(JSON.stringify([mode, exitCode, summary])),
    );
    return [...new Uint8Array(digest)].map((value) => value.toString(16).padStart(2, "0")).join("");
}

test("still creates the GitHub issue when the archive save fails, and says so in the issue", async () => {
    const calls = githubResponder();
    const sentBodies = recordSentBodies();
    const { result: response, lines } = await withConsoleErrors(() =>
        onRequestPost({ request: crashRequest(), env: brokenArchiveEnvironment() }),
    );
    assert.equal(response.status, 200);
    assert.deepEqual(await response.json(), {
        report_id: "abcdef12",
        duplicate: false,
        overflow: false,
    });
    assert.ok(calls.some((query) => query.includes("createIssue")));
    assert.equal(sentBodies.length, 1);
    assert.ok(sentBodies[0].includes("Not saved to the admin archive"));
    assert.equal(archiveFailureLogLines(lines).length, 1);
});

test("leaves the archive note out of issues when the archive save works", async () => {
    githubResponder();
    const sentBodies = recordSentBodies();
    const response = await onRequestPost({ request: crashRequest(), env: environment });
    assert.equal(response.status, 200);
    assert.equal(sentBodies.length, 1);
    assert.ok(!sentBodies[0].includes("Not saved to the admin archive"));
});

test("still comments on a matching issue when the archive save fails", async () => {
    const marker = await crashFingerprintFor("remaster", 7, "error: access violation at <address>");
    const calls = githubResponder({
        matches: [
            {
                id: "I_issue",
                state: "OPEN",
                body: `<!-- crash-fingerprint:${marker} -->`,
                comments: { totalCount: 0 },
            },
        ],
    });
    const sentBodies = recordSentBodies();
    const { result: response, lines } = await withConsoleErrors(() =>
        onRequestPost({ request: crashRequest(), env: brokenArchiveEnvironment() }),
    );
    assert.equal(response.status, 200);
    assert.deepEqual(await response.json(), {
        report_id: "abcdef12",
        duplicate: true,
        overflow: false,
    });
    assert.ok(calls.some((query) => query.includes("addComment")));
    assert.ok(!calls.some((query) => query.includes("createIssue")));
    assert.equal(sentBodies.length, 1);
    assert.ok(sentBodies[0].includes("Not saved to the admin archive"));
    assert.equal(archiveFailureLogLines(lines).length, 1);
});

test("still comments on the overflow issue when the archive save fails and the daily cap is reached", async () => {
    const calls = githubResponder();
    const sentBodies = recordSentBodies();
    const { result: response, lines } = await withConsoleErrors(() =>
        onRequestPost({
            request: crashRequest(),
            env: brokenArchiveEnvironment({ dailySlotAvailable: false }),
        }),
    );
    assert.equal(response.status, 200);
    assert.deepEqual(await response.json(), {
        report_id: "abcdef12",
        duplicate: true,
        overflow: true,
    });
    assert.ok(calls.some((query) => query.includes("addComment")));
    assert.equal(sentBodies.length, 1);
    assert.ok(sentBodies[0].includes("Not saved to the admin archive"));
    assert.equal(archiveFailureLogLines(lines).length, 1);
});

test("reports a failure, not archive-only success, when neither the archive nor GitHub works", async () => {
    globalThis.fetch = async () => {
        throw new Error("GitHub temporarily unavailable");
    };
    const { result: response, lines } = await withConsoleErrors(() =>
        onRequestPost({ request: crashRequest(), env: brokenArchiveEnvironment() }),
    );
    assert.equal(response.status, 502);
    const result = await response.json();
    assert.equal(result.archived_only, undefined);
    assert.ok(result.error.includes("could not save this crash report"));
    assert.equal(archiveFailureLogLines(lines).length, 1);
});

test("reports a failure when the archive save fails and the repository is public", async () => {
    const calls = [];
    globalThis.fetch = async (_url, options) => {
        calls.push(JSON.parse(options.body).query);
        return Response.json({ data: { repository: { id: "R_repo", isPrivate: false } } });
    };
    const { result: response, lines } = await withConsoleErrors(() =>
        onRequestPost({ request: crashRequest(), env: brokenArchiveEnvironment() }),
    );
    assert.equal(response.status, 502);
    assert.equal((await response.json()).archived_only, undefined);
    assert.ok(!calls.some((query) => query.includes("createIssue")));
    assert.equal(archiveFailureLogLines(lines).length, 1);
    assert.ok(lines.some((line) => line.includes("not private, and the archive save failed")));
});

test("reports a failure when the archive save fails, the daily cap is reached and the overflow issue is missing", async () => {
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
    const { result: response, lines } = await withConsoleErrors(() =>
        onRequestPost({
            request: crashRequest(),
            env: brokenArchiveEnvironment({ dailySlotAvailable: false }),
        }),
    );
    assert.equal(response.status, 502);
    assert.equal((await response.json()).archived_only, undefined);
    assert.equal(archiveFailureLogLines(lines).length, 1);
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
    const invalidTokenPage = await tampered.text();
    assert.ok(!invalidTokenPage.includes("abcdef1234567890"));

    const tamperedAgain = await getAdminCrashReports({
        request: new Request("https://corecritical.dev/admin/crash-reports", {
            headers: { "cf-access-jwt-assertion": tamperedToken },
        }),
        env: { ...adminEnvironment, CRASH_REPORT_ADMIN_EMAIL: "other@example.com" },
    });
    assert.equal(tamperedAgain.status, tampered.status);
    assert.equal(await tamperedAgain.text(), invalidTokenPage);
});

test("allows both configured archive admins and rejects a partial match", async () => {
    const { privateKey, token } = await createAdminAccess();
    const env = {
        ...adminEnvironment,
        CRASH_REPORT_ADMIN_EMAIL: " admin@example.com, SECOND@example.com, ",
        CRASH_REPORT_DB: { prepare: () => ({ all: async () => ({ results: [] }) }) },
    };

    const response = await getAdminCrashReports({
        request: new Request("https://corecritical.dev/admin/crash-reports", {
            headers: { "cf-access-jwt-assertion": token },
        }),
        env,
    });
    assert.equal(response.status, 200);

    const secondToken = await makeAccessToken(privateKey, { email: "second@example.com" });
    const secondResponse = await getAdminCrashReports({
        request: new Request("https://corecritical.dev/admin/crash-reports", {
            headers: { "cf-access-jwt-assertion": secondToken },
        }),
        env,
    });
    assert.equal(secondResponse.status, 200);

    const thirdToken = await makeAccessToken(privateKey, { email: "cond@example.com" });
    const thirdResponse = await getAdminCrashReports({
        request: new Request("https://corecritical.dev/admin/crash-reports", {
            headers: { "cf-access-jwt-assertion": thirdToken },
        }),
        env,
    });
    assert.equal(thirdResponse.status, 403);
});

test("rejects an archive admin allowlist containing only separators and whitespace", async () => {
    const { token } = await createAdminAccess();
    const env = {
        ...adminEnvironment,
        CRASH_REPORT_ADMIN_EMAIL: " , , ",
        CRASH_REPORT_DB: { prepare: () => ({ all: async () => ({ results: [] }) }) },
    };

    const response = await getAdminCrashReports({
        request: new Request("https://corecritical.dev/admin/crash-reports", {
            headers: { "cf-access-jwt-assertion": token },
        }),
        env,
    });
    assert.equal(response.status, 503);
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

test("accepts signed int32 Windows exit codes, camelCase settings/packs, and native_crash/native_run logs", async () => {
    const calls = githubResponder();
    const sentBodies = recordSentBodies();
    const response = await onRequestPost({
        request: crashRequest({
            exit_code: -1073741819,
            launcher_version: "1.0.53-preview",
            runtime_version: "mw3-re-2026.11 (abcdef123456)",
            runtime_source_commit: "abcdef1234567890abcdef1234567890abcdef12",
            os: "Windows 11 23H2 (OS Build 10.0.22631.4317)",
            failure_summary:
                "HOST EXCEPTION c0000005 at C:\\Games\\Core Critical\\NativePreview\\bin\\mw3.exe +0x45678 (access 0 address 0000000000000018)",
            settings: {
                engineMode: "remaster",
                width: 2560,
                height: 1440,
                windowMode: "fullscreen_windowed",
                antiAliasing: "fxaa",
                anisotropicFiltering: 16,
                drawDistance: 2400,
                fogDistance: 1600,
                localCdAudio: true,
                instantReplay: false,
                performanceMonitor: true,
                renderThread: true,
            },
            packs: [
                {
                    id: "com.mw3remaster.updated-mw3-mechs",
                    version: "1.4.0",
                    schemaVersion: 2,
                    isEnabled: true,
                    priority: 1,
                },
            ],
            logs: {
                launcher: "Startup: Checking game files...",
                native_run:
                    "mw3: crash details, if any, are written to C:\\Users\\Jane Doe\\AppData\\Local\\MW3Remaster\\mw3-re\\profiles\\native-preview\\crash.txt\nmw3: window 2560x1440 on Vulkan\nC:\\Users\\Jane Doe\\secret\\notes.txt",
                native_crash:
                    "HOST EXCEPTION c0000005 at C:\\Games\\Core Critical\\NativePreview\\bin\\mw3.exe +0x45678 (access 0 address 0000000000000018)\nmw3: crashed: exception 0xc0000005 at 00007FF612345678 module base 00007FF612300000 RVA 0x45678\nmw3: access violation: read (0) target 0x0000000000000018\nmw3: minidump: C:\\Users\\Jane Doe\\AppData\\Local\\MW3Remaster\\mw3-re\\profiles\\native-preview\\crash.dmp\n",
            },
        }),
        env: environment,
    });

    assert.equal(response.status, 200);
    assert.ok(calls.some((query) => query.includes("createIssue")));
    assert.equal(archivedReports.length, 1);
    const archived = JSON.parse(archivedReports[0][7]);
    assert.equal(archived.exit_code, -1073741819);
    assert.equal(archived.settings.Width, 2560);
    assert.equal(archived.settings.Height, 1440);
    assert.equal(archived.settings.WindowMode, "fullscreen_windowed");
    assert.equal(archived.settings.RenderThread, true);
    assert.deepEqual(archived.packs, [
        {
            id: "com.mw3remaster.updated-mw3-mechs",
            version: "1.4.0",
            schema_version: 2,
            enabled: true,
            priority: 1,
        },
    ]);
    assert.ok(
        archived.failure_summary.includes(
            "<local-path>/mw3.exe +0x45678 (access 0 address 0000000000000018)",
        ),
    );
    assert.ok(archived.logs.native_crash.includes("RVA 0x45678"));
    assert.ok(
        archived.logs.native_crash.includes("access violation: read (0) target 0x0000000000000018"),
    );
    assert.ok(archived.logs.native_crash.includes("mw3: minidump: <local-path>"));
    assert.ok(
        archived.logs.native_run.includes(
            "mw3: crash details, if any, are written to <local-path>",
        ),
    );
    assert.ok(!JSON.stringify(archived).includes("Jane Doe"));
    assert.ok(!JSON.stringify(archived).includes("Core Critical\\NativePreview"));

    assert.equal(sentBodies.length, 1);
    const crashHeadingIndex = sentBodies[0].indexOf("#### Native crash details (crash.txt)");
    const runHeadingIndex = sentBodies[0].indexOf("#### Native run log (mw3.log)");
    const launcherHeadingIndex = sentBodies[0].indexOf("#### Launcher log");
    assert.ok(crashHeadingIndex >= 0 && runHeadingIndex > crashHeadingIndex);
    assert.ok(launcherHeadingIndex > runHeadingIndex);
});

test("groups relocated native faults but distinguishes different relative addresses", async () => {
    githubResponder();
    const failures = [
        "mw3: crashed: exception 0xc0000005 at 00007FF700005234 module base 00007FF700000000 RVA 0x5234 (access violation: write (1) target 0000000000000000)",
        "mw3: crashed: exception 0xc0000005 at 00007FF600005234 module base 00007FF600000000 RVA 0x5234 (access violation: write (1) target 0000000000000010)",
        "mw3: crashed: exception 0xc0000005 at 00007FF600005678 module base 00007FF600000000 RVA 0x5678 (access violation: write (1) target 0000000000000010)",
    ];
    for (const failure_summary of failures) {
        const response = await onRequestPost({
            request: crashRequest({ failure_summary }),
            env: environment,
        });
        assert.equal(response.status, 200);
    }
    const fingerprints = archivedReports.map((report) => report[6]);
    assert.ok(fingerprints[0]);
    assert.equal(fingerprints[0], fingerprints[1]);
    assert.notEqual(fingerprints[0], fingerprints[2]);
});

test("keeps 'No specific failure was recorded.' ungrouped", async () => {
    const calls = githubResponder();
    const response = await onRequestPost({
        request: crashRequest({
            exit_code: -1073741819,
            failure_summary: "No specific failure was recorded.",
        }),
        env: environment,
    });
    assert.equal(response.status, 200);
    assert.ok(!calls.some((query) => query.includes("matched: search")));
    assert.ok(calls.some((query) => query.includes("createIssue")));
    assert.equal(archivedReports.length, 1);
    assert.equal(archivedReports[0][6], null);
});

test("renders structured semantic admin detail sections for rich and sparse reports with escaped HTML", async () => {
    const { token } = await createAdminAccess();
    const richReport = {
        format_version: 1,
        report_id: "report-rich-5678",
        created_utc: "2026-11-23T12:00:00Z",
        launcher_version: "1.0.53-preview",
        runtime_version: "mw3-re-2026.11 (abcdef123456)",
        mode: "remaster",
        exit_code: -1073741819,
        os: "Windows 11 23H2 (OS Build 10.0.22631.4317)",
        architecture: "X64",
        dotnet_runtime: ".NET 8.0.10",
        failure_summary:
            "mw3: crashed: exception 0xc0000005 RVA 0x45678 <img src=x onerror=alert(1)>",
        hardware: {
            Processors: [
                {
                    Manufacturer: "AMD",
                    Model: "Ryzen 7 7800X3D",
                    PhysicalCores: 8,
                    LogicalProcessors: 16,
                },
            ],
            Memory: {
                TotalBytes: 34359738368,
                Modules: [
                    {
                        CapacityBytes: 17179869184,
                        Type: "DDR5",
                        ConfiguredSpeedMhz: 6000,
                    },
                ],
            },
            GraphicsAdapters: [
                {
                    Name: "NVIDIA GeForce RTX 4080",
                    DedicatedVideoMemoryBytes: 17179869184,
                    SharedSystemMemoryBytes: 17179869184,
                    DriverVersion: "32.0.15.6094",
                    DriverDate: "2026-08-14T00:00:00Z",
                },
            ],
        },
        settings: {
            Width: 2560,
            Height: 1440,
            WindowMode: "fullscreen_windowed",
            AntiAliasing: "fxaa",
            AnisotropicFiltering: 16,
            DrawDistance: 2400,
            RenderThread: true,
        },
        packs: [
            {
                id: "com.mw3remaster.updated-mw3-mechs",
                version: "1.4.0",
                schema_version: 2,
                enabled: true,
                priority: 1,
            },
        ],
        logs: {
            launcher: "Launcher log line",
            native_run: "mw3: run log line",
            native_crash: "mw3: crashed: exception 0xc0000005 RVA 0x45678",
        },
    };
    const richRow = {
        report_id: richReport.report_id,
        created_utc: richReport.created_utc,
        stored_utc: "2026-11-23T12:00:05Z",
        mode: richReport.mode,
        exit_code: richReport.exit_code,
        failure_summary: richReport.failure_summary,
        crash_fingerprint: "cafebabe1234",
        report_json: JSON.stringify(richReport),
    };
    const adminDb = {
        prepare() {
            return {
                all: async () => ({ results: [richRow] }),
                bind: () => ({ first: async () => richRow }),
            };
        },
    };

    const detail = await getAdminCrashReports({
        request: new Request("https://corecritical.dev/admin/crash-reports?id=report-rich-5678", {
            headers: { "cf-access-jwt-assertion": token },
        }),
        env: { ...adminEnvironment, CRASH_REPORT_DB: adminDb },
    });
    assert.equal(detail.status, 200);
    const html = await detail.text();
    assert.ok(html.includes("-1073741819 (0xC0000005)"));
    assert.ok(html.includes("1.0.53-preview"));
    assert.ok(html.includes("mw3-re-2026.11 (abcdef123456)"));
    assert.ok(html.includes("Windows 11 23H2 (OS Build 10.0.22631.4317)"));
    assert.ok(html.includes("Ryzen 7 7800X3D"));
    assert.ok(html.includes("8 physical cores, 16 logical processors"));
    assert.ok(html.includes("32 GiB total"));
    assert.ok(html.includes("16 GiB · DDR5 @ 6000 MHz"));
    assert.ok(html.includes("NVIDIA GeForce RTX 4080"));
    assert.ok(html.includes("VRAM: 16 GiB"));
    assert.ok(html.includes("2560 × 1440"));
    assert.ok(html.includes("Render thread"));
    assert.ok(html.includes("com.mw3remaster.updated-mw3-mechs"));
    assert.ok(html.includes("Enabled"));
    assert.ok(
        html.indexOf("Native crash details (crash.txt)") < html.indexOf("Native run log (mw3.log)"),
    );
    assert.ok(
        html.includes(
            '<details class="pane" open><summary>Native crash details (crash.txt)</summary>',
        ),
    );
    assert.ok(html.includes("Raw report metadata (JSON)"));
    assert.ok(!html.includes("<img src=x"));
    assert.ok(html.includes("&lt;img src=x onerror=alert(1)&gt;"));
});

test("preserves trailing error text after single-quoted Process.Start paths and groups duplicates", async () => {
    const calls = githubResponder();
    const sentBodies = recordSentBodies();
    const firstSummary =
        "ERROR: An error occurred trying to start process 'C:\\Games\\Core Critical\\Launcher\\NativePreview\\bin\\mw3.exe' with working directory 'C:\\Games\\Core Critical\\Launcher\\NativePreview\\bin'. An Application Control policy has blocked this file.";
    const firstResponse = await onRequestPost({
        request: crashRequest({
            report_id: "smartapp0001",
            failure_summary: firstSummary,
            logs: {
                launcher: `${firstSummary}\n'\\\\nas01\\users\\Jane Doe\\mw3.exe' was blocked by policy.`,
                native_crash:
                    "HOST EXCEPTION c0000005 at C:\\Games\\Core Critical\\mw3.exe +0x45678 (access 0 address 0000000000000018)\nERROR: Process 'C:\\Games\\Core Critical\\mw3.exe' blocked.",
            },
        }),
        env: environment,
    });
    assert.equal(firstResponse.status, 200);
    assert.equal(archivedReports.length, 1);
    const archived = JSON.parse(archivedReports[0][7]);
    const expectedSummary =
        "ERROR: An error occurred trying to start process '<local-path>' with working directory '<local-path>'. An Application Control policy has blocked this file.";
    assert.equal(archived.failure_summary, expectedSummary);
    assert.equal(
        archived.logs.launcher,
        `${expectedSummary}\n'<network-path>' was blocked by policy.`,
    );
    assert.equal(
        archived.logs.native_crash,
        "HOST EXCEPTION c0000005 at <local-path>/mw3.exe +0x45678 (access 0 address 0000000000000018)\nERROR: Process '<local-path>' blocked.",
    );
    assert.ok(!JSON.stringify(archived).includes("Core Critical"));
    assert.ok(!JSON.stringify(archived).includes("Jane Doe"));
    assert.ok(sentBodies[0].includes(expectedSummary));

    const firstFingerprint = archivedReports[0][6];
    assert.ok(firstFingerprint);
    const duplicateCalls = githubResponder({
        matches: [
            {
                id: "I_existing",
                state: "OPEN",
                body: `<!-- crash-fingerprint:${firstFingerprint} -->`,
                comments: { totalCount: 0 },
            },
        ],
    });
    const secondResponse = await onRequestPost({
        request: crashRequest({
            report_id: "smartapp0002",
            failure_summary:
                "ERROR: An error occurred trying to start process 'D:\\Other Games\\MW3\\NativePreview\\bin\\mw3.exe' with working directory 'D:\\Other Games\\MW3\\NativePreview\\bin'. An Application Control policy has blocked this file.",
            logs: { launcher: "retry" },
        }),
        env: environment,
    });
    assert.equal(secondResponse.status, 200);
    assert.deepEqual(await secondResponse.json(), {
        report_id: "smartapp",
        duplicate: true,
        overflow: false,
    });
    assert.equal(archivedReports[1][6], firstFingerprint);
    assert.ok(calls.some((query) => query.includes("createIssue")));
    assert.ok(duplicateCalls.some((query) => query.includes("addComment")));
    assert.ok(!duplicateCalls.some((query) => query.includes("createIssue")));
});

test("preserves internal apostrophes, mixed separators, delimiters, and prose boundaries in single-quoted paths", async () => {
    const cases = [
        [
            "Apostrophe followed by letter or space",
            "ERROR: Failed to start 'C:\\Users\\O'Connor\\Players' Choice\\Bob's Mods\\mw3.exe' in 'D:\\Games\\Players' Choice'. Access is denied.",
            "ERROR: Failed to start '<local-path>' in '<local-path>'. Access is denied.",
        ],
        [
            "Apostrophe followed by punctuation inside filename",
            "ERROR: Failed to open 'C:\\Users\\v1'.txt' because locked.",
            "ERROR: Failed to open '<local-path>' because locked.",
        ],
        [
            "Single-quoted UNC with apostrophe and space",
            "'\\\\nas01\\users\\Players' Choice\\mw3.exe' in '\\\\nas01\\users\\Players' Choice' was blocked.",
            "'<network-path>' in '<network-path>' was blocked.",
        ],
        [
            "Mixed-separator single-quoted paths with apostrophe and space",
            "Failed 'D:\\Users\\Players' Choice/mw3.exe' in 'D:\\Users\\Players' Choice/NativePreview/bin' and 'D:/Users/Players' Choice\\bin'.",
            "Failed '<local-path>' in '<local-path>' and '<local-path>'.",
        ],
        [
            "Contractions, prose slashes, and other single-quoted strings",
            "ERROR: 'C:\\Games\\a.exe' can't start; 'C:\\Games\\b.exe' failed/errored because users' policy ('reason') blocked it.",
            "ERROR: '<local-path>' can't start; '<local-path>' failed/errored because users' policy ('reason') blocked it.",
        ],
        [
            "Prose slashes before possessive plurals",
            "ERROR: 'C:\\Games\\b.exe' read/users' policy and 'C:\\Games\\c.exe' read/write/execute because users' policy blocked it.",
            "ERROR: '<local-path>' read/users' policy and '<local-path>' read/write/execute because users' policy blocked it.",
        ],
        [
            "Colon and possessive name after quoted path",
            "ERROR: 'C:\\Games\\a.exe' failed: James' policy blocked it.",
            "ERROR: '<local-path>' failed: James' policy blocked it.",
        ],
        [
            "Common wrapping delimiters",
            "('C:\\a\\1.exe') ['C:\\b\\2.exe','C:\\c\\3.exe'] path='C:\\d\\4.exe',dir='\\\\nas01\\s'; {\"exe\":\"'C:\\e\\5.exe'\"} \"'C:\\f\\6.exe' blocked\" `'C:\\g\\7.exe'`",
            "('<local-path>') ['<local-path>','<local-path>'] path='<local-path>',dir='<network-path>'; {\"exe\":\"'<local-path>'\"} \"'<local-path>' blocked\" `'<local-path>'`",
        ],
        [
            "Multi-line single-quoted paths",
            "Launcher log:\n'C:\\Games\\Core Critical\\mw3.exe' was blocked.\r\n'\\\\nas01\\share\\Jane Doe\\mw3.exe' was blocked.",
            "Launcher log:\n'<local-path>' was blocked.\r\n'<network-path>' was blocked.",
        ],
        [
            "Unclosed single-quoted paths do not leak",
            "ERROR: Could not open 'C:\\Users\\Alice\\secret.txt\nUnclosed 'C:\\Users\\Alice\\secret and \"quoted\" 'C:\\Users\\Bob\\other.exe' failed.",
            "ERROR: Could not open '<local-path>\nUnclosed '<local-path>\"quoted\" '<local-path>' failed.",
        ],
        [
            "Double-quoted path containing apostrophe and space",
            '"C:\\Users\\James\' Folder\\mw3.exe" was blocked.',
            '"<local-path>" was blocked.',
        ],
        [
            "Extended Win32 single-quoted path containing drive colon",
            "ERROR: Failed to open '\\\\?\\C:\\Users\\Alice\\mw3.exe' because access is denied.",
            "ERROR: Failed to open '<network-path>' because access is denied.",
        ],
        [
            "Unclosed single-quoted path before colon and closed path",
            "ERROR: Unclosed 'C:\\Users\\Alice\\secret failed: 'D:\\Users\\Bob\\mw3.exe' done.",
            "ERROR: Unclosed '<local-path>' done.",
        ],
        [
            "Apostrophe continuation spanning past 4096-char limit of an earlier unclosed quote",
            `ERROR: '\\\\nas01\\share ${"a".repeat(4070)} '\\\\nas02\\O' Connor\\mw3.exe' done.`,
            "ERROR: '<network-path>' done.",
        ],
    ];

    githubResponder();
    for (let index = 0; index < cases.length; index++) {
        const [name, input, expected] = cases[index];
        const response = await onRequestPost({
            request: crashRequest({
                report_id: `redact-case-${index}`,
                logs: { launcher: input },
            }),
            env: environment,
        });
        assert.equal(response.status, 200, name);
        const archived = JSON.parse(archivedReports[index][7]);
        assert.equal(archived.logs.launcher, expected, name);
    }
});

test("bounds scanning time on adversarial repeated unclosed single-quoted paths while redacting later paths", async () => {
    githubResponder();
    const driveNoise = " 'C:\\Users\\Alice ".repeat(1500);
    const uncNoise = " '\\\\nas01\\secret\\share ".repeat(1200);
    const longSingleLine = `${driveNoise}\n${uncNoise}\n'C:\\Games\\mw3.exe' failed: James' policy 'D:\\Users\\O'Connor\\log.txt' done.`;
    assert.ok(longSingleLine.length < 64 * 1024);

    const started = performance.now();
    const response = await onRequestPost({
        request: crashRequest({
            report_id: "adversarial-bounded-1",
            logs: { launcher: longSingleLine },
        }),
        env: environment,
    });
    const elapsedMs = performance.now() - started;

    assert.equal(response.status, 200);
    assert.ok(elapsedMs < 1000, `Expected bounded redaction under 1000ms, got ${elapsedMs}ms`);
    const archived = JSON.parse(archivedReports[0][7]);
    assert.ok(!archived.logs.launcher.includes("Alice"));
    assert.ok(!archived.logs.launcher.includes("nas01"));
    assert.ok(!archived.logs.launcher.includes("O'Connor"));
    assert.ok(
        archived.logs.launcher.endsWith(
            "'<local-path>' failed: James' policy '<local-path>' done.",
        ),
    );

    const colonUncChunk = `${" '\\\\".repeat(1020)}:`;
    const colonUncLog = `${colonUncChunk.repeat(16)}\n'\\\\nas01\\secret\\mw3.exe' failed.`;
    assert.ok(colonUncLog.length <= 64 * 1024);
    const colonStarted = performance.now();
    const colonResponse = await onRequestPost({
        request: crashRequest({
            report_id: "adversarial-bounded-2",
            logs: { launcher: colonUncLog, native_crash: colonUncLog },
        }),
        env: environment,
    });
    const colonElapsedMs = performance.now() - colonStarted;

    assert.equal(colonResponse.status, 200);
    assert.ok(
        colonElapsedMs < 150,
        `Expected colon-terminated UNC redaction under 150ms, got ${colonElapsedMs}ms`,
    );
    const colonArchived = JSON.parse(archivedReports[1][7]);
    assert.ok(!colonArchived.logs.launcher.includes("nas01"));
    assert.ok(colonArchived.logs.launcher.endsWith("'<network-path>' failed."));
});

// Records the title and body of the issue the service creates.
function recordCreatedIssue() {
    githubResponder();
    const baseFetch = globalThis.fetch;
    const created = {};
    globalThis.fetch = async (url, options) => {
        const body = JSON.parse(options.body);
        if (body.query.includes("createIssue")) {
            created.title = body.variables.title;
            created.body = body.variables.body;
        }
        return baseFetch(url, options);
    };
    return created;
}

const PROBLEMS_LOG = "[12.5] E mw3: video memory full: used 5900 MiB of 5990 MiB budget\n";

test("accepts a clean-exit report that carries a problems log, titled Problems", async () => {
    const created = recordCreatedIssue();
    const response = await onRequestPost({
        request: crashRequest({
            exit_code: 0,
            failure_summary: "mw3: video memory full: used 5900 MiB of 5990 MiB budget",
            logs: { native_run: "RUN_LOG_SENTINEL\n", native_problems: PROBLEMS_LOG },
        }),
        env: environment,
    });
    assert.equal(response.status, 200);
    assert.ok(created.title.startsWith("Problems (remaster, exit 0): "));
    const problemsAt = created.body.indexOf("#### Game problems (mw3-problems.log)");
    const runAt = created.body.indexOf("#### Native run log (mw3.log)");
    assert.ok(problemsAt >= 0 && runAt > problemsAt);
});

test("rejects a clean-exit report without a problems log", async () => {
    for (const logs of [
        { native_run: "RUN_LOG\n" },
        { native_run: "RUN_LOG\n", native_problems: " \n\t" },
        // Only the setup header (level I), as a clean run's problems log holds.
        {
            native_run: "RUN_LOG\n",
            native_problems:
                "[0.512] I mw3: header resolution=1920x1080\n[0.512] I mw3: header hdr=0\n",
        },
        // Plain text without the game's stamp.
        { native_run: "RUN_LOG\n", native_problems: "something went wrong\nW not stamped\n" },
    ]) {
        githubResponder();
        const response = await onRequestPost({
            request: crashRequest({ exit_code: 0, logs }),
            env: environment,
        });
        assert.equal(response.status, 400);
        assert.equal(archivedReports.length, 0);
    }
});

test("lists the problems log first in a crash issue and on the admin page", async () => {
    const created = recordCreatedIssue();
    const response = await onRequestPost({
        request: crashRequest({
            logs: { native_crash: "CRASH_SENTINEL\n", native_problems: PROBLEMS_LOG },
        }),
        env: environment,
    });
    assert.equal(response.status, 200);
    assert.ok(created.title.startsWith("Crash (remaster, exit 7): "));
    assert.ok(
        created.body.indexOf("#### Game problems") <
            created.body.indexOf("#### Native crash details"),
    );

    const { token } = await createAdminAccess();
    const report = JSON.parse(archivedReports[0][7]);
    const row = {
        report_id: report.report_id,
        created_utc: "2026-11-26T13:00:00Z",
        stored_utc: "2026-11-26T13:01:00Z",
        mode: report.mode,
        exit_code: report.exit_code,
        failure_summary: report.failure_summary,
        crash_fingerprint: "deadbeef",
        report_json: JSON.stringify(report),
    };
    const adminDb = {
        prepare: (query) => ({
            bind: () => ({ first: async () => (query.includes("WHERE report_id") ? row : null) }),
        }),
    };
    const detail = await getAdminCrashReports({
        request: new Request(
            `https://corecritical.dev/admin/crash-reports?id=${report.report_id}`,
            { headers: { "cf-access-jwt-assertion": token } },
        ),
        env: { ...adminEnvironment, CRASH_REPORT_DB: adminDb },
    });
    const html = await detail.text();
    assert.equal(detail.status, 200);
    assert.ok(html.indexOf("Game problems") < html.indexOf("Native crash details"));
});

test("keeps only the allowed report header fields, bounded and redacted", async () => {
    const created = recordCreatedIssue();
    const response = await onRequestPost({
        request: crashRequest({
            header: {
                vulkan_device: "NVIDIA GeForce RTX 3060 Laptop GPU",
                vulkan_api_version: "1.3.289",
                vulkan_driver_version: "566.36",
                heaps: [
                    {
                        index: 0,
                        size_bytes: 6283067392,
                        budget_bytes: 5990000000,
                        device_local: true,
                    },
                    { index: 1, size_bytes: "big", budget_bytes: -1, extra: "MUST_NOT_BE_STORED" },
                    { index: 2, size_bytes: 1024 },
                    ...Array.from({ length: 20 }, (_, index) => ({
                        index,
                        size_bytes: 1,
                        budget_bytes: 1,
                    })),
                ],
                resolution: "2560x1080",
                window_mode: "Borderless",
                refresh_hz: 144,
                hdr: false,
                pack_texture_bytes: [
                    { id: "C:\\Users\\Jane Doe\\packs\\hd-mechs", bytes: 3741319168 },
                    ...Array.from({ length: 70 }, (_, index) => ({ id: `p${index}`, bytes: 1 })),
                ],
                input_devices: ["Xbox Controller", 42, "x".repeat(200)],
                serial_number: "MUST_NOT_BE_STORED",
            },
        }),
        env: environment,
    });
    assert.equal(response.status, 200);
    const header = JSON.parse(archivedReports[0][7]).header;
    assert.equal(header.vulkan_device, "NVIDIA GeForce RTX 3060 Laptop GPU");
    assert.equal(header.vulkan_api_version, "1.3.289");
    assert.equal(header.vulkan_driver_version, "566.36");
    // Only the first 16 entries are read; the two incomplete ones among them are dropped.
    assert.equal(header.heaps.length, 14);
    assert.deepEqual(header.heaps[0], {
        index: 0,
        size_bytes: 6283067392,
        budget_bytes: 5990000000,
        device_local: true,
    });
    // The entries with a bad or missing size or budget are dropped whole.
    assert.deepEqual(header.heaps[1], { index: 0, size_bytes: 1, budget_bytes: 1 });
    assert.equal(header.resolution, "2560x1080");
    assert.equal(header.window_mode, "Borderless");
    assert.equal(header.refresh_hz, 144);
    assert.equal(header.hdr, false);
    assert.equal(header.pack_texture_bytes.length, 64);
    assert.ok(!header.pack_texture_bytes[0].id.includes("Jane Doe"));
    assert.ok(header.pack_texture_bytes[0].id.includes("<local-path>"));
    assert.deepEqual(header.input_devices, ["Xbox Controller", "x".repeat(80)]);
    assert.ok(!JSON.stringify(header).includes("MUST_NOT_BE_STORED"));
    assert.ok(created.body.includes('"vulkan_driver_version": "566.36"'));
});

test("drops header fields of the wrong type", async () => {
    githubResponder();
    const response = await onRequestPost({
        request: crashRequest({
            header: {
                refresh_hz: "60",
                hdr: 1,
                heaps: [1, 2],
                pack_texture_bytes: [null],
                resolution: 2560,
                input_devices: [7],
            },
        }),
        env: environment,
    });
    assert.equal(response.status, 200);
    assert.ok(!("header" in JSON.parse(archivedReports[0][7])));
});

test("stores no header key for a report without one", async () => {
    githubResponder();
    const response = await onRequestPost({ request: crashRequest(), env: environment });
    assert.equal(response.status, 200);
    assert.ok(!("header" in JSON.parse(archivedReports[0][7])));
});
