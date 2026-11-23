"""Shared authored loopback fixtures for automation contracts and completion receipts."""

import base64
import contextlib
import http.server
import json
import sys
import threading
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/github"))
import openai_automation as automation
import openai_automation_github as github

NOW = datetime(2026, 11, 7, 12, tzinfo=UTC)


def snapshot_document():
    return automation.strict_json(
        (ROOT / "tests/fixtures/openai_automation_snapshot.json").read_bytes()
    )


def policy_document():
    return automation.strict_json(
        (ROOT / "tools/github/openai_automation_policy.json").read_bytes()
    )


def triage_document():
    return {
        "issue_number": 9001,
        "revision": "a" * 64,
        "labels": ["enhancement", "area: ci"],
        "priority": "P1",
        "next_action": "Validate the authored example and record the result.",
    }


def state_document():
    return {
        "version": 1,
        "repository": automation.REPOSITORY,
        "board_id": automation.BOARD_ID,
        "cycle_start": "2026-11-01T00:00:00Z",
        "cycle_end": "2026-12-01T00:00:00Z",
        "generation": 0,
        "lease": None,
        "allocations": [],
        "intents": [],
        "actions_minutes": 0,
    }


def enabled_policy():
    row = policy_document()
    row.update(
        enabled=True,
        rollout_complete=True,
        controller_sha="1" * 40,
        model="fixture-model",
        effort="low",
        input_price_micro_usd_per_million=1_000_000,
        output_price_micro_usd_per_million=4_000_000,
        api_budget_micro_usd=10_000_000,
        request_budget_micro_usd=500_000,
        actions_budget_minutes=100,
        cycle_start="2026-11-01T00:00:00Z",
        cycle_end="2026-12-01T00:00:00Z",
        prerequisites=dict.fromkeys(automation.PREREQUISITES, True),
    )
    return automation.Policy.parse(row)


def response_document(value):
    return {
        "id": "resp_fixture",
        "model": "fixture-model",
        "status": "completed",
        "usage": {"input_tokens": 100, "output_tokens": 40, "total_tokens": 140},
        "output": [
            {
                "type": "message",
                "role": "assistant",
                "status": "completed",
                "content": [{"type": "output_text", "text": json.dumps(value)}],
            }
        ],
    }


def seed_lease(service):
    state = automation.acquire_lease(
        automation.parse_state(service.state), "publisher", NOW, NOW + timedelta(minutes=4)
    )
    service.state = json.loads(json.dumps(automation.state_payload(state)))


@contextlib.contextmanager
def fixture_http(respond):
    """Real bounded HTTP parsing, with synthetic credentials and no public network."""

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            self.answer()

        def do_POST(self):
            self.answer()

        def do_PUT(self):
            self.answer()

        def answer(self):
            length = int(self.headers.get("Content-Length", "0"))
            payload = automation.strict_json(self.rfile.read(length)) if length else None
            status, headers, body = respond(self.command, self.path, payload, self.headers)
            raw = body if isinstance(body, bytes) else json.dumps(body).encode()
            self.send_response(status)
            for name, value in headers.items():
                self.send_header(name, value)
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def open_local(request):
        local = urllib.request.Request(
            f"http://127.0.0.1:{server.server_port}{request.selector}",
            data=request.data,
            headers=dict(request.header_items()),
            method=request.method,
        )
        return urllib.request.build_opener(github.NoRedirect()).open(local, timeout=2)

    try:
        yield open_local
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


