"""List where the project board, the issues and the pull requests disagree.

The rules are described in "Project board" and "Names and formats" in
docs/github-workflow.md. This only reads: it changes nothing on GitHub and uses
the caller's own `gh` login, which needs the `project` scope
(`gh auth refresh -s project`).

Exit codes: 0 when nothing is found, 1 when at least one problem is found,
2 when `gh` fails or its output can't be read.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

# The base-branch rule lives in the PR conventions check; reuse it rather than repeat it.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_pr_conventions

REPOSITORY = "roswellien/MW3Recomp-Private"
BOARD_OWNER = "roswellien"
BOARD_NUMBER = 1

TYPE_LABELS = ("bug", "enhancement", "documentation", "playtest", "research", "release")
# Issues from the General form carry this until triage gives them a type.
TRIAGE_LABEL = "needs-triage"
AREA_LABELS = tuple(f"area: {area}" for area in check_pr_conventions.AREAS)

# A card In progress whose issue hasn't changed for this long probably isn't.
STALE_AFTER = timedelta(days=7)
# Merged PRs and closed issues older than this aren't checked, so old history stays quiet.
RECENT = timedelta(days=14)

# The most items one read asks for. A read that comes back this full may have been cut
# short, so it is treated as a failed read rather than checked as if it were complete.
LIST_LIMIT = 1000
INTEGRATION_BRANCH = "develop"


@dataclass(frozen=True)
class Issue:
    number: int
    is_open: bool
    closed_as_completed: bool
    closed_at: datetime | None
    updated_at: datetime
    assignees: tuple[str, ...]
    labels: tuple[str, ...]


@dataclass(frozen=True)
class PullRequest:
    number: int
    title: str
    state: str  # "OPEN", "CLOSED" or "MERGED"
    base: str
    head: str
    changed_files: int
    merged_at: datetime | None
    closes: tuple[int, ...]  # this repository's issues from "Closes #N" or a manual link


@dataclass(frozen=True)
class Card:
    issue_number: int
    status: str  # empty when unset
    priority: str  # empty when unset


@dataclass(frozen=True)
class Finding:
    subject: str  # "issue #12" or "PR #34"
    problem: str
    action: str


def find_problems(
    issues: list[Issue], pulls: list[PullRequest], cards: list[Card], now: datetime
) -> list[Finding]:
    """Return every disagreement between the board, issues and PRs, issues first."""
    issues_by_number = {issue.number: issue for issue in issues}
    cards_by_issue = {card.issue_number: card for card in cards}
    open_pulls_by_issue = _pulls_closing_each_issue(pulls, "OPEN")
    merged_pulls_by_issue = _pulls_closing_each_issue(pulls, "MERGED")

    findings: list[Finding] = []
    for issue in sorted(issues, key=lambda issue: issue.number):
        card = cards_by_issue.get(issue.number)
        findings += _check_issue_labels(issue)
        findings += _check_card(issue, card, open_pulls_by_issue.get(issue.number, []), now)
        findings += _check_closed_issue(issue, merged_pulls_by_issue.get(issue.number, []), now)
    for pull in sorted(pulls, key=lambda pull: pull.number):
        findings += _check_pull(pull, issues_by_number, now)
    return findings


def _pulls_closing_each_issue(pulls: list[PullRequest], state: str) -> dict[int, list[PullRequest]]:
    """Map each issue number to the PRs in `state` that close it."""
    pulls_by_issue: dict[int, list[PullRequest]] = {}
    for pull in pulls:
        if pull.state != state:
            continue
        for issue_number in pull.closes:
            pulls_by_issue.setdefault(issue_number, []).append(pull)
    return pulls_by_issue


def _check_issue_labels(issue: Issue) -> list[Finding]:
    if not issue.is_open:
        return []
    subject = f"issue #{issue.number}"
    findings = []
    has_type = any(label in TYPE_LABELS for label in issue.labels)
    if not has_type and TRIAGE_LABEL not in issue.labels:
        findings.append(
            Finding(subject, "has no type label", f"add one of: {', '.join(TYPE_LABELS)}")
        )
    if not any(label in AREA_LABELS for label in issue.labels):
        findings.append(
            Finding(subject, "has no area label", "add at least one 'area: <name>' label")
        )
    return findings


def _check_card(
    issue: Issue, card: Card | None, open_pulls: list[PullRequest], now: datetime
) -> list[Finding]:
    subject = f"issue #{issue.number}"
    if card is None:
        if issue.is_open:
            return [Finding(subject, "is not on the board", "add it to the board")]
        return []
    if not issue.is_open:
        if card.status != "Done":
            return [
                Finding(
                    subject,
                    f"is closed but its card is {_status_name(card)}",
                    "set the card to Done",
                )
            ]
        return []

    findings = []
    if card.status == "Done":
        findings.append(
            Finding(
                subject,
                "is open but its card is Done",
                "set the card to where the work is, or close the issue",
            )
        )
    if not card.priority:
        findings.append(Finding(subject, "has no priority", "set P0, P1 or P2 on its card"))
    if card.status == "In progress":
        if not issue.assignees:
            findings.append(
                Finding(
                    subject,
                    "is In progress with nobody assigned",
                    "assign whoever is working on it",
                )
            )
        if now - issue.updated_at > STALE_AFTER:
            idle_days = (now - issue.updated_at).days
            findings.append(
                Finding(
                    subject,
                    f"is In progress but hasn't changed for {idle_days} days",
                    "confirm someone is still on it, or move the card back to Ready",
                )
            )
    if card.status == "In review" and not open_pulls:
        findings.append(
            Finding(
                subject,
                "is In review but no open PR closes it",
                "move the card to match, or add 'Closes #N' to its PR",
            )
        )
    return findings


def _check_closed_issue(
    issue: Issue, merged_pulls: list[PullRequest], now: datetime
) -> list[Finding]:
    if issue.is_open or not issue.closed_as_completed or issue.closed_at is None:
        return []
    if now - issue.closed_at > RECENT or merged_pulls:
        return []
    return [
        Finding(
            f"issue #{issue.number}",
            "was closed as completed, but no merged PR closes it",
            "check the work landed; link the PR that did it (the issue's Development box), or reopen it",
        )
    ]


def _check_pull(
    pull: PullRequest, issues_by_number: dict[int, Issue], now: datetime
) -> list[Finding]:
    subject = f"PR #{pull.number}"
    if pull.state == "MERGED":
        # A stacked PR merged into another topic branch hasn't reached the integration
        # branch yet, so its issue rightly stays open.
        reached_integration = pull.base == INTEGRATION_BRANCH
        if not reached_integration or pull.merged_at is None or now - pull.merged_at > RECENT:
            return []
        still_open = [number for number in pull.closes if _is_open(issues_by_number.get(number))]
        return [
            Finding(
                subject,
                f"merged, but issue #{number} is still open",
                f"close #{number} with a comment naming PR #{pull.number}",
            )
            for number in still_open
        ]
    if pull.state != "OPEN":
        return []

    findings = []
    if pull.changed_files == 0:
        findings.append(Finding(subject, "has no changed files", "push the work, or close the PR"))
    # Only the base-branch rule is an error there; the author only affects naming
    # warnings, which are dropped here, so it is left empty.
    base_errors = [
        finding
        for finding in check_pr_conventions.check(pull.title, pull.head, pull.base, "")
        if finding.level == "error"
    ]
    for error in base_errors:
        findings.append(Finding(subject, error.message.rstrip("."), "change the PR's base branch"))
    is_release_or_sync = (pull.head, pull.base) in (("develop", "main"), ("main", "develop"))
    if not pull.closes and not is_release_or_sync:
        findings.append(
            Finding(
                subject,
                "doesn't close an issue",
                "add 'Closes #N' to its description, filing the issue first",
            )
        )
    return findings


def _is_open(issue: Issue | None) -> bool:
    return issue is not None and issue.is_open


def _status_name(card: Card) -> str:
    return card.status or "without a status"


# Reading from GitHub


def _parse_time(text: str | None) -> datetime | None:
    if not text:
        return None
    # gh prints UTC times ending in "Z"; fromisoformat reads that as UTC.
    return datetime.fromisoformat(text)


def _run_gh(arguments: list[str]) -> list[dict] | dict:
    # The return code is checked below so the error can carry gh's own message.
    try:
        result = subprocess.run(
            ["gh", *arguments], capture_output=True, text=True, encoding="utf-8", check=False
        )
    except FileNotFoundError as error:
        # Without this, a missing gh would end in a traceback and exit code 1, which means
        # "problems found" to anyone scripting around this check.
        raise RuntimeError("gh is not installed or not on PATH") from error
    if result.returncode != 0:
        raise RuntimeError(f"gh {' '.join(arguments[:2])} failed: {result.stderr.strip()}")
    return json.loads(result.stdout)


def parse_issues(rows: Iterable[dict]) -> list[Issue]:
    issues = []
    for row in rows:
        updated_at = _parse_time(row["updatedAt"])
        if updated_at is None:
            raise ValueError(f"issue #{row['number']} has no updatedAt")
        issues.append(
            Issue(
                number=row["number"],
                is_open=row["state"] == "OPEN",
                closed_as_completed=row.get("stateReason") == "COMPLETED",
                closed_at=_parse_time(row.get("closedAt")),
                updated_at=updated_at,
                assignees=tuple(person["login"] for person in row["assignees"]),
                labels=tuple(label["name"] for label in row["labels"]),
            )
        )
    return issues


def parse_pulls(rows: Iterable[dict]) -> list[PullRequest]:
    return [
        PullRequest(
            number=row["number"],
            title=row["title"],
            state=row["state"],
            base=row["baseRefName"],
            head=row["headRefName"],
            changed_files=row["changedFiles"],
            merged_at=_parse_time(row.get("mergedAt")),
            closes=_issues_closed_here(row["closingIssuesReferences"]),
        )
        for row in rows
    ]


def _issues_closed_here(references: list[dict]) -> tuple[int, ...]:
    # "Closes other/project#1" is a reference too; kept as a bare number it would pass
    # for this repository's issue #1.
    our_issue_url = f"https://github.com/{REPOSITORY}/issues/"
    return tuple(
        reference["number"]
        for reference in references
        if reference["url"].startswith(our_issue_url)
    )


def parse_cards(board: dict) -> list[Card]:
    # Only this repository's issues are checked: PR and draft cards are skipped, and so
    # are issues from other repositories, whose numbers could match ours.
    repository_url = f"https://github.com/{REPOSITORY}"
    return [
        Card(
            issue_number=item["content"]["number"],
            status=item.get("status") or "",
            priority=item.get("priority") or "",
        )
        for item in board["items"]
        if item.get("content", {}).get("type") == "Issue"
        and item.get("repository") == repository_url
    ]


def fetch() -> tuple[list[Issue], list[PullRequest], list[Card]]:
    issue_fields = "number,state,stateReason,closedAt,updatedAt,assignees,labels"
    pull_fields = (
        "number,title,state,baseRefName,headRefName,changedFiles,mergedAt,closingIssuesReferences"
    )
    every_item = ["-R", REPOSITORY, "--state", "all", "--limit", str(LIST_LIMIT)]
    issues = _run_gh(["issue", "list", *every_item, "--json", issue_fields])
    _require_complete(len(issues), "issues")
    pulls = _run_gh(["pr", "list", *every_item, "--json", pull_fields])
    _require_complete(len(pulls), "pull requests")
    board_options = ["--owner", BOARD_OWNER, "--limit", str(LIST_LIMIT), "--format", "json"]
    board = _run_gh(["project", "item-list", str(BOARD_NUMBER), *board_options])
    _require_complete(len(board["items"]), "board items")
    if board["totalCount"] > len(board["items"]):
        raise RuntimeError(
            f"the board has {board['totalCount']} items but only {len(board['items'])} were read"
        )
    return parse_issues(issues), parse_pulls(pulls), parse_cards(board)


def _require_complete(count: int, what: str) -> None:
    # Checking a partial read would report missing cards and PRs that exist, or a clean
    # board that isn't, so stop instead and say how to fix it.
    if count >= LIST_LIMIT:
        raise RuntimeError(
            f"read {count} {what}, the most one read returns, so some may be missing; "
            "raise LIST_LIMIT in tools/github/check_board.py"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="List where the project board, the issues and the pull requests disagree (read-only)."
    )
    parser.parse_args(argv)
    try:
        issues, pulls, cards = fetch()
    except (RuntimeError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"Could not read GitHub: {error}", file=sys.stderr)
        return 2
    findings = find_problems(issues, pulls, cards, datetime.now(UTC))
    for finding in findings:
        print(f"{finding.subject} {finding.problem}: {finding.action}.")
    if not findings:
        print("No problems found.")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
