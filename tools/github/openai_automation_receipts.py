"""Redacted completion evidence, independent of the fenced remote state ledger.

The caller supplies a private, persistent directory; there is no default path or
credential lookup. Receipts are immutable evidence, never instructions or authority.
Hosted durable storage/retention must be verified before the dormant rollout opens.
"""

from __future__ import annotations

import json
import os
import stat
import tempfile
from pathlib import Path

import openai_automation as domain

MAX_RECEIPT_BYTES = 4096
ANOMALIES = ("invalid_response_id", "invalid_response_model", "invalid_usage", "unexpected_model")


def allocation_binding(state: domain.State, policy: domain.Policy, operation_id: str) -> str:
    matches = [item for item in state.allocations if item.operation_id == operation_id]
    domain.require(len(matches) == 1, "unknown_allocation")
    allocation = matches[0]
    return domain.fingerprint(
        {
            "repository": state.repository,
            "board_id": state.board_id,
            "cycle_start": domain.utc_text(domain.instant(state.cycle_start)),
            "cycle_end": domain.utc_text(domain.instant(state.cycle_end)),
            "operation_id": allocation.operation_id,
            "reserved_micro_usd": allocation.reserved_micro_usd,
            "model": policy.model,
            "input_price": policy.input_price_micro_usd_per_million,
            "output_price": policy.output_price_micro_usd_per_million,
        }
    )


def parse_receipt(value: object) -> dict:
    row = domain.exact_object(
        value,
        {
            "version",
            "repository",
            "board_id",
            "operation_id",
            "allocation_binding",
            "response_id",
            "model",
            "usage",
            "anomalies",
        },
    )
    domain.require(type(row["version"]) is int and row["version"] == 1, "invalid_receipt_version")
    domain.require(
        row["repository"] == domain.REPOSITORY and row["board_id"] == domain.BOARD_ID, "wrong_scope"
    )
    domain.identifier(row["operation_id"], r"[A-Za-z0-9_-]{1,64}")
    domain.identifier(row["allocation_binding"], r"[0-9a-f]{64}")
    anomalies = domain.string_list(row["anomalies"], ANOMALIES)
    for name, pattern, code in (
        ("response_id", r"resp_[A-Za-z0-9_-]{1,120}", "invalid_response_id"),
        ("model", r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}", "invalid_response_model"),
    ):
        if row[name] is None:
            domain.require(code in anomalies, "incomplete_receipt")
        else:
            domain.identifier(row[name], pattern)
            domain.require(code not in anomalies, "inconsistent_receipt")
    if row["usage"] is None:
        domain.require("invalid_usage" in anomalies, "incomplete_receipt")
    else:
        domain.usage_tokens(
            domain.exact_object(row["usage"], {"input_tokens", "output_tokens", "total_tokens"})
        )
        domain.require("invalid_usage" not in anomalies, "inconsistent_receipt")
    return row


def completion_receipt(
    state: domain.State, policy: domain.Policy, operation_id: str, response: object
) -> dict:
    # Only validated identifiers/counts cross this boundary. Never persist a body,
    # prompt, output text, provider error, token, or arbitrary unexpected value.
    response = response if type(response) is dict else {}
    row = {
        "version": 1,
        "repository": domain.REPOSITORY,
        "board_id": domain.BOARD_ID,
        "operation_id": operation_id,
        "allocation_binding": allocation_binding(state, policy, operation_id),
        "response_id": None,
        "model": None,
        "usage": None,
        "anomalies": [],
    }
    for name, source, pattern, code in (
        ("response_id", "id", r"resp_[A-Za-z0-9_-]{1,120}", "invalid_response_id"),
        ("model", "model", r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}", "invalid_response_model"),
    ):
        try:
            row[name] = domain.identifier(response.get(source), pattern)
        except domain.AutomationError:
            row["anomalies"].append(code)
    if row["model"] is not None and row["model"] != policy.model:
        row["anomalies"].append("unexpected_model")
    try:
        row["usage"] = domain.usage_tokens(response.get("usage"))
    except domain.AutomationError:
        row["anomalies"].append("invalid_usage")
    return parse_receipt(row)


