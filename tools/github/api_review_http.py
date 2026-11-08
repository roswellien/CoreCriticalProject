import json
import re
import urllib.error
import urllib.request
from http.client import HTTPException

import openai_automation as domain
from openai_automation_github import NoRedirect

_ENDPOINTS = {
    "openai": "https://api.openai.com/v1/responses",
    "mistral": "https://api.mistral.ai/v1/chat/completions",
}
_KEY_RE = re.compile(r"^[A-Za-z0-9_-]{1,512}$")
_XRID_RE = re.compile(r"^[A-Za-z0-9_.-]{1,128}$")
_MAX = 256 * 1024


def request(provider: str, key: str, payload: dict, *, opener=None) -> tuple[dict, str | None]:
    if provider not in _ENDPOINTS:
        domain.require(False, "api_review_http_unknown_provider")
    domain.require(isinstance(key, str) and _KEY_RE.match(key), "api_review_http_bad_key")
    body = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
    domain.require(len(body) <= _MAX, "api_review_http_oversized_request")
    req = urllib.request.Request(_ENDPOINTS[provider], data=body, method="POST")
    req.add_header("Authorization", "Bearer " + key)
    req.add_header("Content-Type", "application/json")
    if opener is None:
        opener = urllib.request.build_opener(NoRedirect()).open
    try:
        with opener(req, timeout=180) as resp:
            domain.require(resp.status == 200, "api_review_http_status")
            ctype = resp.headers.get("Content-Type", "")
            domain.require("application/json" in ctype, "api_review_http_not_json")
            raw = resp.read(_MAX + 1)
            domain.require(len(raw) <= _MAX, "api_review_http_oversized_response")
            xrid = resp.headers.get("X-Request-Id")
            xrid = xrid if isinstance(xrid, str) and _XRID_RE.match(xrid) else None
    except urllib.error.HTTPError as e:
        e.close()
        domain.require(False, f"api_review_http_{e.code}")
    except (urllib.error.URLError, TimeoutError, OSError, HTTPException):
        domain.require(False, "api_review_outcome_unknown")
    result = domain.strict_json(raw)
    domain.require(isinstance(result, dict), "api_review_http_not_object")
    return result, xrid
