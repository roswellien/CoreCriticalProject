"""Check a pull request's base branch, branch name and title against the project conventions.

The rules are described in "Names and formats" in docs/github-workflow.md. A PR
into `main` that does not come from `develop` is an error, because GitHub branch
protection is unavailable on this repository's plan. Branch names and titles
that break the documented formats are errors.

Inputs: --title, --head, --base and --author (the PR author's GitHub login).
Exit codes: 0 when there are no errors, 1 when there is at least one error, 2
for invalid command-line usage.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
import re
import sys
from typing import Mapping, TextIO

# The only list of area names in code. The area labels in docs/github-workflow.md
# and the area dropdown in .github/ISSUE_TEMPLATE/general.yml must match it;
# tests/test_pr_conventions.py checks that they do.
AREAS = ("launcher", "runtime", "renderer", "mod-tools", "content", "analysis", "ci", "website")
# Allowed in PR titles in addition to AREAS; it pairs with the `documentation` label.
DOCS_AREA = "docs"
BRANCH_TYPES = ("feature", "fix", "docs", "ci", "refactor")
MAX_TITLE_LENGTH = 72

# <username>/<type>/<issue>-<slug> or <username>/<type>/<slug>. GitHub usernames
# are at most 39 characters of letters, digits and inner hyphens.
BRANCH_PATTERN = re.compile(
    r"^(?P<user>[a-z0-9](?:[a-z0-9-]{0,37}[a-z0-9])?)"
    r"/(?P<type>" + "|".join(BRANCH_TYPES) + r")"
    r"/(?:[0-9]+-)?[a-z0-9]+(?:-[a-z0-9]+)*$"
)
# <Verb> <area>: <what changed>; the verb may be hyphenated, as in "Re-enable".
TITLE_PATTERN = re.compile(r"^[A-Z][a-z]+(?:-[a-z]+)* (?P<area>[A-Za-z-]+): \S.*$")

BRANCH_FORMAT = "<username>/<type>/<issue>-<slug>"
TITLE_FORMAT = "<Verb> <area>: <what changed>"
DOCS_REFERENCE = '"Names and formats" in docs/github-workflow.md'


@dataclass(frozen=True)
class Finding:
    level: str  # "error" or "warning"
    message: str


def check(title: str, head: str, base: str, author: str) -> list[Finding]:
    """Return every convention problem for one PR, errors first."""
    if base == "main":
        return _check_release(title, head)
    if base == "develop" and head == "main":
        return _check_sync(title)
    if base == "develop":
        return _check_branch(head, author) + _check_title(title)
    # PRs stacked on a topic branch are not checked.
    return []


def _check_release(title: str, head: str) -> list[Finding]:
    findings = []
    if head != "develop":
        findings.append(
            Finding("error", f"PRs into main come only from develop, not from {head!r} (docs/github-workflow.md).")
        )
    if not title.startswith("Release "):
        findings.append(Finding("error", f"A release PR title starts with 'Release ' ({DOCS_REFERENCE})."))
    return findings


def _check_sync(title: str) -> list[Finding]:
    if title.startswith("Sync main into develop"):
        return []
    return [Finding("error", f"A sync PR title starts with 'Sync main into develop' ({DOCS_REFERENCE}).")]


def _check_branch(head: str, author: str) -> list[Finding]:
    match = BRANCH_PATTERN.match(head)
    if match is None:
        return [Finding("error", f"Branch {head!r} does not match {BRANCH_FORMAT} ({DOCS_REFERENCE}).")]
    if match["user"] != author.lower():
        return [
            Finding("error", f"Branch {head!r} starts with {match['user']!r}, but the PR author is {author!r}.")
        ]
    return []


def _check_title(title: str) -> list[Finding]:
    findings = []
    match = TITLE_PATTERN.match(title)
    if match is None:
        findings.append(Finding("error", f"Title {title!r} does not match {TITLE_FORMAT} ({DOCS_REFERENCE})."))
    else:
        area = match["area"].lower()
        if area not in AREAS and area != DOCS_AREA:
            allowed = ", ".join(AREAS + (DOCS_AREA,))
            findings.append(Finding("error", f"Title area {match['area']!r} is not one of: {allowed}."))
    if title.endswith("."):
        findings.append(Finding("error", "Title ends with a period."))
    if len(title) > MAX_TITLE_LENGTH:
        findings.append(Finding("error", f"Title is {len(title)} characters; keep it to {MAX_TITLE_LENGTH}."))
    return findings


def _escape_workflow_command(text: str) -> str:
    """Escape text for a GitHub workflow command, so a crafted title cannot start a second command."""
    return text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def _summary_line(finding: Finding) -> str:
    # Backticks are removed so the PR author's text cannot close the code span and inject Markdown.
    message = finding.message.replace("`", "").replace("\r", " ").replace("\n", " ")
    return f"- **{finding.level}**: `{message}`\n"


def report(findings: list[Finding], env: Mapping[str, str], out: TextIO) -> None:
    """Print findings, as workflow commands and a step summary when running in GitHub Actions.

    `env` and `out` are parameters, not os.environ and sys.stdout, so tests never
    write into a real CI run's annotations or summary.
    """
    in_actions = bool(env.get("GITHUB_ACTIONS"))
    for finding in findings:
        if in_actions:
            out.write(f"::{finding.level} title=PR conventions::{_escape_workflow_command(finding.message)}\n")
        else:
            out.write(f"{finding.level}: {finding.message}\n")
    summary_path = env.get("GITHUB_STEP_SUMMARY")
    if in_actions and summary_path:
        with open(summary_path, "a", encoding="utf-8") as summary:
            summary.write("## PR conventions\n\n")
            if findings:
                summary.writelines(_summary_line(finding) for finding in findings)
            else:
                summary.write("No problems found.\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check a PR's base branch, branch name and title against the project conventions."
    )
    parser.add_argument("--title", required=True)
    parser.add_argument("--head", required=True, help="the PR's source branch")
    parser.add_argument("--base", required=True, help="the branch the PR merges into")
    parser.add_argument("--author", required=True, help="the PR author's GitHub login")
    args = parser.parse_args(argv)
    findings = check(args.title, args.head, args.base, args.author)
    report(findings, os.environ, sys.stdout)
    return 1 if any(finding.level == "error" for finding in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