def settle_receipt(state: domain.State, policy: domain.Policy, receipt: dict) -> domain.State:
    receipt = parse_receipt(receipt)
    operation_id = receipt["operation_id"]
    domain.require(
        receipt["allocation_binding"] == allocation_binding(state, policy, operation_id),
        "receipt_allocation_mismatch",
    )
    domain.require(not receipt["anomalies"], "receipt_requires_owner_reconciliation")
    allocation = next(item for item in state.allocations if item.operation_id == operation_id)
    response = {"id": receipt["response_id"], "model": receipt["model"], "usage": receipt["usage"]}
    if allocation.actual_micro_usd is not None:
        domain.require(
            allocation.response_id == receipt["response_id"]
            and allocation.actual_micro_usd
            == domain.usage_cost(
                policy, receipt["usage"]["input_tokens"], receipt["usage"]["output_tokens"]
            ),
            "receipt_settlement_conflict",
        )
        return state
    return domain.settle_usage(state, policy, operation_id, response)


class CompletionJournal:
    def __init__(self, directory: Path):
        domain.require(directory.is_absolute(), "receipt_directory_not_absolute")
        self.directory = directory
        self._check_directory()

    def _check_directory(self) -> None:
        try:
            info = self.directory.lstat()
        except OSError:
            raise domain.Blocked("completion_receipt_io_failed") from None
        domain.require(
            stat.S_ISDIR(info.st_mode)
            and not stat.S_ISLNK(info.st_mode)
            and not getattr(info, "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0),
            "unsafe_receipt_directory",
        )
        if os.name != "nt":
            domain.require(
                info.st_uid == os.geteuid() and info.st_mode & 0o077 == 0,
                "unsafe_receipt_permissions",
            )

    def _path(self, operation_id: str) -> Path:
        domain.identifier(operation_id, r"[A-Za-z0-9_-]{1,64}")
        return self.directory / f"receipt-{domain.fingerprint(operation_id)}.json"

    def _flush_directory(self) -> None:
        # Windows has no portable directory fsync. Its ACLs and storage crash
        # guarantees require deployment verification; scratch-only Actions is barred.
        if os.name != "nt":
            descriptor = os.open(self.directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)

    def check_available(self, operation_id: str) -> None:
        self._check_directory()
        temporary = None
        linked = None
        try:
            try:
                domain.require(not self._path(operation_id).exists(), "completion_receipt_exists")
                # Exercise the publication primitive before allocating money. A writable
                # filesystem may still lack the hard links that immutable receipts need.
                with tempfile.NamedTemporaryFile(dir=self.directory, delete=False) as probe:
                    temporary = Path(probe.name)
                    probe.write(b"receipt storage check")
                    probe.flush()
                    os.fsync(probe.fileno())
                linked = temporary.with_name(temporary.name + ".link")
                os.link(temporary, linked)
                try:
                    os.link(temporary, linked)
                except FileExistsError:
                    pass
                else:
                    raise domain.Blocked("completion_receipt_storage_not_exclusive")
                self._flush_directory()
            finally:
                if linked is not None:
                    linked.unlink(missing_ok=True)
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
        except OSError:
            raise domain.Blocked("completion_receipt_io_failed") from None

    def read(self, operation_id: str) -> dict:
        self._check_directory()
        path = self._path(operation_id)
        try:
            domain.require(not path.is_symlink(), "unsafe_receipt_file")
            with path.open("rb") as source:
                info = os.fstat(source.fileno())
                if os.name != "nt":
                    domain.require(
                        info.st_uid == os.geteuid() and info.st_mode & 0o077 == 0,
                        "unsafe_receipt_permissions",
                    )
                raw = source.read(MAX_RECEIPT_BYTES + 1)
                domain.require(len(raw) <= MAX_RECEIPT_BYTES, "receipt_too_large")
                row = parse_receipt(domain.strict_json(raw))
        except OSError:
            raise domain.Blocked("completion_receipt_io_failed") from None
        domain.require(row["operation_id"] == operation_id, "wrong_receipt_operation")
        return row

    def record(self, receipt: dict) -> None:
        self._check_directory()
        receipt = parse_receipt(receipt)
        raw = json.dumps(receipt, sort_keys=True, allow_nan=False).encode("utf-8")
        domain.require(len(raw) <= MAX_RECEIPT_BYTES, "receipt_too_large")
        path = self._path(receipt["operation_id"])
        temporary = None
        try:
            try:
                with tempfile.NamedTemporaryFile(dir=self.directory, delete=False) as output:
                    temporary = Path(output.name)
                    output.write(raw)
                    output.flush()
                    os.fsync(output.fileno())
                try:
                    # A same-directory hard link is atomic and never replaces evidence.
                    os.link(temporary, path)
                except FileExistsError:
                    if self.read(receipt["operation_id"]) != receipt:
                        raise domain.Conflict("completion_receipt_conflict") from None
                self._flush_directory()
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
        except OSError:
            raise domain.Blocked("completion_receipt_io_failed") from None
