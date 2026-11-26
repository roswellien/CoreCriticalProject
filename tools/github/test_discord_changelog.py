import datetime as dt
import io
import json
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch

import discord_changelog as dc

DAY = "2026-11-26"
WEBHOOK = "https://discord.com/api/webhooks/123456789012345678/" + "a" * 60
TARGET = {"type": 1, "guild_id": dc.GUILD, "channel_id": dc.CHANNEL}
NAME = f"discord-changelog-reservation-{DAY}"
RECEIPT = {"id": "912345678901234567", "channel_id": dc.CHANNEL}


def inputs(*bullets, version="1.0.58 Preview", day=DAY):
    return {"date": day, "version": version, "bullets": json.dumps(bullets)}


def listing(*ids):
    return {
        "total_count": len(ids),
        "artifacts": [{"name": NAME, "id": value, "expired": False} for value in ids],
    }


class ChangelogTests(unittest.TestCase):
    def test_format_and_mentions(self):
        _, result = dc.format_payload(inputs("Fixed <@123> and @everyone"), DAY)
        self.assertEqual(result["allowed_mentions"], {"parse": []})
        self.assertTrue(result["flags"] & 4096)
        for expected in ("What Changed Today", dc.WEBSITE, dc.YOUTUBE, "1.0.58 Preview"):
            self.assertIn(expected, result["content"])

    def test_oversized_not_truncated(self):
        _, result = dc.format_payload(inputs("a" * 2050, "last item"), DAY)
        self.assertIn("last item", result["embeds"][0]["description"])
        with self.assertRaises(dc.ChangelogError):
            dc.format_payload(inputs("😃" * 2080), DAY)

    def test_bad_payloads(self):
        for value in (
            inputs(),
            inputs(" "),
            inputs("bad\nnew line"),
            inputs("bad\ud800"),
            inputs("x", version="no"),
            inputs("x", day="2026-11-25"),
            {"date": DAY, "version": "1.0.0", "bullets": "{}"},
        ):
            with self.subTest(value=value), self.assertRaises(dc.ChangelogError):
                dc.format_payload(value, DAY)

    def test_wrong_or_missing_webhook(self):
        for url in ("", WEBHOOK.replace("discord.com", "example.com"), WEBHOOK + "?wait=true"):
            request = Mock()
            with self.assertRaises(dc.ChangelogError):
                dc.check_webhook(url, request)
            request.assert_not_called()
        for data in ({**TARGET, "channel_id": "wrong"}, {**TARGET, "guild_id": "wrong"}, {}):
            with self.assertRaisesRegex(dc.ChangelogError, "destination mismatch"):
                dc.check_webhook(WEBHOOK, Mock(return_value=data))

    def test_preflight_fails_closed(self):
        for data in (listing(25), {"total_count": 1, "artifacts": []}, {}):
            request = Mock(return_value=data)
            with self.assertRaises(dc.ChangelogError):
                dc.reserve_preflight(NAME, "token", WEBHOOK, request)
            self.assertEqual(request.call_count, 1)
        request = Mock(side_effect=[listing(), TARGET])
        dc.reserve_preflight(NAME, "token", WEBHOOK, request)
        self.assertEqual(request.call_count, 2)

    def test_success_returns_message_link(self):
        request = Mock(side_effect=[listing(42), TARGET, RECEIPT])
        link = dc.send_once(NAME, DAY, "42", "token", WEBHOOK, {}, request, lambda: DAY)
        self.assertTrue(link.endswith("/" + RECEIPT["id"]))
        self.assertEqual(request.call_args.args, (WEBHOOK + "?wait=true",))
        self.assertEqual(request.call_count, 3)

    def test_failures_never_retry(self):
        for response in (
            {"id": "wrong"},
            {**RECEIPT, "channel_id": "wrong"},
            dc.ChangelogError("HTTP 429"),
            dc.ChangelogError("timeout"),
        ):
            request = Mock(side_effect=[listing(42), TARGET, response])
            with self.assertRaisesRegex(dc.ChangelogError, "do not rerun"):
                dc.send_once(NAME, DAY, "42", "token", WEBHOOK, {}, request, lambda: DAY)
            self.assertEqual(request.call_count, 3)

    def test_missing_or_duplicate_reservation_blocks_post(self):
        for data in (listing(), listing(41), listing(41, 42)):
            request = Mock(return_value=data)
            with self.assertRaises(dc.ChangelogError):
                dc.send_once(NAME, DAY, "42", "token", WEBHOOK, {}, request, lambda: DAY)
            self.assertEqual(request.call_count, 1)

    def test_date_changes_before_post(self):
        request = Mock(side_effect=[listing(42), TARGET])
        today = Mock(side_effect=[DAY, "2026-11-27"])
        with self.assertRaisesRegex(dc.ChangelogError, "no longer current"):
            dc.send_once(NAME, DAY, "42", "token", WEBHOOK, {}, request, today)
        self.assertEqual(request.call_count, 2)

    def test_context_guards(self):
        env = {
            "GITHUB_EVENT_NAME": "workflow_dispatch",
            "GITHUB_REPOSITORY": dc.REPO,
            "GITHUB_REF": dc.REF,
            "GITHUB_RUN_ATTEMPT": "1",
        }
        dc.check_live_context({"live": "true"}, env)
        for key, wrong in (
            ("GITHUB_RUN_ATTEMPT", "2"),
            ("GITHUB_REF", "refs/heads/main"),
            ("GITHUB_REPOSITORY", "example/fork"),
            ("GITHUB_EVENT_NAME", "push"),
        ):
            with self.assertRaises(dc.ChangelogError):
                dc.check_live_context({"live": "true"}, {**env, key: wrong})
        with self.assertRaises(dc.ChangelogError):
            dc.check_live_context({"live": "false"}, env)

    def test_transport_redirect_timeout_and_provider_errors(self):
        self.assertIsNone(dc.NoRedirect().redirect_request(None, None, 302, "", {}, "elsewhere"))
        for error in (
            TimeoutError(WEBHOOK),
            urllib.error.HTTPError(WEBHOOK, 429, WEBHOOK, {}, None),
        ):
            with patch.object(dc.urllib.request, "build_opener") as build:
                build.return_value.open.side_effect = error
                with self.assertRaises(dc.ChangelogError) as caught:
                    dc.read_json(WEBHOOK, payload={})
                self.assertNotIn(WEBHOOK, str(caught.exception))
                self.assertEqual(build.return_value.open.call_count, 1)

    def test_dry_entry_point_never_requests_or_reserves(self):
        with tempfile.TemporaryDirectory() as directory:
            event_file = Path(directory) / "event.json"
            event_file.write_text(json.dumps({"inputs": inputs("Fixed a bug")}), encoding="utf-8")
            with (
                patch.dict(dc.os.environ, {"GITHUB_EVENT_PATH": str(event_file)}, clear=True),
                patch.object(dc, "today_mountain", return_value=DAY),
                patch.object(dc, "reserve_preflight") as reserve,
                patch.object(dc, "send_once") as send,
                redirect_stdout(io.StringIO()) as output,
            ):
                dc.main(["sender", "dry"])
                reserve.assert_not_called()
                send.assert_not_called()
                self.assertIn("Dry run", output.getvalue())

    def test_mountain_date_in_winter_and_summer(self):
        datetime = dt.datetime
        for month, date in ((1, "2026-01-14"), (7, "2026-07-14")):
            instant = datetime(2026, month, 15, 3, tzinfo=dt.UTC)
            with patch.object(dc.dt, "datetime") as clock:
                clock.now.side_effect = instant.astimezone
                self.assertEqual(dc.today_mountain(), date)


if __name__ == "__main__":
    unittest.main()
