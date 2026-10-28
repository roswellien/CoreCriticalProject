"""Checks for tools/github/check_board.py, the read-only project board check."""

import contextlib
import importlib.util
import io
import sys
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def load_checker():
    spec = importlib.util.spec_from_file_location(
        "check_board", ROOT / "tools/github/check_board.py"
    )
    module = importlib.util.module_from_spec(spec)
    # Registered before running, because dataclasses look their module up in sys.modules.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


board = load_checker()

NOW = datetime(2026, 10, 28, 12, 0, tzinfo=UTC)
LABELS = ("enhancement", "area: ci")


def issue(
    number,
    *,
    is_open=True,
    completed=False,
    closed_days_ago=None,
    idle_days=0,
    assignees=("someone",),
    labels=LABELS,
):
    closed_at = None if closed_days_ago is None else NOW - timedelta(days=closed_days_ago)
    return board.Issue(
        number=number,
        is_open=is_open,
        closed_as_completed=completed,
        closed_at=closed_at,
        updated_at=NOW - timedelta(days=idle_days),
        assignees=tuple(assignees),
        labels=tuple(labels),
    )


def pull(
    number,
    *,
    state="OPEN",
    base="develop",
    head="carson-nr/fix/1-x",
    changed_files=3,
    merged_days_ago=None,
    closes=(1,),
    title="Fix launcher: something",
):
    merged_at = None if merged_days_ago is None else NOW - timedelta(days=merged_days_ago)
    return board.PullRequest(
        number=number,
        title=title,
        state=state,
        base=base,
        head=head,
        changed_files=changed_files,
        merged_at=merged_at,
        closes=tuple(closes),
    )


def card(number, status="Backlog", priority="P1"):
    return board.Card(issue_number=number, status=status, priority=priority)


def problems(issues=(), pulls=(), cards=()):
    findings = board.find_problems(list(issues), list(pulls), list(cards), NOW)
    return [(finding.subject, finding.problem) for finding in findings]


class HealthyBoardTests(unittest.TestCase):
    def test_issue_in_review_with_its_open_pr_is_clean(self):
        self.assertEqual(problems([issue(1)], [pull(2)], [card(1, "In review")]), [])

    def test_closed_issue_done_with_its_merged_pr_is_clean(self):
        found = problems(
            [issue(1, is_open=False, completed=True, closed_days_ago=1)],
            [pull(2, state="MERGED", merged_days_ago=1)],
            [card(1, "Done")],
        )
        self.assertEqual(found, [])


class IssueTests(unittest.TestCase):
    def test_open_issue_missing_from_board(self):
        self.assertEqual(problems([issue(1)]), [("issue #1", "is not on the board")])

    def test_missing_type_and_area_labels(self):
        found = problems([issue(1, labels=())], cards=[card(1)])
        self.assertEqual(
            found, [("issue #1", "has no type label"), ("issue #1", "has no area label")]
        )

    def test_triage_label_stands_in_for_a_type(self):
        found = problems([issue(1, labels=("needs-triage", "area: launcher"))], cards=[card(1)])
        self.assertEqual(found, [])

    def test_missing_priority(self):
        self.assertEqual(
            problems([issue(1)], cards=[card(1, priority="")]), [("issue #1", "has no priority")]
        )

    def test_closed_issues_need_no_labels_or_priority(self):
        found = problems([issue(1, is_open=False, labels=())], cards=[card(1, "Done", priority="")])
        self.assertEqual(found, [])


class CardStatusTests(unittest.TestCase):
    def test_open_issue_marked_done(self):
        self.assertEqual(
            problems([issue(1)], cards=[card(1, "Done")]),
            [("issue #1", "is open but its card is Done")],
        )

    def test_closed_issue_not_done(self):
        found = problems([issue(1, is_open=False)], cards=[card(1, "In progress")])
        self.assertEqual(found, [("issue #1", "is closed but its card is In progress")])

    def test_in_progress_without_assignee(self):
        found = problems([issue(1, assignees=())], cards=[card(1, "In progress")])
        self.assertEqual(found, [("issue #1", "is In progress with nobody assigned")])

    def test_in_progress_gone_quiet(self):
        found = problems([issue(1, idle_days=8)], cards=[card(1, "In progress")])
        self.assertEqual(found, [("issue #1", "is In progress but hasn't changed for 8 days")])

    def test_in_progress_within_a_week_is_fine(self):
        self.assertEqual(problems([issue(1, idle_days=6)], cards=[card(1, "In progress")]), [])

    def test_in_review_without_open_pr(self):
        found = problems(
            [issue(1)], [pull(2, state="MERGED", merged_days_ago=30)], [card(1, "In review")]
        )
        self.assertEqual(found, [("issue #1", "is In review but no open PR closes it")])


