"""Authored fixtures for new automation authority/state behavior, absent from board tests."""

import copy
import json
import sys
import unittest
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/github"))
import openai_automation as automation

NOW = datetime(2026, 11, 7, 12, tzinfo=UTC)


def snapshot_document():
    return automation.strict_json((ROOT / "tests/fixtures/openai_automation_snapshot.json").read_bytes())


def policy_document():
    return automation.strict_json((ROOT / "tools/github/openai_automation_policy.json").read_bytes())


def triage_document():
    return {"issue_number": 9001, "revision": "a" * 64,
            "labels": ["enhancement", "area: ci"], "priority": "P1",
            "next_action": "Validate the authored example and record the result."}


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
        for change in ({"extra": True}, {"repository": "someone/else"}, {"enabled": "true"},
                       {"api_budget_micro_usd": -1}, {"api_budget_micro_usd": True},
                       {"api_budget_micro_usd": float("inf")}, {"cycle_start": "2026-11-01T00:00:00Z"}):
            with self.subTest(change=change), self.assertRaises(automation.AutomationError):
                automation.Policy.parse(policy_document() | change)

    def test_json_rejects_duplicate_keys_non_finite_and_malformed_documents(self):
        for value in ('{"enabled":false,"enabled":true}', '{"cost":NaN}', '{"cost":Infinity}', '{'):
            with self.subTest(value=value), self.assertRaises(automation.AutomationError):
                automation.strict_json(value)

    def test_complete_snapshot_reports_only_unclaimed_ready(self):
        snapshot = automation.Snapshot.parse(snapshot_document())
        self.assertEqual(snapshot.eligible_ready(), (9001,))
        self.assertEqual(snapshot.issue(9002).assignees, ("example-maintainer",))
        for change in ({"complete": False}, {"repository": "another/repo"},
                       {"base_sha": "develop"}):
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
        for change in ({"status": "Ready"}, {"status": "Done"}, {"assignees": ["bot"]},
                       {"issue_number": 9002}, {"revision": "b" * 64},
                       {"labels": ["enhancement", "area: ci", "automation-ready"]},
                       {"priority": "P9"}, {"next_action": "${{ secrets.OPENAI_API_KEY }}"},
                       {"next_action": "$(run-command)"}, {"next_action": "https://attacker.test"},
                       {"next_action": "<script>execute()</script>"}, {"next_action": "x" * 501}):
            with self.subTest(change=change), self.assertRaises(automation.AutomationError):
                automation.TriageProposal.parse(triage_document() | change, snapshot, 9001)

    def test_summary_ids_and_text_cannot_introduce_other_targets(self):
        snapshot = automation.Snapshot.parse(snapshot_document())
        entry = {"issue_number": 9001, "summary": "The authored example needs validation.",
                 "suggested_priority": "P1", "next_action": "Run the fixture check."}
        self.assertEqual(automation.parse_summary({"entries": [entry]}, snapshot)[0].issue_number, 9001)
        for entries in ([entry, entry], [entry | {"issue_number": 19}],
                        [entry | {"summary": "<img src=credential>"}]):
            with self.subTest(entries=entries), self.assertRaises(automation.AutomationError):
                automation.parse_summary({"entries": entries}, snapshot)


if __name__ == "__main__":
    unittest.main()
