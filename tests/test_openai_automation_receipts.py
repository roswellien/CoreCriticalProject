"""Completion storage and recovery are separate from ordinary publication authority."""

import copy
import json
import os
import sys
import tempfile
import unittest
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/github"))
import openai_automation_openai as provider
import openai_automation_receipts as receipts
from openai_automation_fixtures import (
    NOW,
    GitHubService,
    automation,
    enabled_policy,
    fixture_http,
    github,
    github_client,
    response_document,
    seed_lease,
    state_document,
    triage_document,
)


class CompletionTests(unittest.TestCase):
    def test_storage_preflight_blocks_unsupported_or_nonexclusive_publication(self):
        for variant in ("unsupported", "nonexclusive"):
            service = GitHubService()
            seed_lease(service)
            with (
                fixture_http(service.respond) as opener,
                tempfile.TemporaryDirectory() as directory,
            ):
                journal = receipts.CompletionJournal(Path(directory))
                client = github_client(opener)
                api = provider.OpenAI(
                    enabled_policy(),
                    client,
                    github.JsonTransport("api.openai.com", "fixture", opener=opener),
                    journal,
                )
                failure = OSError("private-path") if variant == "unsupported" else None
                code = (
                    "completion_receipt_io_failed"
                    if variant == "unsupported"
                    else "completion_receipt_storage_not_exclusive"
                )
                with (
                    self.subTest(variant=variant),
                    mock.patch.object(receipts.os, "link", side_effect=failure),
                    self.assertRaisesRegex(automation.Blocked, f"^{code}$"),
                ):
                    api.propose(
                        "triage",
                        client.read_snapshot(NOW),
                        9001,
                        "unsent",
                        "publisher",
                        1,
                        lambda: NOW,
                    )
                self.assertEqual(service.state["allocations"], [])
                self.assertFalse(
                    any(row[0] == "PUT" or row[1] == "/v1/responses" for row in service.requests)
                )
                self.assertEqual(list(Path(directory).iterdir()), [])

    def test_immutable_redacted_receipts_validate_evidence_and_allocation_binding(self):
        policy = enabled_policy()
        state = automation.allocate_request(
            automation.parse_state(state_document()), policy, "complete", 100, NOW
        )
        response = response_document({"secret-fixture": "not persisted"})
        with tempfile.TemporaryDirectory() as directory:
            journal = receipts.CompletionJournal(Path(directory))
            with self.assertRaisesRegex(automation.Blocked, "^completion_receipt_io_failed$"):
                journal.read("missing")
            receipt = receipts.completion_receipt(state, policy, "complete", response)
            journal.check_available("complete")
            journal.record(receipt)
            journal.record(receipt)
            self.assertEqual(journal.read("complete"), receipt)
            self.assertNotIn(
                "secret-fixture", next(Path(directory).glob("receipt-*.json")).read_text()
            )
            with self.assertRaisesRegex(automation.Conflict, "completion_receipt_conflict"):
                journal.record(receipt | {"response_id": "resp_other"})
            self.assertEqual(journal.read("complete"), receipt)
            with self.assertRaisesRegex(automation.AutomationError, "completion_receipt_exists"):
                journal.check_available("complete")
            for operation in ("../escape", "x" * 65):
                with self.assertRaisesRegex(automation.AutomationError, "invalid_id"):
                    journal.check_available(operation)
            settled = receipts.settle_receipt(state, policy, receipt)
            self.assertEqual(settled.allocations[0].actual_micro_usd, 260)
            self.assertEqual(receipts.settle_receipt(settled, policy, receipt), settled)
            for changed, config in (
                (replace(state, cycle_start="2026-10-01T00:00:00Z"), policy),
                (state, replace(policy, input_price_micro_usd_per_million=2)),
            ):
                with self.assertRaisesRegex(
                    automation.AutomationError, "receipt_allocation_mismatch"
                ):
                    receipts.settle_receipt(changed, config, receipt)
            for change, anomaly in (
                ({"model": "unapproved"}, "unexpected_model"),
                ({"id": "https://secret.invalid"}, "invalid_response_id"),
                ({"usage": None}, "invalid_usage"),
                (
                    {"usage": {"input_tokens": True, "output_tokens": 0, "total_tokens": 1}},
                    "invalid_usage",
                ),
            ):
                evidence = receipts.completion_receipt(state, policy, "complete", response | change)
                self.assertIn(anomaly, evidence["anomalies"])
                self.assertNotIn("https://secret.invalid", json.dumps(evidence))
                with self.assertRaisesRegex(
                    automation.AutomationError, "receipt_requires_owner_reconciliation"
                ):
                    receipts.settle_receipt(state, policy, evidence)

    def test_storage_failures_do_not_overwrite_evidence_or_release_reservations(self):
        state = automation.allocate_request(
            automation.parse_state(state_document()), enabled_policy(), "complete", 100, NOW
        )
        receipt = receipts.completion_receipt(
            state, enabled_policy(), "complete", response_document({})
        )
        with tempfile.TemporaryDirectory() as directory:
            journal = receipts.CompletionJournal(Path(directory))
            with (
                mock.patch.object(receipts.os, "link", side_effect=OSError("private-path")),
                self.assertRaisesRegex(automation.Blocked, "^completion_receipt_io_failed$"),
            ):
                journal.record(receipt)
            self.assertEqual(list(Path(directory).iterdir()), [])
            with (
                mock.patch.object(journal, "_flush_directory", side_effect=OSError("private-path")),
                self.assertRaisesRegex(automation.Blocked, "^completion_receipt_io_failed$"),
            ):
                journal.record(receipt)
            # A flush failure may leave complete evidence. It is never overwritten.
            self.assertEqual(journal.read("complete"), receipt)
            self.assertIsNone(state.allocations[0].actual_micro_usd)
            if os.name != "nt":
                os.chmod(directory, 0o777)
                try:
                    with self.assertRaisesRegex(
                        automation.AutomationError, "unsafe_receipt_permissions"
                    ):
                        journal.read("complete")
                finally:
                    os.chmod(directory, 0o700)

    def test_successful_response_keeps_receipt_across_disable_expiry_and_model_anomaly(self):
        for variant in ("disable", "expiry", "model", "fence"):
            service = GitHubService()
            seed_lease(service)
            time = [NOW]
            calls = []

            def respond(
                method,
                path,
                payload,
                headers,
                service=service,
                variant=variant,
                calls=calls,
                time=time,
            ):
                if path != "/v1/responses":
                    return service.respond(method, path, payload, headers)
                calls.append(payload)
                response = response_document(triage_document())
                if variant == "disable":
                    service.enabled = False
                elif variant == "expiry":
                    time[0] += timedelta(minutes=5)
                elif variant == "model":
                    response["model"] = "unapproved"
                else:
                    service.state["generation"] = service.state["lease"]["fence"] = 2
                    service.sha = "d" * 40
                return 200, {}, response

            with fixture_http(respond) as opener, tempfile.TemporaryDirectory() as directory:
                journal = receipts.CompletionJournal(Path(directory))
                client = github_client(opener)
                api = provider.OpenAI(
                    enabled_policy(),
                    client,
                    github.JsonTransport("api.openai.com", "fixture", opener=opener),
                    journal,
                )
                with self.subTest(variant=variant), self.assertRaises(automation.AutomationError):
                    api.propose(
                        "triage",
                        client.read_snapshot(NOW),
                        9001,
                        "interrupted",
                        "publisher",
                        1,
                        lambda time=time: time[0],
                    )
                receipt = journal.read("interrupted")
                self.assertEqual(receipt["response_id"], "resp_fixture")
                self.assertEqual(receipt["usage"]["input_tokens"], 100)
                self.assertEqual(len(calls), 1)
                allocation = service.state["allocations"][0]
                self.assertIsNone(allocation["actual_micro_usd"])
                self.assertIsNone(allocation["response_id"])
                self.assertGreater(allocation["reserved_micro_usd"], 0)
                if variant == "fence":
                    self.assertEqual(service.state["generation"], 2)
                if variant == "disable":
                    unchanged = copy.deepcopy(service.state)
                    with self.assertRaisesRegex(automation.Blocked, "disabled"):
                        api.reconcile_receipt("interrupted", "publisher", lambda time=time: time[0])
                    self.assertEqual(service.state, unchanged)
                    service.enabled = True
                if variant == "model":
                    with self.assertRaisesRegex(
                        automation.AutomationError, "receipt_requires_owner_reconciliation"
                    ):
                        api.reconcile_receipt("interrupted", "publisher", lambda time=time: time[0])
                    continue
                api.reconcile_receipt("interrupted", "publisher", lambda time=time: time[0])
                self.assertEqual(service.state["allocations"][0]["actual_micro_usd"], 260)
                self.assertEqual(service.state["allocations"][0]["response_id"], "resp_fixture")
                if variant == "expiry":
                    self.assertEqual(service.state["generation"], 2)
                before = copy.deepcopy(service.state)
                api.reconcile_receipt("interrupted", "publisher", lambda time=time: time[0])
                self.assertEqual(service.state, before)
                self.assertEqual(len(calls), 1)
                self.assertEqual(service.effects, [])

    def test_recovery_respects_fresh_sha_and_other_publishers(self):
        for variant in ("cas", "publisher", "cycle"):
            service = GitHubService()
            policy = enabled_policy()
            time = [NOW]
            if variant == "cycle":
                end = automation.utc_text(NOW + timedelta(seconds=1))
                policy = replace(policy, cycle_end=end)
                service.state["cycle_end"] = end
            seed_lease(service)
            service.state = json.loads(
                json.dumps(
                    automation.state_payload(
                        automation.allocate_request(
                            automation.parse_state(service.state),
                            policy,
                            "pending",
                            100,
                            NOW,
                        )
                    )
                )
            )
            reads = []

            def respond(
                method,
                path,
                payload,
                headers,
                service=service,
                variant=variant,
                reads=reads,
                time=time,
            ):
                if method == "GET" and path.startswith(github.STATE_ROUTE):
                    reads.append(path)
                    if variant == "cas" and len(reads) == 2:
                        service.state["actions_minutes"] = 42
                        service.sha = "d" * 40
                result = service.respond(method, path, payload, headers)
                if variant == "cycle" and len(reads) == 2:
                    time[0] = NOW + timedelta(seconds=2)
                return result

            with fixture_http(respond) as opener, tempfile.TemporaryDirectory() as directory:
                journal = receipts.CompletionJournal(Path(directory))
                journal.record(
                    receipts.completion_receipt(
                        automation.parse_state(service.state),
                        policy,
                        "pending",
                        response_document({}),
                    )
                )
                api = provider.OpenAI(
                    policy,
                    github_client(opener),
                    github.JsonTransport("api.openai.com", "fixture", opener=opener),
                    journal,
                )
                if variant == "publisher":
                    service.state["lease"]["run_id"] = "someone-else"
                with self.assertRaises(automation.AutomationError):
                    api.reconcile_receipt("pending", "publisher", lambda time=time: time[0])
                self.assertIsNone(service.state["allocations"][0]["actual_micro_usd"])
                self.assertFalse(any(row[0] == "PUT" for row in service.requests))
                if variant == "cas":
                    self.assertEqual(service.state["actions_minutes"], 42)


if __name__ == "__main__":
    unittest.main()