class ClosedIssueTests(unittest.TestCase):
    def test_recently_completed_without_merged_pr(self):
        found = problems(
            [issue(1, is_open=False, completed=True, closed_days_ago=2)],
            [pull(2, state="CLOSED", changed_files=0)],
            [card(1, "Done")],
        )
        self.assertEqual(
            found, [("issue #1", "was closed as completed, but no merged PR closes it")]
        )

    def test_old_closures_stay_quiet(self):
        found = problems(
            [issue(1, is_open=False, completed=True, closed_days_ago=30)], cards=[card(1, "Done")]
        )
        self.assertEqual(found, [])

    def test_closed_as_not_planned_needs_no_pr(self):
        found = problems([issue(1, is_open=False, closed_days_ago=2)], cards=[card(1, "Done")])
        self.assertEqual(found, [])


class PullRequestTests(unittest.TestCase):
    def test_empty_pr(self):
        found = problems([issue(1)], [pull(2, changed_files=0)], [card(1, "In review")])
        self.assertEqual(found, [("PR #2", "has no changed files")])

    def test_topic_branch_into_main(self):
        found = problems([issue(1)], [pull(2, base="main")], [card(1, "In review")])
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0][0], "PR #2")
        self.assertIn("PRs into main come only from develop", found[0][1])

    def test_pr_without_issue(self):
        self.assertEqual(
            problems(pulls=[pull(2, closes=())]), [("PR #2", "doesn't close an issue")]
        )

    def test_release_and_sync_prs_need_no_issue(self):
        release = pull(2, base="main", head="develop", closes=(), title="Release launcher 1.0.45")
        sync = pull(
            3, base="develop", head="main", closes=(), title="Sync main into develop after 1.0.45"
        )
        self.assertEqual(problems(pulls=[release, sync]), [])

    def test_merged_pr_with_issue_still_open(self):
        found = problems(
            [issue(1)], [pull(2, state="MERGED", merged_days_ago=1)], [card(1, "In review")]
        )
        self.assertIn(("PR #2", "merged, but issue #1 is still open"), found)

    def test_old_merged_prs_stay_quiet(self):
        found = problems([issue(1)], [pull(2, state="MERGED", merged_days_ago=30)], [card(1)])
        self.assertEqual(found, [])

    def test_closed_unmerged_prs_are_ignored(self):
        self.assertEqual(problems(pulls=[pull(2, state="CLOSED", changed_files=0, closes=())]), [])


class ParsingTests(unittest.TestCase):
    def test_parses_gh_json(self):
        issues = board.parse_issues(
            [
                {
                    "number": 22,
                    "state": "CLOSED",
                    "stateReason": "COMPLETED",
                    "closedAt": "2026-10-28T02:45:05Z",
                    "updatedAt": "2026-10-28T02:45:05Z",
                    "assignees": [{"login": "roswellien"}],
                    "labels": [{"name": "enhancement"}, {"name": "area: ci"}],
                }
            ]
        )
        self.assertEqual(issues[0].closed_at, datetime(2026, 10, 28, 2, 45, 5, tzinfo=UTC))
        self.assertTrue(issues[0].closed_as_completed)
        self.assertEqual(issues[0].labels, ("enhancement", "area: ci"))

        pulls = board.parse_pulls(
            [
                {
                    "number": 31,
                    "title": "Add CI: group generated release notes by PR label",
                    "state": "OPEN",
                    "baseRefName": "main",
                    "headRefName": "copilot/generate-release-notes-from-prs",
                    "changedFiles": 0,
                    "mergedAt": None,
                    "closingIssuesReferences": [{"number": 21}],
                }
            ]
        )
        self.assertEqual(pulls[0].closes, (21,))
        self.assertIsNone(pulls[0].merged_at)

    def test_only_this_repositorys_issue_cards_are_kept(self):
        ours = "https://github.com/roswellien/MW3Recomp-Private"
        cards = board.parse_cards(
            {
                "items": [
                    {
                        "content": {"type": "Issue", "number": 21},
                        "repository": ours,
                        "status": "Ready",
                        "priority": "P2",
                    },
                    {
                        "content": {"type": "Issue", "number": 22},
                        "repository": "https://github.com/roswellien/MW3Recomp",
                        "status": "Ready",
                    },
                    {
                        "content": {"type": "PullRequest", "number": 31},
                        "repository": ours,
                        "status": "Backlog",
                    },
                    {"content": {"type": "DraftIssue"}, "status": "Backlog"},
                ]
            }
        )
        self.assertEqual(cards, [board.Card(issue_number=21, status="Ready", priority="P2")])


class ExitCodeTests(unittest.TestCase):
    def test_missing_gh_exits_2_not_1(self):
        # Exit code 1 means "problems found", so a missing gh must not end there.
        stderr = io.StringIO()
        with (
            mock.patch.object(board.subprocess, "run", side_effect=FileNotFoundError("gh")),
            contextlib.redirect_stderr(stderr),
        ):
            self.assertEqual(board.main([]), 2)
        self.assertIn("gh is not installed", stderr.getvalue())

    def test_failing_gh_exits_2(self):
        failed = mock.Mock(returncode=1, stdout="", stderr="missing project scope")
        stderr = io.StringIO()
        with (
            mock.patch.object(board.subprocess, "run", return_value=failed),
            contextlib.redirect_stderr(stderr),
        ):
            self.assertEqual(board.main([]), 2)
        self.assertIn("missing project scope", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
