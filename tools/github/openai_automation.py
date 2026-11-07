"""Inactive automation foundation: strict contracts, state transitions and offline preview.

This module owns authority and money decisions. Adapters may execute only its named
operations; issue text and provider output are data, never control instructions.
Runtime admission is deliberately closed until the worker/maintenance rollout lands.
All persistent money is integer micro-USD, times are UTC, and revisions are explicit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from dataclasses import asdict, dataclass, fields, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_board

AREA_LABELS = check_board.AREA_LABELS
TYPE_LABELS = check_board.TYPE_LABELS
REPOSITORY = check_board.REPOSITORY
BOARD_NUMBER = check_board.BOARD_NUMBER
BOARD_OWNER = check_board.BOARD_OWNER

BOARD_ID = "PVT_kwHODf7y6M4BpC8L"
PRIORITY_FIELD = "PVTSSF_lAHODf7y6M4BpC8LzhngSb0"
PRIORITY_OPTIONS = {"P0": "79628723", "P1": "0a877460", "P2": "da944a9c"}
NEXT_ACTION_FIELD = "PVTF_lAHODf7y6M4BpC8LzhoZL5o"
STATUS_FIELD = "PVTSSF_lAHODf7y6M4BpC8LzhngSSM"
STATE_BRANCH = "roswellien/ci/260-automation-state"
STATE_PATH = "openai-automation/state.json"
MAX_DOCUMENT_BYTES = 2_000_000
MAX_ITEMS = 1000
RUNTIME_CAPABILITIES = frozenset({"foundation"})
REQUIRED_CAPABILITIES = frozenset({"foundation", "worker", "maintenance"})
PREREQUISITES = (
    "credits",
    "project_cap",
    "secret_isolation",
    "platform_no_merge",
    "app_identity",
    "projects_identity",
    "ready_setters",
    "hosted_data",
    "canary",
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

    def finite_float(value: str) -> float:
        parsed = float(value)
        require(math.isfinite(parsed), "non_finite_json_number")
        return parsed

    try:
        require(len(text) <= MAX_DOCUMENT_BYTES, "document_too_large")
        return json.loads(
            text,
            object_pairs_hook=unique_object,
            parse_constant=reject_constant,
            parse_float=finite_float,
        )
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
    require(
        (empty or bool(value.strip())) and len(value.encode("utf-8")) <= maximum,
        "invalid_text_length",
    )
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
        require(row["effort"] in (None, "none", "low", "medium", "high", "xhigh"), "invalid_effort")
        for name in (
            "input_price_micro_usd_per_million",
            "output_price_micro_usd_per_million",
            "api_budget_micro_usd",
            "request_budget_micro_usd",
            "actions_budget_minutes",
        ):
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
    for name in (
        "controller_sha",
        "model",
        "effort",
        "input_price_micro_usd_per_million",
        "output_price_micro_usd_per_million",
        "api_budget_micro_usd",
        "request_budget_micro_usd",
        "actions_budget_minutes",
        "cycle_start",
        "cycle_end",
    ):
        if getattr(policy, name) is None:
            blockers.append(f"missing_{name}")
    if policy.cycle_start is not None and not (
        instant(policy.cycle_start) <= now < instant(policy.cycle_end)
    ):
        blockers.append("credit_cycle_inactive")
    blockers.extend(
        f"unverified_{name}" for name in PREREQUISITES if not policy.prerequisites[name]
    )
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
        require(
            row["status"] in ("", "Backlog", "Ready", "In progress", "In review", "Done"),
            "invalid_status",
        )
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
        row = exact_object(
            value,
            {
                "version",
                "repository",
                "board_id",
                "base_sha",
                "captured_at",
                "complete",
                "issues",
                "implementation_issues",
            },
        )
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
        return cls(
            row["repository"],
            row["board_id"],
            row["base_sha"],
            row["captured_at"],
            issues,
            references,
        )

    def issue(self, number: int) -> Issue:
        for issue in self.issues:
            if issue.number == number:
                return issue
        raise AutomationError("unknown_issue")

    def eligible_ready(self) -> tuple[int, ...]:
        return tuple(
            issue.number
            for issue in self.issues
            if issue.open
            and issue.status == "Ready"
            and not issue.assignees
            and issue.number not in self.implementation_issues
        )


def proposal_text(value: Any, maximum: int) -> str:
    value = text_value(value, maximum)
    # Only plain review text is published. Links are constructed from validated IDs.
    require(
        not re.search(r"https?://|www\.|[<>`]|\$\{|\$\(|\x1b", value, re.IGNORECASE),
        "unsafe_proposal_text",
    )
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
        existing_types = set(issue.labels) & set(TYPE_LABELS)
        proposed_types = set(labels) & set(TYPE_LABELS)
        require(not existing_types or existing_types == proposed_types, "human_type_label_conflict")
        require(
            sum(label in TYPE_LABELS for label in labels) == 1
            and any(label in AREA_LABELS for label in labels),
            "missing_triage_labels",
        )
        require(row["priority"] in PRIORITY_OPTIONS, "invalid_priority")
        return cls(
            expected_issue,
            issue.revision,
            labels,
            row["priority"],
            proposal_text(row["next_action"], 500),
        )

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
    require(
        type(row["entries"]) is list and len(row["entries"]) <= MAX_ITEMS, "invalid_summary_entries"
    )
    entries = []
    seen = set()
    for entry in row["entries"]:
        exact_object(entry, {field.name for field in fields(SummaryEntry)})
        number = integer(entry["issue_number"], 1)
        snapshot.issue(number)
        require(number not in seen, "duplicate_summary_issue")
        seen.add(number)
        require(entry["suggested_priority"] in PRIORITY_OPTIONS, "invalid_priority")
        entries.append(
            SummaryEntry(
                number,
                proposal_text(entry["summary"], 1000),
                entry["suggested_priority"],
                proposal_text(entry["next_action"], 500),
            )
        )
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


def parse_state(value: Any) -> State:
    row = dict(exact_object(value, {field.name for field in fields(State)}))
    require(integer(row["version"]) == 1, "unsupported_state_version")
    require(row["repository"] == REPOSITORY and row["board_id"] == BOARD_ID, "wrong_scope")
    require(instant(row["cycle_start"]) < instant(row["cycle_end"]), "invalid_cycle")
    integer(row["generation"])
    integer(row["actions_minutes"])
    if row["lease"] is not None:
        lease = exact_object(row["lease"], {field.name for field in fields(Lease)})
        identifier(lease["run_id"], r"[A-Za-z0-9_-]{1,64}")
        require(integer(lease["fence"], 1) == row["generation"], "invalid_fence")
        instant(lease["expires_at"])
        row["lease"] = Lease(**lease)
    require(
        type(row["allocations"]) is list and len(row["allocations"]) <= MAX_ITEMS,
        "invalid_allocations",
    )
    allocations = []
    for allocation in row["allocations"]:
        exact_object(allocation, {field.name for field in fields(Allocation)})
        identifier(allocation["operation_id"], r"[A-Za-z0-9_-]{1,64}")
        integer(allocation["reserved_micro_usd"], 1)
        if allocation["actual_micro_usd"] is not None:
            integer(allocation["actual_micro_usd"])
            identifier(allocation["response_id"], r"resp_[A-Za-z0-9_-]{1,120}")
        else:
            require(allocation["response_id"] is None, "incomplete_usage")
        allocations.append(Allocation(**allocation))
    require(
        len({item.operation_id for item in allocations}) == len(allocations), "duplicate_allocation"
    )
    row["allocations"] = tuple(allocations)
    require(type(row["intents"]) is list and len(row["intents"]) <= MAX_ITEMS, "invalid_intents")
    row["intents"] = tuple(parse_intent(intent) for intent in row["intents"])
    require(
        len({item.operation_id for item in row["intents"]}) == len(row["intents"]),
        "duplicate_intent",
    )
    return State(**row)


def parse_intent(value: Any) -> Intent:
    row = dict(exact_object(value, {field.name for field in fields(Intent)}))
    identifier(row["operation_id"], r"[A-Za-z0-9_-]{1,64}")
    integer(row["issue_number"], 1, 2**31 - 1)
    identifier(row["item_id"], r"PVTI_[A-Za-z0-9_-]{1,100}")
    identifier(row["revision"], r"[0-9a-f]{64}")
    require(row["outcome"] in ("prepared", "publishing", "applied", "conflict"), "invalid_outcome")
    require(row["field"] in ("labels", "priority", "next_action"), "disallowed_field")
    if row["field"] == "labels":
        row["before"] = string_list(
            list(row["before"]) if type(row["before"]) is tuple else row["before"]
        )
        row["desired"] = string_list(
            list(row["desired"]) if type(row["desired"]) is tuple else row["desired"]
        )
        require(set(row["before"]) <= set(row["desired"]), "human_label_removal")
        require(
            set(row["desired"]) - set(row["before"]) <= set(TYPE_LABELS + AREA_LABELS),
            "disallowed_label",
        )
    elif row["field"] == "priority":
        require(
            row["before"] in ("", *PRIORITY_OPTIONS) and row["desired"] in PRIORITY_OPTIONS,
            "invalid_priority",
        )
    else:
        text_value(row["before"], 2000, empty=True)
        proposal_text(row["desired"], 500)
    return Intent(**row)


def acquire_lease(state: State, run_id: str, now: datetime, expires_at: datetime) -> State:
    """Propose a publisher lease. The caller must persist it with the previous blob SHA."""
    identifier(run_id, r"[A-Za-z0-9_-]{1,64}")
    require(
        now < expires_at and (expires_at - now).total_seconds() <= 300, "invalid_lease_deadline"
    )
    if state.lease is not None and instant(state.lease.expires_at) > now:
        raise Blocked("publisher_busy")
    if any(intent.outcome in ("publishing", "conflict") for intent in state.intents):
        raise Blocked("unreconciled_publication")
    if any(allocation.actual_micro_usd is None for allocation in state.allocations):
        raise Blocked("unreconciled_usage")
    generation = state.generation + 1
    return replace(
        state, generation=generation, lease=Lease(run_id, generation, utc_text(expires_at))
    )


def assert_fence(state: State, run_id: str, fence: int, now: datetime) -> None:
    if state.lease is None or state.lease.run_id != run_id or state.lease.fence != fence:
        raise Blocked("stale_publisher")
    if not now < instant(state.lease.expires_at):
        raise Blocked("expired_publisher")


def prepare_triage(
    state: State, snapshot: Snapshot, proposal: TriageProposal, operation_id: str
) -> State:
    """Create durable per-field intents; this function performs no publication."""
    identifier(operation_id, r"[A-Za-z0-9_-]{1,55}")
    issue = snapshot.issue(proposal.issue_number)
    require(issue.revision == proposal.revision and issue.open, "stale_proposal")
    if any(
        item.issue_number == issue.number and item.outcome != "applied" for item in state.intents
    ):
        raise Blocked("issue_has_pending_intent")
    intents = list(state.intents)
    for name, desired in (
        ("labels", proposal.merged_labels(issue)),
        ("priority", proposal.priority),
        ("next_action", proposal.next_action),
    ):
        before = getattr(issue, name)
        if before == desired or (name == "labels" and set(before) == set(desired)):
            continue
        intent = Intent(
            f"{operation_id}_{name}",
            issue.number,
            issue.item_id,
            name,
            before,
            desired,
            issue.revision,
            "prepared",
        )
        intents.append(parse_intent(asdict(intent)))
    require(len({item.operation_id for item in intents}) == len(intents), "duplicate_intent")
    return replace(state, intents=tuple(intents))


def intent_outcome(intent: Intent, issue: Issue) -> str:
    require(intent.issue_number == issue.number and intent.item_id == issue.item_id, "wrong_issue")
    current = getattr(issue, intent.field)
    if intent.field == "labels":
        current = tuple(sorted(current))
    desired = tuple(sorted(intent.desired)) if intent.field == "labels" else intent.desired
    before = tuple(sorted(intent.before)) if intent.field == "labels" else intent.before
    if current == desired:
        return "applied"
    if current == before and issue.revision == intent.revision and issue.open:
        return "prepared"
    return "conflict"


def update_intent(state: State, operation_id: str, outcome: str) -> State:
    require(any(item.operation_id == operation_id for item in state.intents), "unknown_intent")
    updated = tuple(
        replace(item, outcome=outcome) if item.operation_id == operation_id else item
        for item in state.intents
    )
    for item in updated:
        parse_intent(asdict(item))
    return replace(state, intents=updated)


def usage_cost(policy: Policy, input_tokens: int, output_tokens: int) -> int:
    integer(input_tokens, 0, 10**9)
    integer(output_tokens, 0, 10**9)
    require(
        policy.input_price_micro_usd_per_million is not None
        and policy.output_price_micro_usd_per_million is not None,
        "missing_prices",
    )
    # Full input price is conservative: do not infer a cache discount from authentication.
    numerator = input_tokens * policy.input_price_micro_usd_per_million
    numerator += output_tokens * policy.output_price_micro_usd_per_million
    return (numerator + 999_999) // 1_000_000


def allocate_request(
    state: State, policy: Policy, operation_id: str, input_bytes: int, now: datetime
) -> State:
    """Propose a durable soft allocation before inference, never a vendor reservation."""
    if configuration_blockers(policy, now):
        raise Blocked("configuration_incomplete")
    require(
        state.cycle_start == policy.cycle_start and state.cycle_end == policy.cycle_end,
        "ledger_cycle_mismatch",
    )
    identifier(operation_id, r"[A-Za-z0-9_-]{1,64}")
    integer(input_bytes, 1, policy.max_input_bytes)
    require(
        not any(item.operation_id == operation_id for item in state.allocations),
        "duplicate_allocation",
    )
    if any(item.actual_micro_usd is None for item in state.allocations):
        raise Blocked("unreconciled_usage")
    if any(item.actual_micro_usd > item.reserved_micro_usd for item in state.allocations):
        raise Blocked("allocation_exceeded")
    if any(item.outcome != "applied" for item in state.intents):
        raise Blocked("unreconciled_publication")
    # UTF-8 bytes plus framing headroom bound tokenized text; no images/tools are sent.
    estimate = usage_cost(policy, input_bytes, policy.max_output_tokens)
    reserved = max(1, (estimate * (100 + policy.headroom_percent) + 99) // 100)
    spent = sum(item.actual_micro_usd for item in state.allocations)
    if reserved > policy.request_budget_micro_usd or spent + reserved > policy.api_budget_micro_usd:
        raise Blocked("api_budget_exhausted")
    # Charge the full five-minute Linux job allowance conservatively for each call.
    if state.actions_minutes + 5 > policy.actions_budget_minutes:
        raise Blocked("actions_budget_exhausted")
    require(len(state.allocations) < MAX_ITEMS, "allocation_limit")
    return replace(
        state,
        allocations=state.allocations + (Allocation(operation_id, reserved, None, None),),
        actions_minutes=state.actions_minutes + 5,
    )


def settle_usage(state: State, policy: Policy, operation_id: str, response: dict) -> State:
    matches = [item for item in state.allocations if item.operation_id == operation_id]
    require(len(matches) == 1 and matches[0].actual_micro_usd is None, "allocation_not_pending")
    response_id = identifier(response.get("id"), r"resp_[A-Za-z0-9_-]{1,120}")
    require(
        not any(item.response_id == response_id for item in state.allocations), "duplicate_response"
    )
    require(response.get("model") == policy.model, "unexpected_response_model")
    usage = response.get("usage")
    require(type(usage) is dict, "missing_usage")
    input_tokens = integer(usage.get("input_tokens"), 0, 10**9)
    output_tokens = integer(usage.get("output_tokens"), 0, 10**9)
    require(
        integer(usage.get("total_tokens"), 0, 2 * 10**9) == input_tokens + output_tokens,
        "invalid_usage_total",
    )
    cost = usage_cost(policy, input_tokens, output_tokens)
    allocations = tuple(
        replace(item, actual_micro_usd=cost, response_id=response_id)
        if item.operation_id == operation_id
        else item
        for item in state.allocations
    )
    return replace(state, allocations=allocations)


@dataclass(frozen=True)
class Decision:
    kind: str
    blockers: tuple[str, ...]
    ready_candidates: tuple[int, ...]
    pending_intents: tuple[str, ...]


def reconciliation_decision(
    policy: Policy, snapshot: Snapshot, state: State | None, now: datetime
) -> Decision:
    blockers = list(configuration_blockers(policy, now))
    if not REQUIRED_CAPABILITIES <= RUNTIME_CAPABILITIES:
        blockers.insert(0, "foundation_rollout_incomplete")
    pending = (
        ()
        if state is None
        else tuple(item.operation_id for item in state.intents if item.outcome != "applied")
    )
    if state is None:
        blockers.append("state_not_loaded")
    else:
        if state.cycle_start != policy.cycle_start or state.cycle_end != policy.cycle_end:
            blockers.append("ledger_cycle_mismatch")
        if any(item.actual_micro_usd is None for item in state.allocations):
            blockers.append("unreconciled_usage")
    kind = "queue_report"
    if pending:
        kind = "reconcile_intent"
    if blockers:
        kind = "pause"
    return Decision(
        kind,
        tuple(blockers),
        snapshot.eligible_ready(),
        pending,
    )


def render_summary(entries: tuple[SummaryEntry, ...]) -> list[dict]:
    return [
        {
            "issue": f"https://github.com/{REPOSITORY}/issues/{entry.issue_number}",
            "summary": entry.summary,
            "suggested_priority": entry.suggested_priority,
            "next_action": entry.next_action,
        }
        for entry in entries
    ]


def read_json_file(path: Path) -> Any:
    with path.open("rb") as source:
        return strict_json(source.read(MAX_DOCUMENT_BYTES + 1))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("mode", choices=("preview", "reconcile", "summary", "triage"))
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument(
        "--state", type=Path, help="optional authored local state for offline preview"
    )
    parser.add_argument(
        "--policy", type=Path, default=Path(__file__).with_name("openai_automation_policy.json")
    )
    parser.add_argument("--issue", type=int, default=0)
    parser.add_argument("--admission-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.mode != "preview":
            # Check code capability before opening configuration, importing clients,
            # reading credentials or inspecting ambient workflow inputs.
            require_runtime_capabilities()
            raise Blocked("runtime_dispatch_not_implemented")
        require(
            args.snapshot is not None and args.issue == 0 and not args.admission_only,
            "invalid_preview_arguments",
        )
        policy = Policy.parse(read_json_file(args.policy))
        snapshot = Snapshot.parse(read_json_file(args.snapshot))
        state = parse_state(read_json_file(args.state)) if args.state is not None else None
        decision = reconciliation_decision(policy, snapshot, state, datetime.now(UTC))
        print(
            json.dumps(
                {
                    "mode": "offline_preview",
                    "decision": asdict(decision),
                    "issue_count": len(snapshot.issues),
                    "remote_writes": 0,
                    "provider_calls": 0,
                },
                sort_keys=True,
            )
        )
        return 0
    except Blocked as error:
        print(f"blocked: {error}", file=sys.stderr)
        return 2
    except AutomationError as error:
        print(f"invalid: {error}", file=sys.stderr)
        return 2
    except (OSError, ValueError, TypeError, KeyError, UnicodeError):
        print("operation_failed", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
