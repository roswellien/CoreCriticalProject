"""Inactive automation foundation: strict contracts, state transitions and offline preview.

This module owns authority and money decisions. Adapters may execute only its named
operations; issue text and provider output are data, never control instructions.
Runtime admission is deliberately closed until the worker/maintenance rollout lands.
All persistent money is integer micro-USD, times are UTC, and revisions are explicit.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass, fields, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_board import AREA_LABELS, BOARD_NUMBER, BOARD_OWNER, REPOSITORY, TYPE_LABELS

BOARD_ID = "PVT_kwHODf7y6M4BpC8L"
PRIORITY_FIELD = "PVTSSF_lAHODf7y6M4BpC8LzhngSb0"
PRIORITY_OPTIONS = {"P0": "79628723", "P1": "0a877460", "P2": "da944a9c"}
NEXT_ACTION_FIELD = "PVTF_lAHODf7y6M4BpC8LzhoZL5o"
STATE_BRANCH = "roswellien/ci/260-automation-state"
STATE_PATH = "openai-automation/state.json"
MAX_DOCUMENT_BYTES = 2_000_000
MAX_ITEMS = 1000
RUNTIME_CAPABILITIES = frozenset({"foundation"})
REQUIRED_CAPABILITIES = frozenset({"foundation", "worker", "maintenance"})
PREREQUISITES = (
    "credits", "project_cap", "secret_isolation", "platform_no_merge",
    "app_identity", "projects_identity", "ready_setters", "hosted_data", "canary",
)


class AutomationError(Exception):
    """A fixed, non-sensitive error code suitable for logs."""


class Blocked(AutomationError):
    """Configuration, authority or uncertain state requires owner attention."""


class Conflict(Blocked):
    """A remote precondition changed; reread, never replay the stale write."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise AutomationError(code)


def strict_json(text: str | bytes) -> Any:
    def unique_object(pairs: list[tuple[str, Any]]) -> dict:
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate_json_key")
            result[key] = value
        return result

    def reject_constant(value: str) -> None:
        raise AutomationError("non_finite_json_number")

    try:
        require(len(text) <= MAX_DOCUMENT_BYTES, "document_too_large")
        return json.loads(text, object_pairs_hook=unique_object, parse_constant=reject_constant)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise AutomationError("invalid_json") from error


def exact_object(value: Any, names: set[str]) -> dict:
    require(type(value) is dict and set(value) == names, "invalid_object_fields")
    return value


def integer(value: Any, minimum: int = 0, maximum: int = 10**15) -> int:
    require(type(value) is int and minimum <= value <= maximum, "invalid_integer")
    return value


def boolean(value: Any) -> bool:
    require(type(value) is bool, "invalid_boolean")
    return value


def text_value(value: Any, maximum: int, *, empty: bool = False) -> str:
    require(type(value) is str, "invalid_text")
    require((empty or bool(value.strip())) and len(value.encode("utf-8")) <= maximum,
            "invalid_text_length")
    require(not any(ord(char) < 32 and char not in "\n\t" for char in value), "control_text")
    return value


def identifier(value: Any, pattern: str) -> str:
    require(type(value) is str and re.fullmatch(pattern, value) is not None, "invalid_id")
    return value


def instant(value: Any) -> datetime:
    try:
        require(type(value) is str and value.endswith("Z"), "invalid_utc_time")
        parsed = datetime.fromisoformat(value)
        require(parsed.tzinfo == UTC, "invalid_utc_time")
        return parsed
    except ValueError as error:
        raise AutomationError("invalid_utc_time") from error


def utc_text(value: datetime) -> str:
    require(value.tzinfo == UTC, "invalid_utc_time")
    return value.isoformat().replace("+00:00", "Z")


def string_list(value: Any, allowed: tuple[str, ...] | None = None) -> tuple[str, ...]:
    require(type(value) is list and len(value) <= 100, "invalid_list")
    result = tuple(text_value(item, 100) for item in value)
    require(len(set(result)) == len(result), "duplicate_list_value")
    require(allowed is None or all(item in allowed for item in result), "disallowed_label")
    return result


