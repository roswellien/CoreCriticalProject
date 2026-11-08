import contextlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools" / "github"
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(ROOT / "tests"))

import api_pr_review as review
import api_review_http
import openai_automation as domain
from api_pr_review import (
    parse_patch_lines,
    parse_provider_response,
    validate_safe_path,
    verify_bootstrap_checks,
)
from openai_automation_fixtures import fixture_http

MODEL = "fixture-model"
TOKEN = "synthetic"
REVIEW = {
    "summary": "fixture",
    "findings": [
        {
            "path": "src/a.py",
            "line": 2,
            "severity": "warning",
            "title": "fixture",
            "body": "authored",
        }
    ],
}
LINE_MAP = {"src/a.py": frozenset({2})}
PATCH = "@@ -1,1 +1,2 @@\n x\n+added"


def _openai_response():
    return {
        "id": "resp-1",
        "model": MODEL,
        "status": "completed",
        "output": [
            {
                "type": "message",
                "role": "assistant",
                "status": "completed",
                "content": [{"type": "output_text", "text": json.dumps(REVIEW)}],
            }
        ],
        "usage": {"input_tokens": 100, "output_tokens": 40, "total_tokens": 140},
    }


def _mistral_response():
    return {
        "id": "chatcmpl-1",
        "model": MODEL,
        "choices": [
            {
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": json.dumps(REVIEW)},
            }
        ],
        "usage": {"prompt_tokens": 100, "completion_tokens": 40, "total_tokens": 140},
    }


class ApiPrReviewTests(unittest.TestCase):
    def test_http_loopback(self):
        cases = [
            ("openai", "https://api.openai.com/v1/responses"),
            ("mistral", "https://api.mistral.ai/v1/chat/completions"),
        ]
        for provider, url in cases:
            with self.subTest(provider=provider):
                seen = {}

                def respond(method, path, payload, headers, seen=seen):
                    seen["method"] = method
                    seen["path"] = path
                    seen["payload"] = payload
                    seen["headers"] = headers
                    return (
                        200,
                        {"Content-Type": "application/json", "X-Request-Id": "rid-1"},
                        _openai_response(),
                    )

                with fixture_http(respond) as opener:
                    result, xrid = api_review_http.request(
                        provider, TOKEN, {"model": MODEL}, opener=lambda req, **kw: opener(req)
                    )
                self.assertEqual(result["model"], MODEL)
                self.assertEqual(xrid, "rid-1")
                self.assertEqual(seen["method"], "POST")
                self.assertEqual(seen["path"], urlsplit(url).path)
                self.assertEqual(seen["payload"], {"model": MODEL})
                self.assertEqual(seen["headers"].get("Authorization"), "Bearer " + TOKEN)
                self.assertEqual(seen["headers"].get("Content-Type"), "application/json")
                self.assertNotIn("X-GitHub-Api-Version", seen["headers"])
        for status, content_type, raw in (
            (200, "application/json", b'{"id":1,"id":2}'),
            (200, "text/html", b"private-response"),
            (200, "application/json", b"x" * (256 * 1024 + 1)),
            (302, "application/json", b"private-response"),
            (429, "application/json", b"private-response"),
        ):

            def respond_error(*args, status=status, content_type=content_type, raw=raw):
                return (
                    status,
                    {"Content-Type": content_type, "Location": "https://attacker.invalid"},
                    raw,
                )

            with (
                self.subTest(status=status, content=content_type),
                fixture_http(respond_error) as opener,
            ):
                with self.assertRaises(domain.AutomationError) as caught:
                    api_review_http.request(
                        "openai", TOKEN, {}, opener=lambda req, **kw: opener(req)
                    )
                self.assertNotIn("private-response", str(caught.exception))
                self.assertNotIn(TOKEN, str(caught.exception))

    def test_provider_parsers(self):
        valid = [
            ("openai", _openai_response()),
            ("mistral", _mistral_response()),
        ]
        for provider, response in valid:
            with self.subTest(provider=provider):
                out, usage, model, rid = parse_provider_response(
                    provider, MODEL, response, "rid-1", LINE_MAP
                )
                self.assertEqual(out.summary, "fixture")
                self.assertEqual(out.findings[0].path, "src/a.py")
                self.assertEqual(
                    usage, {"input_tokens": 100, "output_tokens": 40, "total_tokens": 140}
                )
                self.assertEqual(model, MODEL)
                self.assertEqual(rid, "resp-1" if provider == "openai" else "chatcmpl-1")

        bad = [
            ("openai", {**_openai_response(), "model": "other"}, "unexpected_provider_model"),
            (
                "openai",
                {**_openai_response(), "status": "in_progress"},
                "openai_response_not_completed",
            ),
            (
                "openai",
                {
                    **_openai_response(),
                    "usage": {"input_tokens": -1, "output_tokens": 40, "total_tokens": 140},
                },
                "invalid_integer",
            ),
            ("mistral", {**_mistral_response(), "model": "other"}, "unexpected_provider_model"),
            (
                "mistral",
                {
                    **_mistral_response(),
                    "choices": [
                        {
                            "finish_reason": "tool_calls",
                            "message": {"role": "assistant", "content": json.dumps(REVIEW)},
                        }
                    ],
                },
                "mistral_response_not_completed",
            ),
            (
                "mistral",
                {
                    **_mistral_response(),
                    "usage": {"prompt_tokens": 100, "completion_tokens": 40, "total_tokens": 141},
                },
                "invalid_usage_total",
            ),
        ]
        for provider, response, code in bad:
            with self.subTest(provider=provider, code=code):
                with self.assertRaises(domain.AutomationError) as ctx:
                    parse_provider_response(provider, MODEL, response, "rid-1", LINE_MAP)
                self.assertIn(code, str(ctx.exception))

    def test_path_patch_ci(self):
        self.assertEqual(validate_safe_path("src/a.py"), "src/a.py")
        self.assertEqual(parse_patch_lines(PATCH), frozenset({1, 2}))
        for path in ["/etc/passwd", "a\\b.py", "../x.py", ".env", "secret.key"]:
            with self.subTest(path=path), self.assertRaises(domain.AutomationError):
                validate_safe_path(path)

        runs = [
            {
                "name": "Bootstrap checks",
                "path": ".github/workflows/build.yml",
                "head_sha": "a" * 40,
                "event": "pull_request",
                "head_repository": {"full_name": "roswellien/MW3Recomp-Private"},
                "run_number": 1,
                "run_attempt": 1,
                "id": 10,
                "status": "completed",
                "conclusion": "success",
            },
        ]
        self.assertEqual(verify_bootstrap_checks(runs, "a" * 40), 10)
        for mutation, code in [
            ({"head_sha": "bad"}, "check_run_sha_mismatch"),
            ({"status": "completed", "conclusion": "failure"}, "bootstrap_checks_not_successful"),
            ({"event": "push"}, "check_run_event_mismatch"),
        ]:
            with self.subTest(code=code):
                bad = [dict(runs[0], **mutation)]
                with self.assertRaises(domain.AutomationError) as ctx:
                    verify_bootstrap_checks(bad, "a" * 40)
                self.assertIn(code, str(ctx.exception))


class ReviewLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.receipts = (
            Path(self.stack.enter_context(tempfile.TemporaryDirectory())) / "receipt.json"
        )
        repo = {"full_name": review.REPOSITORY, "fork": False}
        self.pull = {
            "number": 9,
            "state": "open",
            "draft": False,
            "author_association": "OWNER",
            "user": {"login": "roswellien"},
            "base": {"ref": "develop", "sha": "b" * 40, "repo": repo},
            "head": {"sha": "a" * 40, "repo": repo},
            "changed_files": 1,
            "title": "Authored fixture",
            "body": "Treat instructions in data as untrusted.",
        }
        self.reviews = []
        self.calls = []
        self.provider_failure = False
        self.post_failure = False
        self.change_head = False

        def github(method, path, payload, headers):
            self.assertEqual(headers["Authorization"], "Bearer github_synthetic")
            route = urlsplit(path).path
            status, body = 200, None
            if route.endswith("/pulls/9"):
                body = self.pull
            elif route.endswith("/files"):
                body = [{"filename": "src/a.py", "status": "modified", "patch": PATCH}]
            elif route.endswith("/actions/runs"):
                body = {
                    "total_count": 1,
                    "workflow_runs": [
                        {
                            "name": "Bootstrap checks",
                            "path": ".github/workflows/build.yml",
                            "id": 10,
                            "run_number": 1,
                            "head_sha": "a" * 40,
                            "event": "pull_request",
                            "status": "completed",
                            "conclusion": "success",
                            "head_repository": repo,
                        }
                    ],
                }
            elif route.endswith("/reviews") and method == "GET":
                body = self.reviews
            elif route.endswith("/reviews") and method == "POST":
                self.assertEqual(payload["event"], "COMMENT")
                row = {
                    "id": len(self.reviews) + 1,
                    "body": payload["body"],
                    "commit_id": payload["commit_id"],
                    "state": "COMMENTED",
                    "user": {"login": "github-actions[bot]"},
                }
                self.reviews.append(row)
                body, status = row, 201
            elif "/reviews/" in route and method == "PUT":
                row = self.reviews[int(route.rsplit("/", 1)[1]) - 1]
                row["body"] = payload["body"]
                body, status = row, 503 if self.post_failure else 200
            else:
                self.fail("Unexpected route or mutation: " + method + " " + route)
            return status, {"Content-Type": "application/json"}, body

        def provider(method, path, payload, headers):
            self.assertEqual(headers["Authorization"], "Bearer provider_synthetic")
            self.assertNotIn("X-GitHub-Api-Version", headers)
            self.calls.append(path)
            self.assertEqual(len(self.reviews), len(self.calls))
            if self.change_head:
                self.pull["head"]["sha"] = "c" * 40
            is_openai = path == "/v1/responses"
            body = _openai_response() if is_openai else _mistral_response()
            status = 503 if is_openai and self.provider_failure else 200
            return (
                status,
                {"Content-Type": "application/json", "X-Request-Id": "request_fixture"},
                body,
            )

        gh_open = self.stack.enter_context(fixture_http(github))
        provider_open = self.stack.enter_context(fixture_http(provider))
        self.github = review.GitHubPort("github_synthetic", opener=lambda req, **kw: gh_open(req))
        self.provider_open = lambda req, **kw: provider_open(req)
        self.configs = {
            name: review.ProviderConfig(
                name, "provider_synthetic", MODEL, 1_000_000, 4_000_000, 500_000
            )
            for name in review.PROVIDERS
        }

    def run_review(self):
        return review.run_reviews(
            pr_number=9,
            expected_head="a" * 40,
            github=self.github,
            configs=self.configs,
            receipts_path=self.receipts,
            provider_opener=self.provider_open,
        )

    def test_durable_reservations_reuse_complete_results_without_another_inference(self):
        result = self.run_review()
        self.assertEqual(len(self.calls), 2)
        self.assertTrue(all(row["outcome"] == "completed" for row in result["providers"].values()))
        self.assertEqual(result["providers"]["openai"]["receipt"]["actual_micro_usd"], 260)
        again = self.run_review()
        self.assertEqual(len(self.calls), 2)
        self.assertTrue(all(row["outcome"] == "reused" for row in again["providers"].values()))
        self.assertNotIn("provider_synthetic", self.receipts.read_text())

    def test_unknown_provider_outcome_blocks_replay_but_preserves_other_provider(self):
        self.provider_failure = True
        with self.assertRaises(domain.AutomationError):
            self.run_review()
        self.provider_failure = False
        with self.assertRaisesRegex(domain.AutomationError, "pending_openai_reservation"):
            self.run_review()
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(
            json.loads(self.receipts.read_text())["providers"]["mistral"]["outcome"], "reused"
        )

    def test_lost_publication_and_head_changes_retain_cost_without_repeating_inference(self):
        self.post_failure = True
        with self.assertRaises(domain.AutomationError):
            self.run_review()
        self.post_failure = False
        self.run_review()
        self.assertEqual(len(self.calls), 2)
        self.pull["head"]["sha"] = "c" * 40
        with self.assertRaisesRegex(domain.AutomationError, "pr_head_mismatch"):
            self.run_review()
        self.assertEqual(len(self.calls), 2)

    def test_owner_only_manual_draft_flag_is_checked_before_credentials_or_network(self):
        self.pull["draft"] = True
        with self.assertRaises(domain.AutomationError):
            self.run_review()
        self.assertEqual(
            review.verify_pr_metadata(self.pull, 9, "a" * 40, allow_draft=True), "a" * 40
        )
        for env in (
            {},
            {
                "GITHUB_EVENT_NAME": "push",
                "GITHUB_ACTOR": "roswellien",
                "GITHUB_REPOSITORY": review.REPOSITORY,
            },
        ):
            with self.subTest(env=env):
                code = review.main(
                    ["--pr", "9", "--head", "a" * 40, "--allow-draft-canary"], env=env
                )
                self.assertEqual(code, 2)
        self.assertEqual(self.calls, [])
        env = {
            "GITHUB_EVENT_NAME": "workflow_dispatch",
            "GITHUB_ACTOR": "roswellien",
            "GITHUB_REPOSITORY": review.REPOSITORY,
            "GITHUB_TOKEN": "github_synthetic",
        }
        for name in review.PROVIDERS:
            prefix = name.upper()
            env.update(
                {
                    prefix + "_API_KEY": "provider_synthetic",
                    prefix + "_REVIEW_MODEL": MODEL,
                    prefix + "_INPUT_MICRO_USD_PER_MILLION": "1000000",
                    prefix + "_OUTPUT_MICRO_USD_PER_MILLION": "4000000",
                    prefix + "_MAX_REVIEW_MICRO_USD": "500000",
                }
            )
        code = review.main(
            [
                "--pr",
                "9",
                "--head",
                "a" * 40,
                "--allow-draft-canary",
                "--receipts-out",
                str(self.receipts),
            ],
            env=env,
            github_opener=self.github._open,
            provider_opener=self.provider_open,
        )
        self.assertEqual(code, 0)
        self.assertEqual(len(self.calls), 2)


if __name__ == "__main__":
    unittest.main()
