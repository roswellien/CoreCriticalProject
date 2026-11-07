"""Authored fixtures for new automation authority/state behavior, absent from board tests."""

import base64
import contextlib
import copy
import http.server
import json
import sys
import threading
import unittest
import urllib.request
from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest import mock

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


class ContractTests(unittest.TestCase):
    def test_disabled_policy_and_code_guard_are_independent(self):
        row = policy_document()
        policy = automation.Policy.parse(row)
        self.assertIn("disabled", automation.configuration_blockers(policy, NOW))
        row["enabled"] = row["rollout_complete"] = True
        automation.Policy.parse(row)
        with self.assertRaisesRegex(automation.Blocked, "foundation_rollout_incomplete"):
            automation.require_runtime_capabilities()

    def test_policy_rejects_unknown_scope_types_and_unset_cycle_half(self):
        for change in (
            {"extra": True},
            {"repository": "someone/else"},
            {"enabled": "true"},
            {"api_budget_micro_usd": -1},
            {"api_budget_micro_usd": True},
            {"api_budget_micro_usd": float("inf")},
            {"cycle_start": "2026-11-01T00:00:00Z"},
        ):
            with self.subTest(change=change), self.assertRaises(automation.AutomationError):
                automation.Policy.parse(policy_document() | change)

    def test_json_rejects_duplicate_keys_non_finite_and_malformed_documents(self):
        for value in ('{"enabled":false,"enabled":true}', '{"cost":NaN}', '{"cost":Infinity}', "{"):
            with self.subTest(value=value), self.assertRaises(automation.AutomationError):
                automation.strict_json(value)

    def test_complete_snapshot_reports_only_unclaimed_ready(self):
        snapshot = automation.Snapshot.parse(snapshot_document())
        self.assertEqual(snapshot.eligible_ready(), (9001,))
        self.assertEqual(snapshot.issue(9002).assignees, ("example-maintainer",))
        for change in (
            {"complete": False},
            {"repository": "another/repo"},
            {"base_sha": "develop"},
        ):
            with self.subTest(change=change), self.assertRaises(automation.AutomationError):
                automation.Snapshot.parse(snapshot_document() | change)
        row = snapshot_document()
        row["issues"].append(copy.deepcopy(row["issues"][0]))
        with self.assertRaisesRegex(automation.AutomationError, "duplicate_issue"):
            automation.Snapshot.parse(row)

    def test_triage_preserves_human_labels_and_rejects_control_authority(self):
        snapshot = automation.Snapshot.parse(snapshot_document())
        proposal = automation.TriageProposal.parse(triage_document(), snapshot, 9001)
        self.assertIn("needs-info", proposal.merged_labels(snapshot.issue(9001)))
        for change in (
            {"status": "Ready"},
            {"status": "Done"},
            {"assignees": ["bot"]},
            {"issue_number": 9002},
            {"revision": "b" * 64},
            {"labels": ["enhancement", "area: ci", "automation-ready"]},
            {"priority": "P9"},
            {"next_action": "${{ secrets.OPENAI_API_KEY }}"},
            {"next_action": "$(run-command)"},
            {"next_action": "https://attacker.test"},
            {"next_action": "<script>execute()</script>"},
            {"next_action": "x" * 501},
        ):
            with self.subTest(change=change), self.assertRaises(automation.AutomationError):
                automation.TriageProposal.parse(triage_document() | change, snapshot, 9001)

    def test_summary_ids_and_text_cannot_introduce_other_targets(self):
        snapshot = automation.Snapshot.parse(snapshot_document())
        entry = {
            "issue_number": 9001,
            "summary": "The authored example needs validation.",
            "suggested_priority": "P1",
            "next_action": "Run the fixture check.",
        }
        self.assertEqual(
            automation.parse_summary({"entries": [entry]}, snapshot)[0].issue_number, 9001
        )
        for entries in (
            [entry, entry],
            [entry | {"issue_number": 19}],
            [entry | {"summary": "<img src=credential>"}],
        ):
            with self.subTest(entries=entries), self.assertRaises(automation.AutomationError):
                automation.parse_summary({"entries": entries}, snapshot)


