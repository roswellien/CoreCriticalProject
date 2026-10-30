const ACCESS_KEY_CACHE_MS = 5 * 60 * 1000;
let accessKeyCache = null;

function decodeBase64Url(value) {
    const normalized = value.replace(/-/g, "+").replace(/_/g, "/");
    const bytes = atob(normalized + "=".repeat((4 - (normalized.length % 4)) % 4));
    return Uint8Array.from(bytes, (character) => character.charCodeAt(0));
}

function decodeJsonPart(value) {
    return JSON.parse(new TextDecoder().decode(decodeBase64Url(value)));
}

function isConfigured(env) {
    if (
        !env.CRASH_REPORT_ACCESS_ISSUER ||
        !env.CRASH_REPORT_ACCESS_AUD ||
        !env.CRASH_REPORT_ADMIN_EMAIL
    )
        return false;
    try {
        const issuer = new URL(env.CRASH_REPORT_ACCESS_ISSUER);
        return (
            issuer.protocol === "https:" &&
            issuer.pathname === "/" &&
            issuer.hostname.endsWith(".cloudflareaccess.com") &&
            issuer.search === "" &&
            issuer.hash === ""
        );
    } catch {
        return false;
    }
}

async function getAccessKey(issuer, keyId, now) {
    const needsRefresh =
        !accessKeyCache ||
        accessKeyCache.issuer !== issuer ||
        accessKeyCache.expiresAt <= now ||
        (!accessKeyCache.keys.has(keyId) && now - accessKeyCache.fetchedAt >= 30_000);
    if (needsRefresh) {
        const response = await fetch(`${issuer}/cdn-cgi/access/certs`, {
            headers: { accept: "application/json" },
            signal: AbortSignal.timeout(5000),
        });
        if (!response.ok) throw new Error("Cloudflare Access signing keys are unavailable.");
        const body = await response.json();
        if (!Array.isArray(body.keys))
            throw new Error("Cloudflare Access returned invalid signing keys.");
        accessKeyCache = {
            issuer,
            fetchedAt: now,
            expiresAt: now + ACCESS_KEY_CACHE_MS,
            keys: new Map(
                body.keys
                    .filter((key) => key.kid && key.kty === "RSA" && key.alg === "RS256")
                    .map((key) => [key.kid, key]),
            ),
        };
    }
    return accessKeyCache.keys.get(keyId) ?? null;
}

export async function authorizeCrashReportAdmin(request, env) {
    if (!isConfigured(env))
        return { ok: false, status: 503, message: "Admin report access is not configured." };

    const token = request.headers.get("cf-access-jwt-assertion");
    if (!token || token.length > 16_384)
        return { ok: false, status: 401, message: "Cloudflare Access authentication is required." };
    const parts = token.split(".");
    if (parts.length !== 3)
        return { ok: false, status: 403, message: "Cloudflare Access authentication is invalid." };

    try {
        const header = decodeJsonPart(parts[0]);
        const payload = decodeJsonPart(parts[1]);
        if (
            header.alg !== "RS256" ||
            typeof header.kid !== "string" ||
            payload.iss !== env.CRASH_REPORT_ACCESS_ISSUER ||
            !(Array.isArray(payload.aud) ? payload.aud : [payload.aud]).includes(
                env.CRASH_REPORT_ACCESS_AUD,
            )
        ) {
            return {
                ok: false,
                status: 403,
                message: "Cloudflare Access authentication is invalid.",
            };
        }
        const now = Math.floor(Date.now() / 1000);
        if (
            !Number.isFinite(payload.exp) ||
            payload.exp <= now ||
            (payload.nbf != null && (!Number.isFinite(payload.nbf) || payload.nbf > now)) ||
            (payload.iat != null && (!Number.isFinite(payload.iat) || payload.iat > now + 60))
        ) {
            return {
                ok: false,
                status: 403,
                message: "Cloudflare Access authentication has expired or is not yet valid.",
            };
        }
        if (
            typeof payload.email !== "string" ||
            payload.email.toLowerCase() !== env.CRASH_REPORT_ADMIN_EMAIL.trim().toLowerCase()
        ) {
            return {
                ok: false,
                status: 403,
                message: "This account is not allowed to view crash reports.",
            };
        }

        const jwk = await getAccessKey(env.CRASH_REPORT_ACCESS_ISSUER, header.kid, Date.now());
        if (!jwk)
            return {
                ok: false,
                status: 403,
                message: "Cloudflare Access authentication is invalid.",
            };
        const key = await crypto.subtle.importKey(
            "jwk",
            jwk,
            { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" },
            false,
            ["verify"],
        );
        const signatureValid = await crypto.subtle.verify(
            "RSASSA-PKCS1-v1_5",
            key,
            decodeBase64Url(parts[2]),
            new TextEncoder().encode(`${parts[0]}.${parts[1]}`),
        );
        if (!signatureValid)
            return {
                ok: false,
                status: 403,
                message: "Cloudflare Access authentication is invalid.",
            };
        return { ok: true, email: payload.email };
    } catch {
        return {
            ok: false,
            status: 403,
            message: "Cloudflare Access authentication could not be verified.",
        };
    }
}