def fingerprint(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Policy:
    version: int
    repository: str
    board_id: str
    enabled: bool
    rollout_complete: bool
    controller_sha: str | None
    model: str | None
    effort: str | None
    input_price_micro_usd_per_million: int | None
    output_price_micro_usd_per_million: int | None
    api_budget_micro_usd: int | None
    request_budget_micro_usd: int | None
    actions_budget_minutes: int | None
    cycle_start: str | None
    cycle_end: str | None
    max_input_bytes: int
    max_output_tokens: int
    headroom_percent: int
    prerequisites: dict[str, bool]

    @classmethod
    def parse(cls, value: Any) -> Policy:
        row = exact_object(value, {field.name for field in fields(cls)})
        require(integer(row["version"]) == 1, "unsupported_policy_version")
        require(row["repository"] == REPOSITORY and row["board_id"] == BOARD_ID, "wrong_scope")
        for name in ("enabled", "rollout_complete"):
            boolean(row[name])
        if row["controller_sha"] is not None:
            identifier(row["controller_sha"], r"[0-9a-f]{40}")
        if row["model"] is not None:
            identifier(row["model"], r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}")
        require(row["effort"] in (None, "none", "low", "medium", "high", "xhigh"),
                "invalid_effort")
        for name in ("input_price_micro_usd_per_million", "output_price_micro_usd_per_million",
                     "api_budget_micro_usd", "request_budget_micro_usd", "actions_budget_minutes"):
            if row[name] is not None:
                integer(row[name], 1)
        require((row["cycle_start"] is None) == (row["cycle_end"] is None), "incomplete_cycle")
        if row["cycle_start"] is not None:
            require(instant(row["cycle_start"]) < instant(row["cycle_end"]), "invalid_cycle")
        integer(row["max_input_bytes"], 1, 128_000)
        integer(row["max_output_tokens"], 1, 16_000)
        integer(row["headroom_percent"], 10, 100)
        for approved in exact_object(row["prerequisites"], set(PREREQUISITES)).values():
            boolean(approved)
        return cls(**row)


def configuration_blockers(policy: Policy, now: datetime) -> tuple[str, ...]:
    blockers = []
    if not policy.enabled:
        blockers.append("disabled")
    if not policy.rollout_complete:
        blockers.append("rollout_incomplete")
    for name in ("controller_sha", "model", "effort", "input_price_micro_usd_per_million",
                 "output_price_micro_usd_per_million", "api_budget_micro_usd",
                 "request_budget_micro_usd", "actions_budget_minutes", "cycle_start", "cycle_end"):
        if getattr(policy, name) is None:
            blockers.append(f"missing_{name}")
    if policy.cycle_start is not None and not (instant(policy.cycle_start) <= now
                                              < instant(policy.cycle_end)):
        blockers.append("credit_cycle_inactive")
    blockers.extend(f"unverified_{name}" for name in PREREQUISITES
                    if not policy.prerequisites[name])
    return tuple(blockers)


def require_runtime_capabilities() -> None:
    # A configuration edit must never activate unfinished worker/maintenance code.
    if not REQUIRED_CAPABILITIES <= RUNTIME_CAPABILITIES:
        raise Blocked("foundation_rollout_incomplete")


@dataclass(frozen=True)
class Issue:
    number: int
    item_id: str
    title: str
    body: str
    open: bool
    labels: tuple[str, ...]
    assignees: tuple[str, ...]
    status: str
    priority: str
    next_action: str
    revision: str

    @classmethod
    def parse(cls, value: Any) -> Issue:
        row = dict(exact_object(value, {field.name for field in fields(cls)}))
        integer(row["number"], 1, 2**31 - 1)
        identifier(row["item_id"], r"PVTI_[A-Za-z0-9_-]{1,100}")
        text_value(row["title"], 512)
        text_value(row["body"], 16_000, empty=True)
        boolean(row["open"])
        row["labels"] = string_list(row["labels"])
        row["assignees"] = string_list(row["assignees"])
        require(row["status"] in ("", "Backlog", "Ready", "In progress", "In review", "Done"),
                "invalid_status")
        require(row["priority"] in ("", *PRIORITY_OPTIONS), "invalid_priority")
        text_value(row["next_action"], 2000, empty=True)
        identifier(row["revision"], r"[0-9a-f]{64}")
        return cls(**row)


@dataclass(frozen=True)
class Snapshot:
    repository: str
    board_id: str
    base_sha: str
    captured_at: str
    issues: tuple[Issue, ...]
    implementation_issues: tuple[int, ...]

    @classmethod
    def parse(cls, value: Any) -> Snapshot:
        row = exact_object(value, {"version", "repository", "board_id", "base_sha", "captured_at",
                                   "complete", "issues", "implementation_issues"})
        require(row["version"] == 1 and type(row["version"]) is int, "unsupported_snapshot_version")
        require(row["repository"] == REPOSITORY and row["board_id"] == BOARD_ID, "wrong_scope")
        require(row["complete"] is True, "incomplete_snapshot")
        identifier(row["base_sha"], r"[0-9a-f]{40}")
        instant(row["captured_at"])
        require(type(row["issues"]) is list and len(row["issues"]) <= MAX_ITEMS, "invalid_issues")
        issues = tuple(Issue.parse(issue) for issue in row["issues"])
        require(len({issue.number for issue in issues}) == len(issues), "duplicate_issue")
        require(len({issue.item_id for issue in issues}) == len(issues), "duplicate_item")
        references = row["implementation_issues"]
        require(type(references) is list and len(references) <= MAX_ITEMS, "invalid_pr_references")
        references = tuple(integer(number, 1, 2**31 - 1) for number in references)
        require(len(set(references)) == len(references), "duplicate_pr_reference")
        return cls(row["repository"], row["board_id"], row["base_sha"], row["captured_at"],
                   issues, references)

    def issue(self, number: int) -> Issue:
        for issue in self.issues:
            if issue.number == number:
                return issue
        raise AutomationError("unknown_issue")

    def eligible_ready(self) -> tuple[int, ...]:
        return tuple(issue.number for issue in self.issues if issue.open and issue.status == "Ready"
                     and not issue.assignees and issue.number not in self.implementation_issues)


def proposal_text(value: Any, maximum: int) -> str:
    value = text_value(value, maximum)
    # Only plain review text is published. Links are constructed from validated IDs.
    require(not re.search(r"https?://|www\.|[<>`]|\$\{|\$\(|\x1b", value, re.IGNORECASE),
            "unsafe_proposal_text")
    return value


@dataclass(frozen=True)
class TriageProposal:
    issue_number: int
    revision: str
    labels: tuple[str, ...]
    priority: str
    next_action: str

    @classmethod
    def parse(cls, value: Any, snapshot: Snapshot, expected_issue: int) -> TriageProposal:
        row = exact_object(value, {field.name for field in fields(cls)})
        require(integer(row["issue_number"], 1) == expected_issue, "wrong_issue")
        issue = snapshot.issue(expected_issue)
        require(issue.open, "closed_issue")
        require(row["revision"] == issue.revision, "stale_proposal")
        labels = string_list(row["labels"], TYPE_LABELS + AREA_LABELS)
        require(sum(label in TYPE_LABELS for label in labels) == 1
                and any(label in AREA_LABELS for label in labels), "missing_triage_labels")
        require(row["priority"] in PRIORITY_OPTIONS, "invalid_priority")
        return cls(expected_issue, issue.revision, labels, row["priority"],
                   proposal_text(row["next_action"], 500))

    def merged_labels(self, issue: Issue) -> tuple[str, ...]:
        # Append only: human labels and captures are never silently removed.
        return tuple(sorted(set(issue.labels) | set(self.labels)))


@dataclass(frozen=True)
class SummaryEntry:
    issue_number: int
    summary: str
    suggested_priority: str
    next_action: str


def parse_summary(value: Any, snapshot: Snapshot) -> tuple[SummaryEntry, ...]:
    row = exact_object(value, {"entries"})
    require(type(row["entries"]) is list and len(row["entries"]) <= MAX_ITEMS,
            "invalid_summary_entries")
    entries = []
    seen = set()
    for entry in row["entries"]:
        exact_object(entry, {field.name for field in fields(SummaryEntry)})
        number = integer(entry["issue_number"], 1)
        snapshot.issue(number)
        require(number not in seen, "duplicate_summary_issue")
        seen.add(number)
        require(entry["suggested_priority"] in PRIORITY_OPTIONS, "invalid_priority")
        entries.append(SummaryEntry(number, proposal_text(entry["summary"], 1000),
                                    entry["suggested_priority"],
                                    proposal_text(entry["next_action"], 500)))
    return tuple(entries)


@dataclass(frozen=True)
class Lease:
    run_id: str
    fence: int
    expires_at: str


@dataclass(frozen=True)
class Allocation:
    operation_id: str
    reserved_micro_usd: int
    actual_micro_usd: int | None
    response_id: str | None


@dataclass(frozen=True)
class Intent:
    operation_id: str
    issue_number: int
    item_id: str
    field: str
    before: str | tuple[str, ...]
    desired: str | tuple[str, ...]
    revision: str
    outcome: str


@dataclass(frozen=True)
class State:
    version: int
    repository: str
    board_id: str
    cycle_start: str
    cycle_end: str
    generation: int
    lease: Lease | None
    allocations: tuple[Allocation, ...]
    intents: tuple[Intent, ...]
    actions_minutes: int


def state_payload(state: State) -> dict:
    # Dataclasses own this format; adapters serialize no credential-bearing object.
    return asdict(state)