class GitHubService:
    """Small authored API fixture that persists real adapter requests and CAS writes."""

    def __init__(self):
        self.issues = snapshot_document()["issues"]
        self.state = state_document()
        self.sha = "c" * 40
        self.enabled = True
        self.requests = []
        self.effects = []
        self.fail_after_effect = False
        self.disable_after_save = False
        self.nested_incomplete = False
        self.state_missing = False

    def board_response(self):
        nodes = []
        for issue in self.issues:
            values = [
                {"field": {"id": automation.STATUS_FIELD}, "name": issue["status"]},
                {"field": {"id": automation.PRIORITY_FIELD}, "name": issue["priority"]},
                {"field": {"id": automation.NEXT_ACTION_FIELD}, "text": issue["next_action"]},
            ]
            content = {
                "__typename": "Issue",
                "repository": {"nameWithOwner": automation.REPOSITORY},
                "number": issue["number"],
                "title": issue["title"],
                "body": issue["body"],
                "closed": not issue["open"],
                "updatedAt": "2026-11-07T12:00:00Z",
                "labels": {
                    "pageInfo": {"hasNextPage": self.nested_incomplete},
                    "nodes": [{"name": label} for label in issue["labels"]],
                },
                "assignees": {
                    "pageInfo": {"hasNextPage": False},
                    "nodes": [{"login": name} for name in issue["assignees"]],
                },
            }
            nodes.append(
                {
                    "id": issue["item_id"],
                    "content": content,
                    "fieldValues": {"nodes": values, "pageInfo": {"hasNextPage": False}},
                }
            )
        return {
            "data": {
                "node": {
                    "id": automation.BOARD_ID,
                    "number": 1,
                    "owner": {"login": "roswellien"},
                    "items": {
                        "totalCount": len(nodes),
                        "nodes": nodes,
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                    },
                }
            }
        }

    def respond(self, method, path, payload, headers):
        self.requests.append((method, path, payload, headers.get("Authorization")))
        if method == "GET" and path.startswith(github.STATE_ROUTE):
            if self.state_missing:
                return 404, {}, {"message": "secret-fixture"}
            raw = json.dumps(self.state).encode()
            return (
                200,
                {},
                {
                    "type": "file",
                    "encoding": "base64",
                    "sha": self.sha,
                    "size": len(raw),
                    "content": base64.b64encode(raw).decode(),
                },
            )
        if method == "PUT" and path == github.STATE_ROUTE:
            if payload["sha"] != self.sha:
                return 409, {}, {"message": "stale"}
            self.state = automation.strict_json(base64.b64decode(payload["content"]))
            self.sha = automation.fingerprint(self.state)[:40]
            if self.disable_after_save:
                self.enabled = False
            return 200, {}, {"content": {"sha": self.sha}}
        if path == f"{github.ROOT}/branches/develop":
            return 200, {}, {"name": "develop", "commit": {"sha": "1" * 40}}
        if path.startswith(f"{github.ROOT}/issues?state=open"):
            return 200, {}, [{"number": issue["number"]} for issue in self.issues if issue["open"]]
        if path.endswith(f"/actions/variables/{github.ENABLED_VARIABLE}"):
            return 200, {}, {"name": github.ENABLED_VARIABLE, "value": str(self.enabled).lower()}
        if path == "/graphql" and "pullRequests" in payload["query"]:
            return (
                200,
                {},
                {
                    "data": {
                        "repository": {
                            "pullRequests": {
                                "totalCount": 1,
                                "pageInfo": {"hasNextPage": False},
                                "nodes": [
                                    {
                                        "closingIssuesReferences": {
                                            "pageInfo": {"hasNextPage": False},
                                            "nodes": [
                                                {
                                                    "number": 9002,
                                                    "repository": {
                                                        "nameWithOwner": automation.REPOSITORY
                                                    },
                                                }
                                            ],
                                        }
                                    }
                                ],
                            }
                        }
                    }
                },
            )
        if path == "/graphql" and "query(" in payload["query"]:
            return 200, {}, self.board_response()
        if path == "/graphql" and "mutation(" in payload["query"]:
            variables = payload["variables"]
            issue = next(issue for issue in self.issues if issue["item_id"] == variables["item"])
            if variables["field"] == automation.NEXT_ACTION_FIELD:
                issue["next_action"] = variables["value"]["text"]
            else:
                issue["priority"] = next(
                    key
                    for key, value in automation.PRIORITY_OPTIONS.items()
                    if value == variables["value"]["singleSelectOptionId"]
                )
            self.effects.append(variables)
            if self.fail_after_effect:
                return 500, {}, {"message": "lost response with secret-fixture"}
            return (
                200,
                {},
                {
                    "data": {
                        "updateProjectV2ItemFieldValue": {"projectV2Item": {"id": issue["item_id"]}}
                    }
                },
            )
        if method == "POST" and path.endswith("/labels"):
            issue = next(issue for issue in self.issues if f"/{issue['number']}/" in path)
            issue["labels"] = sorted(set(issue["labels"]) | set(payload["labels"]))
            self.effects.append(payload)
            return 200, {}, []
        return 400, {}, {"message": "unexpected fixture route"}


def github_client(opener):
    return github.GitHub(
        github.JsonTransport("api.github.com", "fixture-app", opener=opener),
        github.JsonTransport("api.github.com", "fixture-projects", opener=opener),
    )
