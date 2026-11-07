"""Authored fixtures for new automation authority/state behavior, absent from board tests."""

import base64
import contextlib
import copy
import http.server
import io
import json
import subprocess
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
import openai_automation_openai as provider

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


class ProviderTests(unittest.TestCase):
    def test_budget_cycle_unknown_usage_and_integer_accounting(self):
        policy = enabled_policy()
        state = automation.parse_state(state_document())
        allocated = automation.allocate_request(state, policy, "request", 100, NOW)
        self.assertEqual(allocated.allocations[0].reserved_micro_usd, 10_125)
        self.assertEqual(allocated.actions_minutes, 5)
        settled = automation.settle_usage(allocated, policy, "request", response_document({}))
        self.assertEqual(settled.allocations[0].actual_micro_usd, 260)
        for current, config, op, size, time in (
            (allocated, policy, "another", 100, NOW),
            (settled, policy, "request", 100, NOW),
            (state, replace(policy, api_budget_micro_usd=1), "low", 100, NOW),
            (state, replace(policy, request_budget_micro_usd=1), "low", 100, NOW),
            (state, replace(policy, actions_budget_minutes=4), "low", 100, NOW),
            (state, replace(policy, model=None), "missing", 100, NOW),
            (state, policy, "large", 128_001, NOW),
            (state, policy, "expired", 100, NOW + timedelta(days=40)),
            (replace(state, cycle_start="2026-10-01T00:00:00Z"), policy, "cycle", 100, NOW),
        ):
            with self.subTest(op=op), self.assertRaises(automation.AutomationError):
                automation.allocate_request(current, config, op, size, time)
        for changed in (
            {"usage": None},
            {"model": "another-model"},
            {"usage": {"input_tokens": True, "output_tokens": 0, "total_tokens": 1}},
            {"usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 3}},
        ):
            with self.subTest(changed=changed), self.assertRaises(automation.AutomationError):
                automation.settle_usage(
                    allocated, policy, "request", response_document({}) | changed
                )

    def test_tool_free_protocol_persists_budget_before_returning_validated_proposals(self):
        for mode in ("triage", "summary"):
            service = GitHubService()
            seed_lease(service)
            captured = []

            def respond(
                method, path, payload, headers, service=service, mode=mode, captured=captured
            ):
                if path == "/v1/responses":
                    captured.append(
                        (payload, copy.deepcopy(service.state), headers.get("Authorization"))
                    )
                    issue = json.loads(payload["input"])["issues"][0]
                    value = triage_document() | {"revision": issue["revision"]}
                    if mode == "summary":
                        value = {
                            "entries": [
                                {
                                    "issue_number": 9001,
                                    "summary": "Fixture validation is pending.",
                                    "suggested_priority": "P1",
                                    "next_action": "Run the fixture.",
                                }
                            ]
                        }
                    return 200, {}, response_document(value)
                return service.respond(method, path, payload, headers)

            with fixture_http(respond) as opener:
                client = github_client(opener)
                snapshot = client.read_snapshot(NOW)
                api = provider.OpenAI(
                    enabled_policy(),
                    client,
                    github.JsonTransport("api.openai.com", "fixture-openai", opener=opener),
                )
                result = api.propose(
                    mode,
                    snapshot,
                    9001 if mode == "triage" else None,
                    "proposal",
                    "publisher",
                    1,
                    lambda: NOW,
                )
                if mode == "summary":
                    self.assertEqual(
                        provider.domain.render_summary(result)[0]["issue"],
                        f"https://github.com/{automation.REPOSITORY}/issues/9001",
                    )
                self.assertEqual(
                    result.issue_number if mode == "triage" else result[0].issue_number, 9001
                )
                request, persisted, auth = captured[0]
                self.assertEqual(auth, "Bearer fixture-openai")
                self.assertFalse(request["store"])
                self.assertNotIn("tools", request)
                self.assertTrue(request["text"]["format"]["strict"])
                self.assertNotIn("assignees", json.loads(request["input"])["issues"][0])
                self.assertIsNone(persisted["allocations"][0]["actual_micro_usd"])
                self.assertEqual(service.state["allocations"][0]["actual_micro_usd"], 260)
                self.assertEqual(service.effects, [])

    def test_refusal_truncation_tool_output_and_unknown_cost_never_authorize_writes(self):
        variants = ("refusal", "incomplete", "tool", "unknown_issue", "malformed", "usage", "model")
        for variant in variants:
            service = GitHubService()
            seed_lease(service)

            def respond(method, path, payload, headers, service=service, variant=variant):
                if path != "/v1/responses":
                    return service.respond(method, path, payload, headers)
                value = triage_document() | {
                    "revision": json.loads(payload["input"])["issues"][0]["revision"]
                }
                response = response_document(value)
                if variant == "refusal":
                    response["output"][0]["content"] = [{"type": "refusal", "refusal": "No."}]
                elif variant == "incomplete":
                    response["status"] = "incomplete"
                elif variant == "tool":
                    response["output"] = [{"type": "function_call", "name": "merge"}]
                elif variant == "unknown_issue":
                    response["output"][0]["content"][0]["text"] = json.dumps(
                        value | {"issue_number": 19}
                    )
                elif variant == "malformed":
                    response["output"][0]["content"][0]["text"] = "not-json"
                elif variant == "usage":
                    response["usage"] = None
                else:
                    response["model"] = "unapproved"
                return 200, {}, response

            with fixture_http(respond) as opener:
                client = github_client(opener)
                api = provider.OpenAI(
                    enabled_policy(),
                    client,
                    github.JsonTransport("api.openai.com", "fixture-openai", opener=opener),
                )
                with self.subTest(variant=variant), self.assertRaises(automation.AutomationError):
                    api.propose(
                        "triage",
                        client.read_snapshot(NOW),
                        9001,
                        "bad",
                        "publisher",
                        1,
                        lambda: NOW,
                    )
                allocation = service.state["allocations"][0]
                self.assertEqual(
                    allocation["actual_micro_usd"], None if variant in ("usage", "model") else 260
                )
                self.assertEqual(service.effects, [])

    def test_timeout_disable_and_changed_source_cannot_duplicate_spending(self):
        for variant in ("timeout", "disable", "source"):
            service = GitHubService()
            seed_lease(service)
            calls = []

            def respond(
                method, path, payload, headers, service=service, variant=variant, calls=calls
            ):
                if path == "/v1/responses":
                    calls.append(payload)
                    return 500, {}, {"message": "secret-fixture"}
                result = service.respond(method, path, payload, headers)
                if method == "PUT" and variant == "source":
                    service.issues[0]["body"] = "Changed by a human."
                return result

            with fixture_http(respond) as opener:
                client = github_client(opener)
                snapshot = client.read_snapshot(NOW)
                service.disable_after_save = variant == "disable"
                api = provider.OpenAI(
                    enabled_policy(),
                    client,
                    github.JsonTransport("api.openai.com", "fixture-openai", opener=opener),
                )
                with self.assertRaises(automation.AutomationError):
                    api.propose("triage", snapshot, 9001, "first", "publisher", 1, lambda: NOW)
                service.enabled = True
                with self.assertRaisesRegex(automation.Blocked, "unreconciled_usage"):
                    api.propose("triage", snapshot, 9001, "retry", "publisher", 1, lambda: NOW)
                self.assertEqual(len(calls), 1 if variant == "timeout" else 0)
                self.assertIsNone(service.state["allocations"][0]["actual_micro_usd"])

    def test_actual_usage_overshoot_is_recorded_and_blocks_further_calls(self):
        service = GitHubService()
        seed_lease(service)

        def respond(method, path, payload, headers):
            if path == "/v1/responses":
                response = response_document(triage_document())
                response["usage"] = {
                    "input_tokens": 500_000,
                    "output_tokens": 0,
                    "total_tokens": 500_000,
                }
                return 200, {}, response
            return service.respond(method, path, payload, headers)

        with fixture_http(respond) as opener:
            client = github_client(opener)
            snapshot = client.read_snapshot(NOW)
            api = provider.OpenAI(
                enabled_policy(),
                client,
                github.JsonTransport("api.openai.com", "fixture-openai", opener=opener),
            )
            for operation in ("overshoot", "next"):
                with self.assertRaisesRegex(automation.Blocked, "allocation_exceeded"):
                    api.propose("triage", snapshot, 9001, operation, "publisher", 1, lambda: NOW)
            self.assertEqual(service.state["allocations"][0]["actual_micro_usd"], 500_000)
            self.assertEqual(len(service.state["allocations"]), 1)


class EntryPointTests(unittest.TestCase):
    def test_offline_preview_runs_without_credentials_or_network(self):
        command = [
            sys.executable,
            "-B",
            str(ROOT / "tools/github/openai_automation.py"),
            "preview",
            "--snapshot",
            str(ROOT / "tests/fixtures/openai_automation_snapshot.json"),
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=True, cwd=ROOT)
        value = json.loads(result.stdout)
        self.assertEqual(value["decision"]["ready_candidates"], [9001])
        self.assertEqual((value["remote_writes"], value["provider_calls"]), (0, 0))
        with (
            mock.patch("os.getenv", side_effect=AssertionError("credential lookup")),
            mock.patch(
                "urllib.request.OpenerDirector.open",
                side_effect=AssertionError("network attempted"),
            ),
            contextlib.redirect_stdout(io.StringIO()) as output,
        ):
            self.assertEqual(automation.main(command[3:]), 0)
        self.assertEqual(json.loads(output.getvalue())["mode"], "offline_preview")

    def test_live_modes_block_before_config_or_credentials_even_with_ambient_authorization(self):
        for mode in ("reconcile", "summary", "triage"):
            with (
                mock.patch.object(
                    automation, "read_json_file", side_effect=AssertionError("file read")
                ),
                mock.patch("os.getenv", side_effect=AssertionError("credential lookup")),
                contextlib.redirect_stderr(io.StringIO()) as error,
            ):
                self.assertEqual(
                    automation.main([mode, "--policy", "do-not-read.env", "--issue", "9001"]), 2
                )
            self.assertEqual(error.getvalue().strip(), "blocked: foundation_rollout_incomplete")

    def test_reconciliation_reports_pending_intents_without_claiming_ready(self):
        snapshot = automation.Snapshot.parse(snapshot_document())
        policy = enabled_policy()
        state = automation.prepare_triage(
            automation.parse_state(state_document()),
            snapshot,
            automation.TriageProposal.parse(triage_document(), snapshot, 9001),
            "new",
        )
        before = asdict(state)
        decision = automation.reconciliation_decision(policy, snapshot, state, NOW)
        self.assertEqual(decision.kind, "pause")
        self.assertEqual(decision.pending_intents, ("new_next_action",))
        self.assertIn("foundation_rollout_incomplete", decision.blockers)
        self.assertEqual(asdict(state), before)
        self.assertEqual(snapshot.issue(9001).status, "Ready")


class WorkflowTests(unittest.TestCase):
    def test_workflow_structure_keeps_trusted_code_and_credentials_closed(self):
        workflow = automation.strict_json(
            (ROOT / ".github/workflows/openai-automation.yml").read_bytes()
        )
        self.assertEqual(set(workflow["on"]), {"schedule", "workflow_dispatch"})
        self.assertEqual(workflow["on"]["schedule"], [{"cron": "17 * * * *"}])
        self.assertEqual(workflow["permissions"], {"contents": "read"})
        self.assertFalse(workflow["concurrency"]["cancel-in-progress"])
        self.assertEqual(set(workflow["jobs"]), {"controller"})
        self.assertNotIn("secrets.", json.dumps(workflow))
        job = workflow["jobs"]["controller"]
        self.assertEqual(job.get("permissions", {"contents": "read"}), {"contents": "read"})
        self.assertEqual((job["timeout-minutes"], job["environment"]), (5, "openai-automation"))
        for condition in (
            "github.ref == 'refs/heads/develop'",
            "vars.OPENAI_AUTOMATION_ENABLED == 'true'",
            "vars.OPENAI_AUTOMATION_ROLLOUT_COMPLETE == 'true'",
            "vars.OPENAI_AUTOMATION_CONTROLLER_SHA != ''",
        ):
            self.assertIn(condition, job["if"])
        steps = job["steps"]
        self.assertEqual(len(steps), 5)
        self.assertIn("^[0-9a-f]{40}$", steps[0]["run"])
        self.assertEqual(
            steps[1]["uses"], "actions/checkout@11d5960a326750d5838078e36cf38b85af677262"
        )
        self.assertEqual(
            steps[1]["with"],
            {
                "ref": "${{ vars.OPENAI_AUTOMATION_CONTROLLER_SHA }}",
                "fetch-depth": 0,
                "persist-credentials": False,
            },
        )
        self.assertIn("git merge-base --is-ancestor", steps[2]["run"])
        self.assertEqual(
            steps[3]["uses"], "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065"
        )
        self.assertEqual(
            steps[4]["run"],
            'python -B tools/github/openai_automation.py "$AUTOMATION_MODE" --issue "$AUTOMATION_ISSUE" --admission-only',
        )
        for step in steps:
            self.assertNotIn("${{", step.get("run", ""))
            self.assertNotIn("secrets.", json.dumps(step))
        self.assertNotIn("secrets.", json.dumps(job))
        with contextlib.redirect_stderr(io.StringIO()) as error:
            self.assertEqual(automation.main(["reconcile", "--issue", "0", "--admission-only"]), 2)
        self.assertIn("foundation_rollout_incomplete", error.getvalue())


if __name__ == "__main__":
    unittest.main()
