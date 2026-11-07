"""Constrained GitHub operations and bounded JSON transport for the inactive foundation.

The App port owns repository reads/state/labels; the separate Projects port knows
only one user board and two writable fields. Neither port offers merge, arbitrary
GraphQL, ref updates or command execution. Tests inject a loopback-only opener;
the default production opener additionally enforces the foundation rollout guard.
"""

from __future__ import annotations

import base64
import binascii
import http.client
import json
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any
from urllib.parse import quote

import openai_automation as domain

API_VERSION = "2026-03-10"
ROOT = f"/repos/{domain.REPOSITORY}"
STATE_ROUTE = f"{ROOT}/contents/{domain.STATE_PATH}"
ENABLED_VARIABLE = "OPENAI_AUTOMATION_ENABLED"


@dataclass(frozen=True)
class HttpResult:
    status: int
    body: Any
    headers: dict[str, str]


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file, code, message, headers, new_url):
        return None


class JsonTransport:
    """HTTPS JSON with fixed host, bounded bodies, no redirects and redacted failures.

    `opener` is constructor-only dependency injection for authored loopback tests.
    It has no CLI/environment setting. Production always uses `_open_live`, which
    rejects this foundation release before sending even a read request.
    """

    def __init__(self, host: str, token: str, *, opener: Callable | None = None):
        domain.require(host in ("api.github.com", "api.openai.com"), "disallowed_host")
        domain.identifier(token, r"[A-Za-z0-9_-]{1,512}")
        self.host = host
        self._token = token
        self._open = opener or self._open_live

    @staticmethod
    def _open_live(request):
        domain.require_runtime_capabilities()
        return urllib.request.build_opener(NoRedirect()).open(request, timeout=20)

    def request(self, method: str, path: str, payload: Any = None) -> HttpResult:
        domain.require(method in ("GET", "POST", "PUT"), "disallowed_method")
        domain.require(
            path.startswith("/")
            and not path.startswith("//")
            and not any(char in path for char in "\r\n#"),
            "disallowed_route",
        )
        data = None if payload is None else json.dumps(payload, allow_nan=False).encode("utf-8")
        domain.require(data is None or len(data) <= domain.MAX_DOCUMENT_BYTES, "request_too_large")
        request = urllib.request.Request(
            f"https://{self.host}{path}",
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Accept": "application/vnd.github+json"
                if self.host == "api.github.com"
                else "application/json",
                "Content-Type": "application/json",
                "User-Agent": "MW3-automation-foundation",
                **({"X-GitHub-Api-Version": API_VERSION} if self.host == "api.github.com" else {}),
            },
        )
        try:
            with self._open(request) as response:
                raw = response.read(domain.MAX_DOCUMENT_BYTES + 1)
                headers = {key.lower(): value for key, value in response.headers.items()}
                return HttpResult(response.status, domain.strict_json(raw), headers)
        except urllib.error.HTTPError as error:
            # Do not read/log the body or URL: they can contain prompts or secrets.
            error.close()
            if error.code in (409, 422):
                raise domain.Conflict(f"http_{error.code}") from None
            raise domain.AutomationError(f"http_{error.code}") from None
        except (OSError, TimeoutError, urllib.error.URLError, http.client.HTTPException):
            raise domain.Blocked("unknown_http_outcome") from None


def connection_nodes(value: Any) -> list[dict]:
    domain.require(type(value) is dict and type(value.get("nodes")) is list, "invalid_connection")
    page = value.get("pageInfo", {})
    domain.require(page.get("hasNextPage") is False, "incomplete_nested_pagination")
    domain.require(
        len(value["nodes"]) <= 100 and all(type(node) is dict for node in value["nodes"]),
        "invalid_connection_nodes",
    )
    return value["nodes"]


BOARD_QUERY = """query($board:ID!,$cursor:String){node(id:$board){... on ProjectV2{
id number owner{... on User{login}} items(first:100,after:$cursor){totalCount
pageInfo{hasNextPage endCursor} nodes{id
fieldValues(first:100){pageInfo{hasNextPage} nodes{
... on ProjectV2ItemFieldSingleSelectValue{name field{... on ProjectV2SingleSelectField{id}}}
... on ProjectV2ItemFieldTextValue{text field{... on ProjectV2Field{id}}}}}
content{__typename ... on Issue{number title body closed updatedAt repository{nameWithOwner}
labels(first:100){pageInfo{hasNextPage} nodes{name}}
assignees(first:100){pageInfo{hasNextPage} nodes{login}}}}}}}}}"""

