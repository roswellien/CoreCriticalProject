import { validateHeader } from "../_lib/crash-report-header.js";
import { LOG_LABELS, LOG_ORDER } from "../_lib/crash-report-logs.js";

const MAX_REQUEST_BYTES = 256 * 1024;
const MAX_ISSUE_BODY_CHARS = 48_000;
const MAX_ISSUE_REPORT_CHARS = 20_000;
const MAX_FULL_LOG_REPEATS = 3;
const MAX_QUOTED_PATH_CHARS = 4096;
const DEFAULT_DAILY_ISSUE_LIMIT = 20;
const ARCHIVE_SAVE_FAILED_LOG =
    "Crash report archive save to table crash_report_archive failed; check that website/migrations/0002_crash_report_archive.sql is applied:";
const ARCHIVE_FAILED_NOTE =
    "Not saved to the admin archive: the archive save failed (check migration 0002).";
const GENERIC_FAILURES = [
    "The launch or game ended unexpectedly. Open Logs for details.",
    "No launch details were recorded.",
    "No specific failure was recorded.",
];

const MIN_INT32 = -2_147_483_648;
const MAX_INT32 = 2_147_483_647;

// Only the legacy host fault record may retain a module basename and numeric suffix.
const NATIVE_MODULE_SUFFIX_LINE =
    /^(HOST EXCEPTION (?:0x)?[0-9a-f]{1,8} at )((?:[A-Z]:[\\/]|\\\\)[^\r\n\t"<>|:]{1,1024}?)(\.(?:exe|dll)[ \t]*\+0x[0-9a-f]{1,16}(?: \(access [0-9]+ address (?:0x)?[0-9a-f]{1,16}\))?)(?=\r?$)/gim;

const OPENING_QUOTE_DELIMITERS = new Set(["(", "[", "{", "=", ",", ";", ":", '"', "`", "<"]);
const CLOSING_QUOTE_DELIMITERS = new Set([
    ".",
    ",",
    ";",
    ":",
    "!",
    "?",
    ")",
    "]",
    "}",
    '"',
    "`",
    ">",
]);
const DISALLOWED_PATH_CHARS = new Set(["\r", "\n", "\t", '"', "<", ">", "|"]);
const TRAILING_WORD_STOP_CHARS = new Set([
    "/",
    "\\",
    ":",
    "=",
    "(",
    "[",
    "{",
    ",",
    ";",
    "!",
    "?",
    '"',
    "`",
]);
const CONTINUATION_AFTER_CHARS = new Set([" ", ".", ",", ";", "!", "?", ")", "]"]);
const EXT_DISALLOWED_FOLLOWERS = new Set(["'", "=", ":", ")", "]", "}", '"', "`", ">"]);

function isWhiteSpace(c) {
    return /\s/.test(c);
}

function isAsciiLetter(c) {
    const code = c.charCodeAt(0);
    return (code >= 65 && code <= 90) || (code >= 97 && code <= 122);
}

function isAsciiLetterOrDigit(c) {
    const code = c.charCodeAt(0);
    return (code >= 65 && code <= 90) || (code >= 97 && code <= 122) || (code >= 48 && code <= 57);
}

function isDrivePathStart(text, start) {
    return (
        start + 2 < text.length &&
        isAsciiLetter(text[start]) &&
        text[start + 1] === ":" &&
        (text[start + 2] === "\\" || text[start + 2] === "/")
    );
}

function isUncPathStart(text, start) {
    return (
        start + 2 < text.length &&
        text[start] === "\\" &&
        text[start + 1] === "\\" &&
        !DISALLOWED_PATH_CHARS.has(text[start + 2]) &&
        text[start + 2] !== "'"
    );
}

function isQuotedPathOpeningBoundary(text, quoteIndex) {
    if (quoteIndex === 0) return true;
    const prev = text[quoteIndex - 1];
    return isWhiteSpace(prev) || OPENING_QUOTE_DELIMITERS.has(prev);
}

function isQuotedPathClosingBoundary(text, quoteIndex) {
    if (quoteIndex + 1 >= text.length) return true;
    const next = text[quoteIndex + 1];
    return isWhiteSpace(next) || CLOSING_QUOTE_DELIMITERS.has(next);
}

function hasFileExtension(text, segmentStart, segmentEnd) {
    let lastDot = -1;
    for (let i = segmentEnd - 1; i >= segmentStart; i--) {
        if (text[i] === ".") {
            lastDot = i;
            break;
        }
    }
    if (lastDot <= segmentStart || lastDot >= segmentEnd - 1) return false;
    const extLength = segmentEnd - lastDot - 1;
    if (extLength > 8) return false;
    let hasLetter = false;
    for (let i = lastDot + 1; i < segmentEnd; i++) {
        const c = text[i];
        if (!isAsciiLetterOrDigit(c)) return false;
        if (isAsciiLetter(c)) hasLetter = true;
    }
    return hasLetter;
}

function isMixedForwardSlashContinuation(text, lastSlash, end, slashCount) {
    if (slashCount <= 0 || lastSlash + 1 >= end) return false;
    if (hasFileExtension(text, lastSlash + 1, end)) return true;
    if (slashCount < 2) return false;
    for (let i = lastSlash + 1; i < end; i++) {
        if (isWhiteSpace(text[i])) return false;
    }
    return true;
}

function findContinuationClosingQuote(
    text,
    start,
    expectedSeparator,
    requirePathSeparator,
    allowWhitespace,
    scanLimit,
) {
    let sawSeparator = false;
    let forwardSlashCount = 0;
    let lastForwardSlash = -1;
    for (let i = start; i < scanLimit; i++) {
        const c = text[i];
        if (DISALLOWED_PATH_CHARS.has(c) || c === ":") return -1;
        if (!allowWhitespace && isWhiteSpace(c)) return -1;
        if (c === expectedSeparator || c === "\\") {
            sawSeparator = true;
        } else if (c === "/") {
            forwardSlashCount++;
            lastForwardSlash = i;
        }
        if (c !== "'") continue;

        if (isQuotedPathClosingBoundary(text, i)) {
            if (!requirePathSeparator || sawSeparator) return i;
            return isMixedForwardSlashContinuation(text, lastForwardSlash, i, forwardSlashCount)
                ? i
                : -1;
        }

        // An opening quote after a delimiter starts a separate quoted token,
        // not a continuation.
        if (isQuotedPathOpeningBoundary(text, i)) return -1;
    }
    return -1;
}

function scanSingleTrailingWordQuote(text, start, scanLimit) {
    if (start >= scanLimit) return -1;
    let length = 0;
    for (let i = start; i < scanLimit; i++) {
        const c = text[i];
        if (DISALLOWED_PATH_CHARS.has(c) || isWhiteSpace(c)) return -1;
        if (TRAILING_WORD_STOP_CHARS.has(c)) return -1;
        if (c === "'") {
            if (!isQuotedPathClosingBoundary(text, i)) {
                length++;
                continue;
            }
            return length > 0 ? i : -1;
        }
        length++;
    }
    return -1;
}

// Keep scanning past apostrophes followed by whitespace or punctuation inside a path
// (such as "Players' Choice\mw3.exe" or "v1'.txt") without crossing into another quoted token.
function continuePastInternalApostrophe(text, quoteIndex, expectedSeparator, scanLimit) {
    if (quoteIndex + 1 >= scanLimit) return -1;

    const after = text[quoteIndex + 1];
    if (CONTINUATION_AFTER_CHARS.has(after)) {
        const candidate = findContinuationClosingQuote(
            text,
            quoteIndex + 1,
            expectedSeparator,
            true,
            true,
            scanLimit,
        );
        if (candidate >= 0) return candidate;
    }

    if (
        (after === "." || after === ",") &&
        quoteIndex + 2 < scanLimit &&
        !isWhiteSpace(text[quoteIndex + 2]) &&
        !EXT_DISALLOWED_FOLLOWERS.has(text[quoteIndex + 2])
    ) {
        const candidate = findContinuationClosingQuote(
            text,
            quoteIndex + 2,
            expectedSeparator,
            false,
            false,
            scanLimit,
        );
        if (candidate >= 0) return candidate;
    }

    if (after === " ") {
        const componentEnd = scanSingleTrailingWordQuote(text, quoteIndex + 2, scanLimit);
        if (componentEnd >= 0) return componentEnd;
    }

    return -1;
}

function findSingleQuotedPathClose(
    text,
    pathStart,
    initialScanIndex,
    expectedSeparator,
    scannedNoCloseUntil,
) {
    const scanLimit = Math.min(text.length, pathStart + MAX_QUOTED_PATH_CHARS);
    let index = Math.max(initialScanIndex, scannedNoCloseUntil);
    while (index < scanLimit) {
        const c = text[index];
        if (DISALLOWED_PATH_CHARS.has(c)) {
            return { closeQuote: -1, noCloseBefore: index, scannedNoCloseUntil: index };
        }
        if (c !== "'") {
            index++;
            continue;
        }

        if (!isQuotedPathClosingBoundary(text, index)) {
            index++;
            continue;
        }

        // Extend continuation lookahead past scanLimit so an apostrophe near the
        // 4096-char boundary cannot truncate a following valid quoted path mid-segment.
        let closeQuote = index;
        while (true) {
            const continuationLimit = Math.min(text.length, closeQuote + MAX_QUOTED_PATH_CHARS);
            const continuedQuote = continuePastInternalApostrophe(
                text,
                closeQuote,
                expectedSeparator,
                continuationLimit,
            );
            if (continuedQuote < 0) {
                return { closeQuote, noCloseBefore: -1, scannedNoCloseUntil: -1 };
            }
            closeQuote = continuedQuote;
        }
    }

    return {
        closeQuote: -1,
        noCloseBefore: scanLimit === text.length ? text.length : -1,
        scannedNoCloseUntil: scanLimit,
    };
}

function scrubSingleQuotedPaths(text) {
    const parts = [];
    let copyFrom = 0;
    let index = 0;
    let noCloseBefore = -1;
    let scannedNoCloseUntil = -1;
    while (index < text.length) {
        if (text[index] !== "'" || !isQuotedPathOpeningBoundary(text, index)) {
            index++;
            continue;
        }

        const pathStart = index + 1;
        let replacement = null;
        let expectedSeparator = "\\";
        if (isDrivePathStart(text, pathStart)) {
            replacement = "'<local-path>'";
            expectedSeparator = text[pathStart + 2] === "/" ? "/" : "\\";
        } else if (isUncPathStart(text, pathStart)) {
            replacement = "'<network-path>'";
        }

        if (replacement === null) {
            index++;
            continue;
        }

        if (pathStart < noCloseBefore) {
            index++;
            continue;
        }

        const result = findSingleQuotedPathClose(
            text,
            pathStart,
            pathStart + 3,
            expectedSeparator,
            scannedNoCloseUntil,
        );
        if (result.closeQuote < 0) {
            if (result.noCloseBefore > noCloseBefore) noCloseBefore = result.noCloseBefore;
            if (result.scannedNoCloseUntil > scannedNoCloseUntil) {
                scannedNoCloseUntil = result.scannedNoCloseUntil;
            }
            index++;
            continue;
        }

        parts.push(text.slice(copyFrom, index), replacement);
        copyFrom = result.closeQuote + 1;
        index = copyFrom;
    }

    if (parts.length === 0) return text;
    parts.push(text.slice(copyFrom));
    return parts.join("");
}

function redactPaths(value) {
    let text = value.replace(NATIVE_MODULE_SUFFIX_LINE, (_full, prefix, pathPart, suffix) => {
        const token = pathPart.startsWith("\\\\") ? "<network-path>" : "<local-path>";
        const lastSep = Math.max(pathPart.lastIndexOf("\\"), pathPart.lastIndexOf("/"));
        const stem = lastSep >= 0 ? pathPart.slice(lastSep + 1) : pathPart;
        if (/^[A-Za-z0-9._-]{1,64}$/.test(stem)) {
            return `${prefix}${token}/${stem}${suffix}`;
        }
        return `${prefix}${token}${suffix}`;
    });
    text = scrubSingleQuotedPaths(text);
    return text
        .replace(/(?<![A-Za-z0-9])[A-Za-z]:[\\/][^\r\n\t"<>|]*/g, "<local-path>")
        .replace(/\\\\[^\r\n\t"<>|]+/g, "<network-path>");
}

function field(source, name) {
    const camelName = name[0].toLowerCase() + name.slice(1);
    return source?.[camelName] ?? source?.[name];
}

function hardwareField(source, name) {
    return field(source, name);
}

function json(body, status = 200) {
    return new Response(JSON.stringify(body), {
        status,
        headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
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
    const source =
        hardware && typeof hardware === "object" && !Array.isArray(hardware) ? hardware : {};
    const sourceProcessors = hardwareField(source, "Processors");
    const processors = Array.isArray(sourceProcessors)
        ? sourceProcessors.slice(0, 8).map((processor) => ({
              Manufacturer: boundedText(hardwareField(processor, "Manufacturer"), 120),
              Model: boundedText(hardwareField(processor, "Model"), 200),
              PhysicalCores: boundedCount(hardwareField(processor, "PhysicalCores")),
              LogicalProcessors: boundedCount(hardwareField(processor, "LogicalProcessors")),
          }))
        : [];
    const memory = hardwareField(source, "Memory");
    const sourceMemory =
        memory && typeof memory === "object" && !Array.isArray(memory) ? memory : {};
    const sourceModules = hardwareField(sourceMemory, "Modules");
    const modules = Array.isArray(sourceModules)
        ? sourceModules.slice(0, 32).map((module) => ({
              CapacityBytes: boundedBytes(hardwareField(module, "CapacityBytes")),
              Type: boundedText(hardwareField(module, "Type"), 80),
              ConfiguredSpeedMhz: boundedCount(hardwareField(module, "ConfiguredSpeedMhz")),
          }))
        : [];
    const sourceGraphicsAdapters = hardwareField(source, "GraphicsAdapters");
    const graphicsAdapters = Array.isArray(sourceGraphicsAdapters)
        ? sourceGraphicsAdapters.slice(0, 8).map((adapter) => ({
              Name: boundedText(hardwareField(adapter, "Name"), 200) ?? "Unknown graphics adapter",
              DedicatedVideoMemoryBytes: boundedBytes(
                  hardwareField(adapter, "DedicatedVideoMemoryBytes"),
              ),
              SharedSystemMemoryBytes: boundedBytes(
                  hardwareField(adapter, "SharedSystemMemoryBytes"),
              ),
              DriverVersion: boundedText(hardwareField(adapter, "DriverVersion"), 120),
              DriverDate: boundedText(hardwareField(adapter, "DriverDate"), 40),
          }))
        : [];

    return {
        Processors: processors,
        Memory: {
            TotalBytes: boundedBytes(hardwareField(sourceMemory, "TotalBytes")),
            Modules: modules,
        },
        GraphicsAdapters: graphicsAdapters,
    };
}

function archivedOnlyResponse(reportId) {
    return json(
        { report_id: reportId.slice(0, 8), duplicate: false, overflow: false, archived_only: true },
        202,
    );
}

function deliveryFailedResponse() {
    return json(
        { error: "The report service could not save this crash report. Try again later." },
        502,
    );
}

// Used when the report can't reach GitHub. A report is only "accepted" if the
// archive kept a copy; otherwise the launcher must hear that it was not saved.
function undeliveredResponse(archivedReportId) {
    return archivedReportId ? archivedOnlyResponse(archivedReportId) : deliveryFailedResponse();
}

function validateEnvironment(env) {
    const repository = env.CRASH_REPORT_REPOSITORY;
    const token = env.GITHUB_TOKEN;
    const overflowIssueNumber = Number(env.CRASH_REPORT_OVERFLOW_ISSUE_NUMBER);
    const configuredLimit = Number(env.CRASH_REPORT_DAILY_ISSUE_LIMIT || DEFAULT_DAILY_ISSUE_LIMIT);
    if (
        !repository ||
        !/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(repository) ||
        !token ||
        !Number.isSafeInteger(overflowIssueNumber) ||
        overflowIssueNumber < 1 ||
        !Number.isSafeInteger(configuredLimit) ||
        configuredLimit < 1 ||
        configuredLimit > 1000 ||
        !env.CRASH_REPORT_DB?.prepare
    ) {
        throw new Error("Crash reporting is not configured on the server.");
    }
    return {
        owner: repository.split("/")[0],
        name: repository.split("/")[1],
        token,
        overflowIssueNumber,
        dailyIssueLimit: configuredLimit,
        database: env.CRASH_REPORT_DB,
    };
}

function validateReport(report) {
    if (
        !report ||
        report.format_version !== 1 ||
        typeof report.failure_summary !== "string" ||
        report.failure_summary.trim().length === 0 ||
        report.failure_summary.length > 2000 ||
        typeof report.mode !== "string" ||
        report.mode.trim().length === 0 ||
        report.mode.length > 80 ||
        !Number.isInteger(report.exit_code) ||
        report.exit_code < MIN_INT32 ||
        report.exit_code > MAX_INT32 ||
        !report.logs ||
        typeof report.logs !== "object" ||
        Array.isArray(report.logs)
    ) {
        throw new Error("The crash report format is invalid.");
    }

    const settings = {};
    for (const key of [
        "EngineMode",
        "WindowMode",
        "AntiAliasing",
        "D7VkResolution",
        "D7VkAntiAliasing",
        "D7VkAnisotropicFiltering",
    ]) {
        const value = field(report.settings, key);
        if (typeof value === "string") settings[key] = redactPaths(value.slice(0, 80));
    }
    for (const key of ["Width", "Height", "AnisotropicFiltering", "DrawDistance", "FogDistance"]) {
        const value = field(report.settings, key);
        if (Number.isInteger(value)) settings[key] = value;
    }
    for (const key of [
        "LocalCdAudio",
        "InstantReplay",
        "PerformanceMonitor",
        "RenderThread",
        "D7VkAiTextures",
    ]) {
        const value = field(report.settings, key);
        if (typeof value === "boolean") settings[key] = value;
    }

    const logs = {};
    for (const name of LOG_ORDER) {
        const value = report.logs[name];
        if (value !== undefined && typeof value !== "string")
            throw new Error("The crash report logs are invalid.");
        if (value) logs[name] = redactPaths(value.slice(-64 * 1024));
    }
    // A clean exit is only worth a report when the game logged problems during play;
    // without them it would be noise in the crash-report repository.
    const hasProblems =
        typeof logs.native_problems === "string" && logs.native_problems.trim().length > 0;
    if (report.exit_code === 0 && !hasProblems)
        throw new Error("The crash report format is invalid.");
    const packs = Array.isArray(report.packs)
        ? report.packs.slice(0, 64).map((pack) => {
              const rawId = field(pack, "Id");
              const rawVersion = field(pack, "Version");
              const rawSchema = field(pack, "SchemaVersion") ?? pack?.schema_version;
              const rawEnabled = field(pack, "IsEnabled") ?? pack?.enabled;
              const rawPriority = field(pack, "Priority");
              return {
                  id: typeof rawId === "string" ? redactPaths(rawId.slice(0, 120)) : "",
                  version:
                      typeof rawVersion === "string" ? redactPaths(rawVersion.slice(0, 80)) : "",
                  schema_version: Number.isInteger(rawSchema) ? rawSchema : 0,
                  enabled: rawEnabled === true,
                  priority: Number.isInteger(rawPriority) ? rawPriority : 0,
              };
          })
        : [];
    const reportId =
        typeof report.report_id === "string" && /^[a-zA-Z0-9-]{1,64}$/.test(report.report_id)
            ? report.report_id
            : crypto.randomUUID();
    const rawSourceCommit = report.runtime_source_commit ?? report.runtimeSourceCommit;
    const runtimeSourceCommit =
        typeof rawSourceCommit === "string" && rawSourceCommit.trim().length > 0
            ? redactPaths(rawSourceCommit.trim().slice(0, 40))
            : undefined;
    const header = validateHeader(report.header, redactPaths);
    const hasHeader = Object.keys(header).length > 0;
    const validated = {
        format_version: 1,
        report_id: reportId,
        created_utc: typeof report.created_utc === "string" ? report.created_utc.slice(0, 40) : "",
        launcher_version:
            typeof report.launcher_version === "string"
                ? redactPaths(report.launcher_version.slice(0, 80))
                : "",
        runtime_version:
            typeof report.runtime_version === "string"
                ? redactPaths(report.runtime_version.slice(0, 80))
                : "",
        ...(runtimeSourceCommit ? { runtime_source_commit: runtimeSourceCommit } : {}),
        mode: redactPaths(report.mode.slice(0, 80)),
        exit_code: report.exit_code,
        os: typeof report.os === "string" ? redactPaths(report.os.slice(0, 200)) : "",
        architecture:
            typeof report.architecture === "string"
                ? redactPaths(report.architecture.slice(0, 80))
                : "",
        dotnet_runtime:
            typeof report.dotnet_runtime === "string"
                ? redactPaths(report.dotnet_runtime.slice(0, 120))
                : "",
        hardware: validateHardware(report.hardware),
        // Left out when empty so reports from older launchers are stored exactly as before.
        ...(hasHeader ? { header } : {}),
        failure_summary: redactPaths(report.failure_summary.slice(0, 2000)),
        settings,
        packs,
        logs,
    };
    return validated;
}

function normalizeReason(reason) {
    // The native runtime logs raw fault and module-base addresses for debugging. Ignore those
    // when the crashing instruction has a stable address relative to the executable.
    const nativeFault =
        /^(mw3(?:launcher|pm)?: crashed: exception 0x[0-9a-f]{1,8}) at (?:0x)?[0-9a-f]{1,16} module base (?:0x)?[0-9a-f]{1,16} (RVA 0x[0-9a-f]{1,16})(?: \(access violation: ([a-z]+) \([0-9]+\) target (?:0x)?[0-9a-f]{1,16}\))?$/i.exec(
            reason.trim(),
        );
    if (nativeFault) return nativeFault.slice(1).filter(Boolean).join(" ").toLowerCase();

    return reason
        .toLowerCase()
        .replace(/0x[0-9a-f]+/gi, "<address>")
        .replace(/\s+/g, " ")
        .trim();
}

function isGenericFailure(report) {
    const message = normalizeReason(report.failure_summary).replace(/[.!?]+$/, "");
    return GENERIC_FAILURES.some(
        (summary) => message === normalizeReason(summary).replace(/[.!?]+$/, ""),
    );
}

async function fingerprint(report) {
    const signature = JSON.stringify([
        normalizeReason(report.mode),
        report.exit_code,
        normalizeReason(report.failure_summary),
    ]);
    const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(signature));
    return [...new Uint8Array(digest)].map((value) => value.toString(16).padStart(2, "0")).join("");
}

async function github(token, query, variables) {
    const response = await fetch("https://api.github.com/graphql", {
        method: "POST",
        headers: {
            authorization: `Bearer ${token}`,
            "content-type": "application/json",
            "user-agent": "Core-Critical-Crash-Report-Service",
            "x-github-api-version": "2022-11-28",
        },
        body: JSON.stringify({ query, variables }),
    });
    const body = await response.json();
    if (!response.ok || body.errors?.length) {
        const detail =
            body.errors?.map((error) => error.message).join("; ") ||
            `GitHub returned HTTP ${response.status}.`;
        throw new Error(detail);
    }
    return body.data;
}

function issueBody(
    report,
    crashFingerprint,
    { includeLogs = true, overflow = false, archiveFailed = false } = {},
) {
    const marker = crashFingerprint ? `<!-- crash-fingerprint:${crashFingerprint} -->\n\n` : "";
    const reportLogs = includeLogs ? report.logs : {};
    const safeReport = { ...report };
    safeReport.packs = [...report.packs];
    delete safeReport.logs;
    const serializeReport = (value) =>
        JSON.stringify(value, null, 2).replace(/```/g, "\\u0060\\u0060\\u0060");
    let reportText = serializeReport(safeReport);
    let reportDetailsOmitted = false;
    while (reportText.length > MAX_ISSUE_REPORT_CHARS && safeReport.packs.length > 0) {
        safeReport.packs.pop();
        reportDetailsOmitted = true;
        reportText = serializeReport(safeReport);
    }
    if (reportText.length > MAX_ISSUE_REPORT_CHARS) {
        reportDetailsOmitted = true;
        reportText = serializeReport({
            format_version: safeReport.format_version,
            report_id: safeReport.report_id,
            mode: safeReport.mode,
            exit_code: safeReport.exit_code,
            failure_summary: safeReport.failure_summary,
            metadata_omitted: true,
        });
    }
    const note = overflow
        ? "Daily new-issue limit reached. This report is in the overflow queue."
        : "Crash report sent with the player's report setting or one-time approval.";
    const omittedMetadataNote = reportDetailsOmitted
        ? "\n\nSome report details were omitted to fit GitHub's issue size limit."
        : "";
    // Pages Functions logs are not stored, so the issue is the only place the
    // maintainer will reliably see that the archive is failing.
    const archiveNote = archiveFailed ? `\n${ARCHIVE_FAILED_NOTE}` : "";
    const header = `${marker}${note}\nReport ID: ${report.report_id}${archiveNote}\n\n### Report details\n\n\`\`\`json\n${reportText}\n\`\`\`${omittedMetadataNote}`;
    if (!includeLogs)
        return boundIssueBody(
            `${header}\n\nLog excerpts were omitted for overflow or repeat-report limits.`,
        );

    const orderedKeys = [
        ...LOG_ORDER.filter((key) => key in reportLogs),
        ...Object.keys(reportLogs).filter((key) => !LOG_ORDER.includes(key)),
    ];
    const entries = orderedKeys
        .map((key) => [key, reportLogs[key]])
        .filter(([, content]) => typeof content === "string" && content.length > 0);
    if (entries.length === 0)
        return boundIssueBody(
            `${header}\n\n### Recent log excerpts\n\nNo log files were available in this report.`,
        );
    let body = `${header}\n\n### Recent log excerpts\n\n`;
    for (let index = 0; index < entries.length; index++) {
        const [name, content] = entries[index];
        const remainingEntries = entries.length - index;
        const heading = `#### ${LOG_LABELS[name] ?? name}\n\n`;
        const maxFenceRun = Math.max(
            0,
            ...Array.from(content.matchAll(/`+/g), (match) => match[0].length),
        );
        const fence = "`".repeat(Math.max(3, maxFenceRun + 1));
        const remaining =
            MAX_ISSUE_BODY_CHARS - body.length - heading.length - fence.length * 2 - 10;
        const perLogBudget =
            name === "native_crash"
                ? Math.min(
                      content.length + 128,
                      Math.max(
                          Math.floor(remaining / remainingEntries),
                          Math.min(remaining, 16_384),
                      ),
                  )
                : Math.floor(remaining / remainingEntries);
        if (perLogBudget < 128 || remaining < 128) {
            body += "Additional log excerpts omitted to fit GitHub's issue size limit.\n";
            break;
        }

        const truncationNote =
            content.length > perLogBudget
                ? "[Earlier log lines omitted to fit GitHub's issue size limit.]\n"
                : "";
        const available = Math.max(0, perLogBudget - truncationNote.length);
        let excerpt = content;
        if (excerpt.length > available) {
            excerpt = excerpt.slice(-available);
            const firstNewline = excerpt.indexOf("\n");
            if (firstNewline >= 0) excerpt = excerpt.slice(firstNewline + 1);
        }
        body += `${heading}${fence}text\n${truncationNote}${excerpt.trimEnd()}\n${fence}\n\n`;
    }
    return boundIssueBody(body);
}

function boundIssueBody(body) {
    return body.length > MAX_ISSUE_BODY_CHARS ? body.slice(0, MAX_ISSUE_BODY_CHARS) : body;
}

async function reopenIfClosed(token, issue) {
    if (issue.state !== "CLOSED") return;
    await github(
        token,
        `mutation($issue:ID!) {
    updateIssue(input:{id:$issue, state:OPEN}) { issue { id state } }
  }`,
        { issue: issue.id },
    );
}

async function addReportComment(
    token,
    issue,
    report,
    crashFingerprint,
    { includeLogs = true, overflow = false, archiveFailed = false } = {},
) {
    await reopenIfClosed(token, issue);
    await github(
        token,
        `mutation($issue:ID!, $body:String!) {
    addComment(input:{subjectId:$issue, body:$body}) { commentEdge { node { id } } }
  }`,
        {
            issue: issue.id,
            body: issueBody(report, crashFingerprint, { includeLogs, overflow, archiveFailed }),
        },
    );
}

async function reserveDailyIssueSlot(config) {
    const day = new Date().toISOString().slice(0, 10);
    const row = await config.database
        .prepare(
            `
    INSERT INTO crash_issue_daily_limits (utc_day, issue_count)
    VALUES (?, 1)
    ON CONFLICT(utc_day) DO UPDATE SET issue_count = issue_count + 1
      WHERE issue_count < ?
    RETURNING issue_count
  `,
        )
        .bind(day, config.dailyIssueLimit)
        .first();
    return row !== null;
}

async function archiveReport(database, report, crashFingerprint) {
    await database
        .prepare(
            `
    INSERT OR IGNORE INTO crash_report_archive (
      report_id, created_utc, stored_utc, mode, exit_code, failure_summary, crash_fingerprint, report_json
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
  `,
        )
        .bind(
            report.report_id,
            report.created_utc,
            new Date().toISOString(),
            report.mode,
            report.exit_code,
            report.failure_summary,
            crashFingerprint,
            JSON.stringify(report),
        )
        .run();
}

async function fetchOverflowIssue(token, owner, name, number) {
    const data = await github(
        token,
        `query($owner:String!, $name:String!, $number:Int!) {
    repository(owner:$owner, name:$name) { issue(number:$number) { id url state } }
  }`,
        { owner, name, number },
    );
    return data.repository?.issue ?? null;
}

export async function onRequestPost({ request, env }) {
    if (Number(request.headers.get("content-length") || 0) > MAX_REQUEST_BYTES) {
        return json({ error: "Crash report is too large." }, 413);
    }

    let raw;
    try {
        raw = await request.text();
        if (new TextEncoder().encode(raw).length > MAX_REQUEST_BYTES)
            return json({ error: "Crash report is too large." }, 413);
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

    let crashFingerprint;
    try {
        const generic = isGenericFailure(report);
        crashFingerprint = generic ? null : await fingerprint(report);
    } catch (error) {
        console.error("Crash report fingerprint failed:", error.message);
        return deliveryFailedResponse();
    }

    // The archive is a convenience copy for the admin page; GitHub is the record.
    // A failed save (for example, migration 0002 never applied) must not stop delivery.
    let archivedReportId = null;
    try {
        await archiveReport(config.database, report, crashFingerprint);
        archivedReportId = report.report_id;
    } catch (error) {
        console.error(ARCHIVE_SAVE_FAILED_LOG, error.message);
    }
    const archiveFailed = archivedReportId === null;

    try {
        const marker = crashFingerprint ? `crash-fingerprint:${crashFingerprint}` : null;
        const searchQuery = marker
            ? `repo:${config.owner}/${config.name} is:issue in:body "${marker}"`
            : null;
        const lookup = await github(
            config.token,
            searchQuery
                ? `query($owner:String!, $name:String!, $search:String!) {
          repository(owner:$owner, name:$name) { id isPrivate }
          matched: search(query:$search, type:ISSUE, first:10) {
            nodes { ... on Issue { id url title body state comments { totalCount } } }
          }
        }`
                : `query($owner:String!, $name:String!) {
          repository(owner:$owner, name:$name) { id isPrivate }
        }`,
            searchQuery
                ? { owner: config.owner, name: config.name, search: searchQuery }
                : { owner: config.owner, name: config.name },
        );
        if (!lookup.repository?.isPrivate) {
            console.error(
                archiveFailed
                    ? "Crash report not sent: the configured GitHub repository is not private, and the archive save failed."
                    : "Crash report archived, but the configured GitHub repository is not private.",
            );
            return undeliveredResponse(archivedReportId);
        }

        const existing = marker
            ? lookup.matched?.nodes.find((issue) => issue.body?.includes(marker))
            : null;
        if (existing) {
            const includeLogs = (existing.comments?.totalCount ?? 0) < MAX_FULL_LOG_REPEATS;
            await addReportComment(config.token, existing, report, crashFingerprint, {
                includeLogs,
                archiveFailed,
            });
            return json({
                report_id: report.report_id.slice(0, 8),
                duplicate: true,
                overflow: false,
            });
        }

        if (!(await reserveDailyIssueSlot(config))) {
            const overflow = await fetchOverflowIssue(
                config.token,
                config.owner,
                config.name,
                config.overflowIssueNumber,
            );
            if (!overflow) return undeliveredResponse(archivedReportId);
            await addReportComment(config.token, overflow, report, null, {
                includeLogs: false,
                overflow: true,
                archiveFailed,
            });
            return json({
                report_id: report.report_id.slice(0, 8),
                duplicate: true,
                overflow: true,
            });
        }

        const titleReason = report.failure_summary
            .replace(/[\r\n\t]+/g, " ")
            .trim()
            .slice(0, 120);
        const suffix = crashFingerprint
            ? ` [${crashFingerprint.slice(0, 12)}]`
            : ` [${report.report_id.slice(0, 8)}]`;
        const kind = report.exit_code === 0 ? "Problems" : "Crash";
        const title = `${kind} (${report.mode}, exit ${report.exit_code}): ${titleReason}${suffix}`;
        await github(
            config.token,
            `mutation($repository:ID!, $title:String!, $body:String!) {
      createIssue(input:{repositoryId:$repository, title:$title, body:$body}) {
        issue { id url state }
      }
    }`,
            {
                repository: lookup.repository.id,
                title,
                body: issueBody(report, crashFingerprint, { archiveFailed }),
            },
        );
        return json({ report_id: report.report_id.slice(0, 8), duplicate: false, overflow: false });
    } catch (error) {
        console.error("Crash report delivery failed:", error.message);
        return undeliveredResponse(archivedReportId);
    }
}
