"""Authored fixtures for new automation authority/state behavior, absent from board tests."""

import base64
import contextlib
import copy
import http.client
import http.server
import io
import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import asdict, replace
from datetime import timedelta
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/github"))
import openai_automation as automation
import openai_automation_github as github
import openai_automation_openai as provider
from openai_automation_fixtures import (
    NOW,
    GitHubService,
    enabled_policy,
    fixture_http,
    github_client,
    policy_document,
    response_document,
    seed_lease,
    snapshot_document,
    state_document,
    triage_document,
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
        for value in (
            '{"enabled":false,"enabled":true}',
            '{"cost":NaN}',
            '{"cost":Infinity}',
            '{"cost":1e999}',
            '{"cost":-1e999}',
            "{",
        ):
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
            {"labels": ["bug", "area: ci"]},
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
    def test_operation_id_boundaries_and_terminal_intent_transitions(self):
        snapshot = automation.Snapshot.parse(snapshot_document())
        proposal = automation.TriageProposal.parse(triage_document(), snapshot, 9001)
        initial = automation.parse_state(state_document())
        state = automation.prepare_triage(initial, snapshot, proposal, "x" * 52)
        self.assertEqual(len(state.intents[-1].operation_id), 64)
        unchanged = replace(proposal, next_action=snapshot.issue(9001).next_action)
        self.assertEqual(automation.prepare_triage(initial, snapshot, unchanged, "x" * 52), initial)
        for current in (proposal, unchanged):
            for length in (53, 55):
                with (
                    self.subTest(length=length, unchanged=current == unchanged),
                    self.assertRaisesRegex(automation.AutomationError, "invalid_id"),
                ):
                    automation.prepare_triage(initial, snapshot, current, "x" * length)
        operation_id = state.intents[0].operation_id
        for before, after in (
            ("publishing", "superseded"),
            ("applied", "prepared"),
            ("superseded", "publishing"),
        ):
            changed = replace(state, intents=(replace(state.intents[0], outcome=before),))
            with (
                self.subTest(before=before),
                self.assertRaisesRegex(automation.AutomationError, "invalid_intent_transition"),
            ):
                automation.update_intent(changed, operation_id, after)
        labels = asdict(state.intents[0]) | {
            "field": "labels",
            "before": ["needs-info"],
            "desired": ["enhancement", "area: ci"],
        }
        for desired, code in (
            (["enhancement", "area: ci"], "human_label_removal"),
            (["needs-info", "automation-ready"], "disallowed_label"),
        ):
            with self.subTest(code=code), self.assertRaisesRegex(automation.AutomationError, code):
                automation.parse_intent(labels | {"desired": desired})

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
    def test_crlf_is_bounded_normalized_and_fingerprinted_consistently(self):
        service = GitHubService()
        service.issues[0].update(
            title="First\r\nsecond", body="Body\r\nnext", next_action="Next\r\nline"
        )
        with fixture_http(service.respond) as opener:
            client = github_client(opener)
            first = client.read_snapshot(NOW)
            for name in ("title", "body", "next_action"):
                service.issues[0][name] = service.issues[0][name].replace("\r\n", "\n")
            self.assertEqual(first, client.read_snapshot(NOW))
            self.assertEqual(first.issue(9001).body, "Body\nnext")
            for body, code in (
                ("bare\rreturn", "control_text"),
                ("bad\x00control", "control_text"),
                ("\r\n" * 8001, "invalid_text_length"),
            ):
                service.issues[0]["body"] = body
                with (
                    self.subTest(code=code),
                    self.assertRaisesRegex(automation.AutomationError, code),
                ):
                    client.read_snapshot(NOW)

    def test_label_additions_are_idempotent_and_acknowledge_concurrent_human_labels(self):
        for concurrent in (False, True):
            service = GitHubService()

            def respond(method, path, payload, headers, service=service, concurrent=concurrent):
                result = service.respond(method, path, payload, headers)
                if method == "POST" and path.endswith("/labels") and concurrent:
                    service.issues[0]["labels"].append("needs-review")
                return result

            with fixture_http(respond) as opener:
                client = github_client(opener)
                snapshot = client.read_snapshot(NOW)
                proposal = automation.TriageProposal.parse(
                    triage_document()
                    | {
                        "revision": snapshot.issue(9001).revision,
                        "labels": ["enhancement", "area: ci", "area: launcher"],
                        "priority": "P0",
                    },
                    snapshot,
                    9001,
                )
                seed_lease(service)
                state = automation.prepare_triage(
                    automation.parse_state(service.state), snapshot, proposal, "labels"
                )
                service.state = json.loads(json.dumps(automation.state_payload(state)))
                self.assertEqual(
                    client.publish_one(
                        "labels_labels", "publisher", 1, lambda: NOW, policy=enabled_policy()
                    ),
                    "applied",
                )
                self.assertEqual(
                    client.publish_one(
                        "labels_labels", "publisher", 1, lambda: NOW, policy=enabled_policy()
                    ),
                    "applied",
                )
                posts = [
                    row
                    for row in service.requests
                    if row[0] == "POST" and row[1].endswith("/labels")
                ]
                self.assertEqual([row[2] for row in posts], [{"labels": ["area: launcher"]}])
                self.assertIn("needs-info", service.issues[0]["labels"])
                sibling = service.state["intents"][1]
                self.assertEqual(sibling["revision"] == snapshot.issue(9001).revision, concurrent)
                self.assertEqual(
                    client.publish_one(
                        "labels_priority", "publisher", 1, lambda: NOW, policy=enabled_policy()
                    ),
                    "superseded" if concurrent else "applied",
                )
                self.assertEqual(service.issues[0]["priority"], "P1" if concurrent else "P0")
                if concurrent:
                    self.assertIn("needs-review", service.issues[0]["labels"])

    def test_transport_redacts_protocol_errors_and_scopes_version_header(self):
        for host in ("api.github.com", "api.openai.com"):

            def truncated(request, host=host):
                self.assertEqual(
                    request.get_header("X-github-api-version") is not None, host == "api.github.com"
                )
                raise http.client.IncompleteRead(b"secret-fixture", 30)

            with (
                self.subTest(host=host),
                self.assertRaisesRegex(automation.Blocked, "^unknown_http_outcome$"),
            ):
                github.JsonTransport(host, "fixture", opener=truncated).request("GET", "/")

    def test_publication_requires_approved_policy_even_with_a_live_lease(self):
        service = GitHubService()
        with fixture_http(service.respond) as opener:
            client = github_client(opener)
            self.prepare(service, client)
            for policy in (
                automation.Policy.parse(policy_document()),
                replace(enabled_policy(), cycle_end="2026-11-06T00:00:00Z"),
            ):
                with self.assertRaisesRegex(automation.AutomationError, "configuration_incomplete"):
                    client.publish_one(
                        "triage_priority", "publisher", 1, lambda: NOW, policy=policy
                    )
            self.assertEqual(service.effects, [])

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
                client.publish_one(
                    "triage_priority", "publisher", 1, lambda: NOW, policy=enabled_policy()
                ),
                "applied",
            )
            self.assertEqual(
                client.publish_one(
                    "triage_next_action", "publisher", 1, lambda: NOW, policy=enabled_policy()
                ),
                "applied",
            )
            self.assertEqual(
                client.publish_one(
                    "triage_priority", "publisher", 1, lambda: NOW, policy=enabled_policy()
                ),
                "applied",
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
                with self.subTest(action=action):
                    if action == "human":
                        self.assertEqual(
                            client.publish_one(
                                "triage_priority",
                                "publisher",
                                1,
                                lambda: NOW,
                                policy=enabled_policy(),
                            ),
                            "superseded",
                        )
                        self.assertEqual(
                            client.publish_one(
                                "triage_next_action",
                                "publisher",
                                1,
                                lambda: NOW,
                                policy=enabled_policy(),
                            ),
                            "superseded",
                        )
                        self.assertTrue(
                            all(
                                item["outcome"] == "superseded" for item in service.state["intents"]
                            )
                        )
                        automation.allocate_request(
                            automation.parse_state(service.state),
                            enabled_policy(),
                            "fresh",
                            100,
                            NOW,
                        )
                    else:
                        with self.assertRaises(automation.Blocked):
                            client.publish_one(
                                "triage_priority",
                                "publisher",
                                1,
                                lambda: NOW,
                                policy=enabled_policy(),
                            )
                self.assertEqual(service.effects, [])

    def test_lost_response_is_reconciled_without_repeating_field_write(self):
        service = GitHubService()
        with fixture_http(service.respond) as opener:
            client = github_client(opener)
            self.prepare(service, client)
            service.fail_after_effect = True
            with self.assertRaisesRegex(automation.AutomationError, "^http_500$"):
                client.publish_one(
                    "triage_priority", "publisher", 1, lambda: NOW, policy=enabled_policy()
                )
            self.assertEqual(service.state["intents"][0]["outcome"], "publishing")
            self.assertEqual(
                client.publish_one(
                    "triage_priority", "publisher", 1, lambda: NOW, policy=enabled_policy()
                ),
                "applied",
            )
            self.assertEqual(len(service.effects), 1)
            service.state["intents"][1]["outcome"] = "publishing"
            with self.assertRaisesRegex(automation.Blocked, "uncertain_publication"):
                client.publish_one(
                    "triage_next_action", "publisher", 1, lambda: NOW, policy=enabled_policy()
                )
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
    def test_equivalent_utc_cycles_share_accounting_identity(self):
        state = automation.parse_state(state_document() | {"cycle_start": "2026-11-01T00:00Z"})
        policy = enabled_policy()
        canonical = automation.Policy.parse(
            asdict(policy) | {"cycle_end": "2026-12-01T00:00:00.000000Z"}
        )
        self.assertEqual(canonical.cycle_end, state.cycle_end)
        automation.allocate_request(state, canonical, "equivalent", 100, NOW)
        decision = automation.reconciliation_decision(
            canonical, automation.Snapshot.parse(snapshot_document()), state, NOW
        )
        self.assertNotIn("ledger_cycle_mismatch", decision.blockers)

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

            with fixture_http(respond) as opener, tempfile.TemporaryDirectory() as receipt_dir:
                client = github_client(opener)
                snapshot = client.read_snapshot(NOW)
                api = provider.OpenAI(
                    enabled_policy(),
                    client,
                    github.JsonTransport("api.openai.com", "fixture-openai", opener=opener),
                    provider.CompletionJournal(Path(receipt_dir)),
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

            with fixture_http(respond) as opener, tempfile.TemporaryDirectory() as receipt_dir:
                client = github_client(opener)
                api = provider.OpenAI(
                    enabled_policy(),
                    client,
                    github.JsonTransport("api.openai.com", "fixture-openai", opener=opener),
                    provider.CompletionJournal(Path(receipt_dir)),
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

            with fixture_http(respond) as opener, tempfile.TemporaryDirectory() as receipt_dir:
                client = github_client(opener)
                snapshot = client.read_snapshot(NOW)
                service.disable_after_save = variant == "disable"
                api = provider.OpenAI(
                    enabled_policy(),
                    client,
                    github.JsonTransport("api.openai.com", "fixture-openai", opener=opener),
                    provider.CompletionJournal(Path(receipt_dir)),
                )
                with self.assertRaises(automation.AutomationError):
                    api.propose("triage", snapshot, 9001, "first", "publisher", 1, lambda: NOW)
                service.enabled = True
                with self.assertRaisesRegex(automation.Blocked, "unreconciled_usage"):
                    api.propose("triage", snapshot, 9001, "retry", "publisher", 1, lambda: NOW)
                self.assertEqual(len(calls), 1 if variant == "timeout" else 0)
                self.assertIsNone(service.state["allocations"][0]["actual_micro_usd"])

    def test_cycle_expiry_during_authority_reads_blocks_each_provider_effect(self):
        for phase, expiry_read in (("allocation", 2), ("dispatch", 3), ("settlement", 4)):
            service = GitHubService()
            end = automation.utc_text(NOW + timedelta(seconds=1))
            service.state["cycle_end"] = end
            seed_lease(service)
            policy = replace(enabled_policy(), cycle_end=end)
            time = [NOW]
            state_reads = []
            calls = []

            def respond(
                method,
                path,
                payload,
                headers,
                service=service,
                expiry_read=expiry_read,
                time=time,
                state_reads=state_reads,
                calls=calls,
            ):
                if path == "/v1/responses":
                    calls.append(payload)
                    return 200, {}, response_document({})
                result = service.respond(method, path, payload, headers)
                if method == "GET" and path.startswith(github.STATE_ROUTE):
                    state_reads.append(path)
                    if len(state_reads) == expiry_read:
                        time[0] += timedelta(seconds=2)
                return result

            with fixture_http(respond) as opener, tempfile.TemporaryDirectory() as directory:
                client = github_client(opener)
                journal = provider.CompletionJournal(Path(directory))
                api = provider.OpenAI(
                    policy,
                    client,
                    github.JsonTransport("api.openai.com", "fixture", opener=opener),
                    journal,
                )
                with (
                    self.subTest(phase=phase),
                    self.assertRaisesRegex(automation.AutomationError, "configuration_incomplete"),
                ):
                    api.propose(
                        "triage",
                        client.read_snapshot(NOW),
                        9001,
                        "cycle",
                        "publisher",
                        1,
                        lambda time=time: time[0],
                    )
                self.assertEqual(len(state_reads), expiry_read)
                self.assertEqual(len(calls), 1 if phase == "settlement" else 0)
                allocations = service.state["allocations"]
                self.assertEqual(len(allocations), 0 if phase == "allocation" else 1)
                if allocations:
                    self.assertIsNone(allocations[0]["actual_micro_usd"])
                self.assertEqual(
                    len(list(Path(directory).glob("receipt-*.json"))),
                    1 if phase == "settlement" else 0,
                )
                if phase == "settlement":
                    self.assertEqual(journal.read("cycle")["response_id"], "resp_fixture")

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

        with fixture_http(respond) as opener, tempfile.TemporaryDirectory() as receipt_dir:
            client = github_client(opener)
            snapshot = client.read_snapshot(NOW)
            api = provider.OpenAI(
                enabled_policy(),
                client,
                github.JsonTransport("api.openai.com", "fixture-openai", opener=opener),
                provider.CompletionJournal(Path(receipt_dir)),
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