class StateTests(unittest.TestCase):
    def test_roundtrip_lease_contention_expiry_and_fencing(self):
        state = automation.parse_state(state_document())
        leased = automation.acquire_lease(state, "first", NOW, NOW + timedelta(minutes=4))
        serialized = json.dumps(automation.state_payload(leased))
        self.assertEqual(automation.parse_state(automation.strict_json(serialized)), leased)
        with self.assertRaisesRegex(automation.Blocked, "publisher_busy"):
            automation.acquire_lease(leased, "second", NOW, NOW + timedelta(minutes=4))
        later = NOW + timedelta(minutes=5)
        renewed = automation.acquire_lease(leased, "second", later, later + timedelta(minutes=4))
        self.assertEqual(renewed.generation, 2)
        for state, run, fence, now in ((renewed, "first", 1, later), (leased, "first", 1, later)):
            with self.subTest(run=run), self.assertRaises(automation.Blocked):
                automation.assert_fence(state, run, fence, now)

    def test_intents_detect_human_edits_and_preserve_partial_state(self):
        snapshot = automation.Snapshot.parse(snapshot_document())
        proposal = automation.TriageProposal.parse(
            triage_document() | {"priority": "P0"}, snapshot, 9001
        )
        state = automation.prepare_triage(
            automation.parse_state(state_document()), snapshot, proposal, "triage"
        )
        self.assertEqual(len(state.intents), 2)
        intent = state.intents[0]
        issue = snapshot.issue(9001)
        self.assertEqual(
            automation.intent_outcome(intent, replace(issue, priority="P2")), "conflict"
        )
        self.assertEqual(
            automation.intent_outcome(intent, replace(issue, priority="P0")), "applied"
        )
        publishing = automation.update_intent(state, intent.operation_id, "publishing")
        with self.assertRaisesRegex(automation.Blocked, "unreconciled_publication"):
            automation.acquire_lease(publishing, "later", NOW, NOW + timedelta(minutes=4))
        for changed in (
            {"generation": True},
            {"intents": [asdict(intent) | {"field": "status"}]},
            {"lease": {"run_id": "bad", "fence": 1, "expires_at": "no-time"}},
        ):
            with self.subTest(changed=changed), self.assertRaises(automation.AutomationError):
                automation.parse_state(state_document() | changed)