PULL_QUERY = """query($cursor:String){repository(owner:"roswellien",name:"MW3Recomp-Private"){
pullRequests(first:100,after:$cursor,states:OPEN){totalCount pageInfo{hasNextPage endCursor}
nodes{closingIssuesReferences(first:100){pageInfo{hasNextPage}
nodes{number repository{nameWithOwner}}}}}}}"""

FIELD_MUTATION = """mutation($board:ID!,$item:ID!,$field:ID!,$value:ProjectV2FieldValue!){
updateProjectV2ItemFieldValue(input:{projectId:$board,itemId:$item,fieldId:$field,value:$value}){
projectV2Item{id}}}"""


class GitHub:
    def __init__(self, app: JsonTransport, projects: JsonTransport):
        domain.require(app.host == projects.host == "api.github.com", "wrong_port_host")
        self.app = app
        self.projects = projects

    def _graphql(self, transport: JsonTransport, query: str, variables: dict) -> dict:
        response = transport.request("POST", "/graphql", {"query": query, "variables": variables})
        domain.require(
            response.status == 200
            and type(response.body) is dict
            and not response.body.get("errors")
            and type(response.body.get("data")) is dict,
            "graphql_failure",
        )
        return response.body["data"]

    def _pages(self, route: str) -> list[dict]:
        rows = []
        for page in range(1, 11):
            response = self.app.request("GET", f"{ROOT}/{route}&per_page=100&page={page}")
            domain.require(
                type(response.body) is list and len(response.body) <= 100, "invalid_rest_page"
            )
            rows.extend(response.body)
            domain.require(len(rows) <= domain.MAX_ITEMS, "pagination_limit")
            if 'rel="next"' not in response.headers.get("link", ""):
                return rows
        raise domain.Blocked("pagination_limit")

    def _connections(self, query: str, board: bool) -> list[dict]:
        rows = []
        cursor = None
        seen = set()
        total = None
        for _ in range(10):
            variables = {"cursor": cursor} | ({"board": domain.BOARD_ID} if board else {})
            data = self._graphql(self.projects if board else self.app, query, variables)
            if board:
                node = data.get("node") or {}
                domain.require(
                    node.get("id") == domain.BOARD_ID
                    and node.get("number") == domain.BOARD_NUMBER
                    and node.get("owner", {}).get("login") == domain.BOARD_OWNER,
                    "wrong_scope",
                )
                connection = node["items"]
            else:
                connection = data["repository"]["pullRequests"]
            count = domain.integer(connection["totalCount"], 0, domain.MAX_ITEMS)
            domain.require(total is None or total == count, "pagination_changed")
            total = count
            nodes = connection["nodes"]
            domain.require(type(nodes) is list and len(nodes) <= 100, "invalid_connection_nodes")
            rows.extend(nodes)
            page = connection["pageInfo"]
            domain.boolean(page["hasNextPage"])
            if not page["hasNextPage"]:
                domain.require(len(rows) == total, "incomplete_pagination")
                return rows
            cursor = domain.text_value(page["endCursor"], 1000)
            domain.require(cursor not in seen and bool(nodes), "repeated_cursor")
            seen.add(cursor)
        raise domain.Blocked("pagination_limit")

    def read_snapshot(self, now: datetime) -> domain.Snapshot:
        branch = self.app.request("GET", f"{ROOT}/branches/develop").body
        domain.require(branch.get("name") == "develop", "wrong_base_branch")
        issues = []
        for item in self._connections(BOARD_QUERY, True):
            content = item.get("content")
            domain.require(type(content) is dict, "unreadable_board_content")
            kind = content.get("__typename")
            if kind in ("DraftIssue", "PullRequest"):
                continue
            domain.require(kind == "Issue", "unknown_board_content")
            if content["repository"]["nameWithOwner"] != domain.REPOSITORY:
                continue
            values = {}
            for value in connection_nodes(item["fieldValues"]):
                field_id = (value.get("field") or {}).get("id")
                if field_id in (
                    domain.STATUS_FIELD,
                    domain.PRIORITY_FIELD,
                    domain.NEXT_ACTION_FIELD,
                ):
                    domain.require(field_id not in values, "duplicate_board_field")
                    values[field_id] = value.get("text", value.get("name"))
            row = {
                "number": content["number"],
                "item_id": item["id"],
                "title": domain.github_text(content["title"], 512),
                "body": domain.github_text(content["body"], 16_000, empty=True),
                "open": not domain.boolean(content["closed"]),
                "labels": sorted(label["name"] for label in connection_nodes(content["labels"])),
                "assignees": sorted(
                    person["login"] for person in connection_nodes(content["assignees"])
                ),
                "status": values.get(domain.STATUS_FIELD, ""),
                "priority": values.get(domain.PRIORITY_FIELD, ""),
                "next_action": domain.github_text(
                    values.get(domain.NEXT_ACTION_FIELD, ""), 2000, empty=True
                ),
            }
            domain.instant(content["updatedAt"])
            row["revision"] = domain.fingerprint({"issue": row, "updated_at": content["updatedAt"]})
            issues.append(row)
        open_numbers = {
            domain.integer(row["number"], 1)
            for row in self._pages("issues?state=open")
            if "pull_request" not in row
        }
        boarded = {row["number"] for row in issues if row["open"]}
        domain.require(open_numbers == boarded, "board_issue_set_changed_or_missing")
        references = set()
        for pull in self._connections(PULL_QUERY, False):
            for issue in connection_nodes(pull["closingIssuesReferences"]):
                if issue["repository"]["nameWithOwner"] == domain.REPOSITORY:
                    references.add(domain.integer(issue["number"], 1))
        return domain.Snapshot.parse(
            {
                "version": 1,
                "repository": domain.REPOSITORY,
                "board_id": domain.BOARD_ID,
                "base_sha": branch["commit"]["sha"],
                "captured_at": domain.utc_text(now),
                "complete": True,
                "issues": issues,
                "implementation_issues": sorted(references),
            }
        )

    def enabled(self) -> bool:
        value = self.app.request("GET", f"{ROOT}/actions/variables/{ENABLED_VARIABLE}").body
        return value.get("name") == ENABLED_VARIABLE and value.get("value") == "true"

    def read_state(self) -> tuple[domain.State, str]:
        response = self.app.request(
            "GET", f"{STATE_ROUTE}?ref={quote(domain.STATE_BRANCH, safe='')}"
        )
        row = response.body
        domain.require(
            row.get("type") == "file" and row.get("encoding") == "base64", "invalid_state_file"
        )
        domain.integer(row.get("size"), 1, 500_000)
        sha = domain.identifier(row.get("sha"), r"[0-9a-f]{40}")
        try:
            raw = base64.b64decode("".join(row["content"].split()), validate=True)
        except (ValueError, binascii.Error, KeyError, AttributeError):
            raise domain.AutomationError("invalid_state_encoding") from None
        domain.require(len(raw) == row["size"], "state_size_mismatch")
        return domain.parse_state(domain.strict_json(raw)), sha

    def save_state(self, state: domain.State, previous_sha: str, check: Callable[[], None]) -> str:
        domain.identifier(previous_sha, r"[0-9a-f]{40}")
        # Validate even directly constructed records before they reach the ledger.
        payload = json.dumps(domain.state_payload(state), sort_keys=True, allow_nan=False)
        domain.parse_state(domain.strict_json(payload))
        domain.require(len(payload.encode("utf-8")) <= 500_000, "state_compaction_required")
        check()
        response = self.app.request(
            "PUT",
            STATE_ROUTE,
            {
                "branch": domain.STATE_BRANCH,
                "sha": previous_sha,
                "message": "Update automation state",
                "content": base64.b64encode(payload.encode("utf-8")).decode("ascii"),
            },
        )
        return domain.identifier(response.body["content"]["sha"], r"[0-9a-f]{40}")

    def check_publisher(
        self,
        run_id: str,
        fence: int,
        clock: Callable[[], datetime],
        expected_sha: str | None = None,
        *,
        policy: domain.Policy | None = None,
    ) -> tuple[domain.State, str]:
        if not self.enabled():
            raise domain.Blocked("disabled")
        state, sha = self.read_state()
        # The network reads can cross a lease or budget deadline. Admit the effect
        # using the clock after those reads, not the time when the check began.
        now = clock()
        domain.assert_fence(state, run_id, fence, now)
        if policy is not None:
            domain.require(
                not domain.configuration_blockers(policy, now), "configuration_incomplete"
            )
        if expected_sha is not None and sha != expected_sha:
            raise domain.Conflict("state_sha_changed")
        return state, sha

    def publish_one(
        self,
        operation_id: str,
        run_id: str,
        fence: int,
        clock: Callable[[], datetime],
        *,
        policy: domain.Policy,
    ) -> str:
        """Publish one persisted intent, never retry an uncertain external mutation."""

        def check(expected_sha: str | None = None):
            return self.check_publisher(run_id, fence, clock, expected_sha, policy=policy)

        state, sha = check()
        matches = [item for item in state.intents if item.operation_id == operation_id]
        domain.require(len(matches) == 1, "unknown_intent")
        intent = matches[0]
        if intent.outcome in domain.TERMINAL_OUTCOMES:
            return intent.outcome
        issue = self.read_snapshot(clock()).issue(intent.issue_number)
        outcome = domain.intent_outcome(intent, issue)
        if intent.outcome == "publishing":
            # Seeing the old value does not prove a timed-out request never arrived.
            if outcome != "applied":
                raise domain.Blocked("uncertain_publication")
        elif intent.outcome == "prepared" and outcome == "conflict":
            # No external request is possible until publishing is durably saved. Retire
            # only unsent work; siblings may also be stale and are checked separately.
            state = domain.update_intent(state, operation_id, "superseded")
            self.save_state(state, sha, lambda: check(sha))
            return "superseded"
        elif intent.outcome != "prepared":
            raise domain.Blocked("human_or_source_changed")
        elif outcome != "applied":
            publishing = domain.update_intent(state, operation_id, "publishing")
            sha = self.save_state(publishing, sha, lambda: check(sha))
            if self.read_snapshot(clock()).issue(intent.issue_number) != issue:
                raise domain.Blocked("human_or_source_changed")
            check(sha)
            if intent.field == "labels":
                additions = sorted(set(intent.desired) - set(intent.before))
                self.app.request(
                    "POST", f"{ROOT}/issues/{intent.issue_number}/labels", {"labels": additions}
                )
            else:
                field_id = (
                    domain.PRIORITY_FIELD
                    if intent.field == "priority"
                    else domain.NEXT_ACTION_FIELD
                )
                value = (
                    {"singleSelectOptionId": domain.PRIORITY_OPTIONS[intent.desired]}
                    if intent.field == "priority"
                    else {"text": intent.desired}
                )
                self._graphql(
                    self.projects,
                    FIELD_MUTATION,
                    {
                        "board": domain.BOARD_ID,
                        "item": intent.item_id,
                        "field": field_id,
                        "value": value,
                    },
                )
            fresh = self.read_snapshot(clock()).issue(intent.issue_number)
            if domain.intent_outcome(intent, fresh) != "applied":
                raise domain.Blocked("publication_not_confirmed")
            # Only our just-verified field changed: advance sibling revision checks.
            expected = replace(issue, **{intent.field: intent.desired}, revision=fresh.revision)
            isolated_edit = replace(fresh, labels=tuple(sorted(fresh.labels))) == replace(
                expected, labels=tuple(sorted(expected.labels))
            )
            # A confirmed effect remains applied even if a human changed another field.
            # Only an isolated edit can advance sibling revisions; stale siblings pause.
            state = replace(
                publishing,
                intents=tuple(
                    replace(item, revision=fresh.revision)
                    if isolated_edit
                    and item.issue_number == issue.number
                    and item.outcome == "prepared"
                    else item
                    for item in publishing.intents
                ),
            )
        state = domain.update_intent(state, operation_id, "applied")
        self.save_state(state, sha, lambda: check(sha))
        return "applied"