class GitHubTests(unittest.TestCase):
    def test_pagination_uses_owned_pages_and_rejects_incomplete_queue(self):
        for incomplete in (False, True):
            service = GitHubService()

            def respond(method, path, payload, headers, service=service, incomplete=incomplete):
                status, response_headers, body = service.respond(method, path, payload, headers)
                if path == "/graphql" and "ProjectV2" in payload["query"]:
                    connection = body["data"]["node"]["items"]
                    cursor = payload["variables"]["cursor"]
                    connection["nodes"] = (
                        connection["nodes"][:1] if cursor is None else connection["nodes"][1:]
                    )
                    connection["pageInfo"] = {"hasNextPage": cursor is None, "endCursor": "second"}
                    if incomplete and cursor is not None:
                        connection["totalCount"] = 3
                elif path.startswith(f"{github.ROOT}/issues?state=open"):
                    if path.endswith("page=1"):
                        body = body[:1]
                        response_headers = {"link": '<https://attacker.invalid>; rel="next"'}
                    else:
                        body = body[1:]
                return status, response_headers, body

            with fixture_http(respond) as opener:
                client = github_client(opener)
                if incomplete:
                    with self.assertRaisesRegex(automation.AutomationError, "pagination_changed"):
                        client.read_snapshot(NOW)
                else:
                    self.assertEqual(client.read_snapshot(NOW).eligible_ready(), (9001,))
                    self.assertTrue(
                        any(path.endswith("page=2") for _, path, _, _ in service.requests)
                    )

    def prepare(self, service, client):
        snapshot = client.read_snapshot(NOW)
        proposal = automation.TriageProposal.parse(
            triage_document() | {"revision": snapshot.issue(9001).revision, "priority": "P0"},
            snapshot,
            9001,
        )
        state = automation.acquire_lease(
            automation.parse_state(service.state), "publisher", NOW, NOW + timedelta(minutes=4)
        )
        service.state = json.loads(
            json.dumps(
                automation.state_payload(
                    automation.prepare_triage(state, snapshot, proposal, "triage")
                )
            )
        )

    def test_real_http_snapshot_separate_credentials_and_complete_reads(self):
        service = GitHubService()
        with fixture_http(service.respond) as opener:
            client = github_client(opener)
            self.assertEqual(client.read_snapshot(NOW).eligible_ready(), (9001,))
            for method, path, payload, auth in service.requests:
                is_board = path == "/graphql" and "ProjectV2" in payload["query"]
                self.assertEqual(
                    auth, "Bearer fixture-projects" if is_board else "Bearer fixture-app"
                )
            service.nested_incomplete = True
            with self.assertRaisesRegex(automation.AutomationError, "incomplete_nested_pagination"):
                client.read_snapshot(NOW)

    def test_cas_conflicts_missing_seed_and_errors_do_not_leak_body(self):
        service = GitHubService()
        with fixture_http(service.respond) as opener:
            client = github_client(opener)
            state, sha = client.read_state()
            client.save_state(state, sha, lambda: None)
            with self.assertRaises(automation.Conflict):
                client.save_state(state, sha, lambda: None)
            service.state_missing = True
            with self.assertRaisesRegex(automation.AutomationError, "^http_404$"):
                client.read_state()
            self.assertEqual(len(service.effects), 0)

    def test_intents_precede_writes_and_siblings_advance_without_losing_human_labels(self):
        service = GitHubService()
        with fixture_http(service.respond) as opener:
            client = github_client(opener)
            self.prepare(service, client)
            self.assertEqual(
                client.publish_one("triage_priority", "publisher", 1, lambda: NOW), "applied"
            )
            self.assertEqual(
                client.publish_one("triage_next_action", "publisher", 1, lambda: NOW), "applied"
            )
            self.assertEqual(
                client.publish_one("triage_priority", "publisher", 1, lambda: NOW), "applied"
            )
            self.assertEqual(len(service.effects), 2)
            self.assertIn("needs-info", service.issues[0]["labels"])
            self.assertTrue(
                all(intent["outcome"] == "applied" for intent in service.state["intents"])
            )
            for index, request in enumerate(service.requests):
                if (
                    request[0] == "POST"
                    and request[1] == "/graphql"
                    and "mutation(" in request[2]["query"]
                ):
                    preceding = [row for row in service.requests[:index] if row[0] == "PUT"]
                    state_before = automation.strict_json(
                        base64.b64decode(preceding[-1][2]["content"])
                    )
                    self.assertTrue(
                        any(intent["outcome"] == "publishing" for intent in state_before["intents"])
                    )

    def test_disable_and_human_edit_block_publication(self):
        for action in ("disable", "human", "fence"):
            service = GitHubService()
            with fixture_http(service.respond) as opener:
                client = github_client(opener)
                self.prepare(service, client)
                if action == "disable":
                    service.disable_after_save = True
                elif action == "human":
                    service.issues[0]["next_action"] = "Human owns this step."
                else:
                    service.state["generation"] = service.state["lease"]["fence"] = 2
                with self.subTest(action=action), self.assertRaises(automation.Blocked):
                    client.publish_one("triage_priority", "publisher", 1, lambda: NOW)
                self.assertEqual(service.effects, [])

    def test_lost_response_is_reconciled_without_repeating_field_write(self):
        service = GitHubService()
        with fixture_http(service.respond) as opener:
            client = github_client(opener)
            self.prepare(service, client)
            service.fail_after_effect = True
            with self.assertRaisesRegex(automation.AutomationError, "^http_500$"):
                client.publish_one("triage_priority", "publisher", 1, lambda: NOW)
            self.assertEqual(service.state["intents"][0]["outcome"], "publishing")
            self.assertEqual(
                client.publish_one("triage_priority", "publisher", 1, lambda: NOW), "applied"
            )
            self.assertEqual(len(service.effects), 1)
            service.state["intents"][1]["outcome"] = "publishing"
            with self.assertRaisesRegex(automation.Blocked, "uncertain_publication"):
                client.publish_one("triage_next_action", "publisher", 1, lambda: NOW)
            self.assertEqual(len(service.effects), 1)

    def test_production_transport_and_redirects_stay_closed(self):
        with (
            mock.patch(
                "urllib.request.OpenerDirector.open",
                side_effect=AssertionError("network attempted"),
            ),
            self.assertRaisesRegex(automation.Blocked, "foundation_rollout_incomplete"),
        ):
            github.JsonTransport("api.github.com", "fixture-app").request("GET", "/")
        with (
            fixture_http(
                lambda *args: (302, {"Location": "https://attacker.invalid"}, {})
            ) as opener,
            self.assertRaisesRegex(automation.AutomationError, "^http_302$"),
        ):
            github.JsonTransport("api.github.com", "fixture-app", opener=opener).request("GET", "/")


if __name__ == "__main__":
    unittest.main()
