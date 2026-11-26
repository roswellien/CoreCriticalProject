import datetime as dt
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import discord_release_announcement as da

NOW = dt.datetime(2026, 11, 26, 14, tzinfo=dt.UTC)
HINT = {"id": 531, "tag": "v1.0.59-preview"}
SHA = "1" * 40
WEBHOOK = "https://discord.com/api/webhooks/123456789012345678/" + "a" * 60
ACTIVATION = '{"since":"2026-11-26T08:00:00Z","corecritical":"1.0.58","mw3":"1.0.48"}'
BUNDLED = (
    "Core Critical 1.0.59-preview updates the bundled MW3-RE runtime. Missions can recover from some memory failures."
    "\n\n<!-- corecritical-discord-targets: corecritical=1.0.59,mw3=1.0.49 -->"
)
HISTORICAL = (
    "Core Critical 1.0.58-preview updates the bundled MW3-RE runtime so a mission keeps running "
    "when a model or texture doesn't fit in video memory.\n\n"
    "Existing players can choose **Check for Updates** in the launcher."
)


def release(body=BUNDLED, hint=HINT, **changes):
    return {
        "id": hint["id"],
        "tag_name": hint["tag"],
        "html_url": f"https://github.com/{da.REPO}/releases/tag/{hint['tag']}",
        "prerelease": hint["tag"].endswith("-preview"),
        "draft": False,
        "published_at": "2026-11-26T12:00:00Z",
        "body": body,
        **changes,
    }


def catalog(launcher="1.0.59", runtime="1.0.49"):
    entries = []
    for k, version in zip(da.TARGETS, (launcher, runtime), strict=True):
        path, contract, extension, game = da.TARGETS[k]
        entries.append(
            {
                "product_id": k,
                "game_id": game,
                "version": version,
                "numeric_version": version,
                "status": "promoted",
                "os": "windows",
                "architecture": "x64",
                "contract": contract,
                **{
                    key: {
                        "filename": f"{version}.{ext}",
                        "url": f"{da.ORIGIN}/{path}/{version}/{version}.{ext}",
                        "bytes": 10,
                        "sha256": "f" * 64,
                    }
                    for key, ext in (("metadata", extension), ("payload", "zip"))
                },
            }
        )
    return {
        "schema_version": 1,
        "type": "corecritical-release-catalog-v1",
        "channel": "playtest",
        "sequence": 2026112601,
        "issued_utc": "2026-11-26T12:00:00Z",
        "expires_utc": "2026-12-26T12:00:00Z",
        "releases": entries,
    }


class AnnouncementTests(unittest.TestCase):
    def test_public_preview_with_independently_versioned_bundle(self):
        name, payload = da.qualify(release(), HINT, catalog(), ACTIVATION, NOW)
        self.assertEqual(name, "discord-release-reservation-1.0.59")
        self.assertIn("1.0.59 Preview", payload["content"])
        self.assertIn("Check for Updates", payload["content"])
        self.assertIn(release()["html_url"], payload["content"])
        self.assertNotIn("discord-targets", payload["content"])
        self.assertEqual(payload["allowed_mentions"], {"parse": []})
        self.assertEqual(payload["flags"], 4100)

    def test_stable_launcher_and_runtime_only(self):
        stable = {**HINT, "tag": "v1.0.59"}
        launcher = release("This release improves the launcher and opens settings faster.", stable)
        _, payload = da.qualify(launcher, stable, catalog(runtime="1.0.48"), ACTIVATION, NOW)
        self.assertNotIn("Preview", payload["content"])
        runtime = release("This update fixes the runtime and reduces load stutter.", stable)
        da.qualify(runtime, stable, catalog(launcher="1.0.58", runtime="1.0.59"), ACTIVATION, NOW)

    def test_lag_and_independent_historical_notes(self):
        with self.assertRaises(da.FeedPending):
            da.qualify(release(), HINT, catalog(runtime="1.0.48"), ACTIVATION, NOW)
        prior = {**HINT, "tag": "v1.0.58-preview"}
        with self.assertRaisesRegex(da.ChangelogError, "independently versioned"):
            da.qualify(
                release(HISTORICAL, prior), prior, catalog("1.0.58", "1.0.48"), "", NOW, dry=True
            )

    def test_reject_draft_packs_backfill_renewal_and_invalid_feed(self):
        bad = [
            (release(draft=True), catalog()),
            (release(prerelease=False), catalog()),
            (release("This release adds the Orion asset pack and textures."), catalog()),
            (release(published_at="2026-11-26T04:00:00Z"), catalog()),
            (release(), {**catalog(), "expires_utc": "2026-11-26T13:00:00Z"}),
            (release(), {**catalog(), "releases": catalog()["releases"] * 2}),
            (release(), {**catalog(), "channel": "different"}),
        ]
        for public, feed in bad:
            with self.subTest(public=public), self.assertRaises(da.ChangelogError):
                da.qualify(public, HINT, feed, ACTIVATION, NOW)
        base = '{"since":"2026-11-26T08:00:00Z","corecritical":"1.0.59","mw3":"1.0.49"}'
        with self.assertRaisesRegex(da.ChangelogError, "No new product version"):
            da.qualify(release(), HINT, catalog(), base, NOW)

    def test_notes_do_not_forward_urls_or_mentions(self):
        safe = da.public_blurb(
            "Fixed a renderer crash and [supported updates](https://playtest.corecritical.dev/private) @everyone."
        )
        self.assertNotIn("https:", safe)
        self.assertNotIn("@", safe)
        with self.assertRaises(da.ChangelogError):
            da.public_blurb("Click www.example.com for a copy of the installer.")

    def test_manual_dry_qualifies_without_webhook_or_reservation(self):
        with tempfile.TemporaryDirectory() as directory:
            event = Path(directory) / "event.json"
            event.write_text(json.dumps({"inputs": {"release_id": "531"}}), encoding="utf-8")
            with (
                patch.dict(da.os.environ, {"GITHUB_EVENT_PATH": str(event)}, clear=True),
                patch.object(
                    da, "read_json", side_effect=[release(), {"signed": "fixture"}]
                ) as get,
                patch.object(da, "verified_catalog", return_value=catalog()),
                patch.object(da.dt, "datetime", wraps=dt.datetime) as clock,
                patch.object(da, "check_webhook") as webhook,
                patch.object(da, "send_once") as send,
                patch("builtins.print") as output,
            ):
                clock.now.return_value = NOW
                da.main(["announcement", "dry"])
                self.assertEqual(get.call_count, 2)
                webhook.assert_not_called()
                send.assert_not_called()
                output.assert_called_once_with(
                    "Dry run: published release and signed feed agree; no message sent"
                )

    def test_tag_origin_and_wrong_workflow(self):
        repository = {"full_name": da.REPO, "id": 42}
        upstream = {
            "event": "release",
            "conclusion": "success",
            "run_attempt": 1,
            "name": "Observe CoreCritical release",
            "path": da.WORKFLOW,
            "head_repository": repository,
            "head_branch": "refs/tags/v1.0.59-preview",
            "head_sha": SHA,
        }
        event = {"action": "completed", "repository": repository, "workflow_run": upstream}
        env = {
            "GITHUB_REPOSITORY": da.REPO,
            "GITHUB_REF": da.REF,
            "GITHUB_EVENT_NAME": "workflow_run",
            "GITHUB_RUN_ATTEMPT": "1",
        }
        da.guard_event(event, env)
        ref = {"ref": "refs/tags/v1.0.59-preview", "object": {"type": "commit", "sha": SHA}}
        da.check_observer_tag(upstream, HINT["tag"], Mock(return_value=ref))
        da.check_observer_tag(
            {**upstream, "head_branch": None}, HINT["tag"], Mock(return_value=ref)
        )
        with self.assertRaises(da.ChangelogError):
            da.check_observer_tag(
                {**upstream, "head_sha": "2" * 40}, HINT["tag"], Mock(return_value=ref)
            )
        for key, bad in (("path", "untrusted.yml"), ("event", "pull_request"), ("run_attempt", 2)):
            with self.assertRaises(da.ChangelogError):
                da.guard_event({**event, "workflow_run": {**upstream, key: bad}}, env)
        with self.assertRaises(da.ChangelogError):
            da.guard_event(event, {**env, "GITHUB_REF": upstream["head_branch"]})

    def test_one_post_and_fail_closed_before_post(self):
        name, payload = da.qualify(release(), HINT, catalog(), ACTIVATION, NOW)
        artifact = {"total_count": 1, "artifacts": [{"name": name, "id": 42, "expired": False}]}
        destination = {"type": 1, "guild_id": da.GUILD, "channel_id": da.CHANNEL}
        receipt = {"id": "912345678901234567", "channel_id": da.CHANNEL}
        request = Mock(side_effect=[artifact, destination, receipt])
        self.assertTrue(
            da.send_once(name, "42", "gh", WEBHOOK, payload, request).endswith(receipt["id"])
        )
        self.assertEqual(request.call_args.kwargs, {"payload": payload})
        for replies, count in (
            ([{"total_count": 0, "artifacts": []}], 1),
            ([artifact, {**destination, "channel_id": "other"}], 2),
            ([artifact, destination, da.ChangelogError("timeout")], 3),
        ):
            request = Mock(side_effect=replies)
            with self.assertRaises(da.ChangelogError):
                da.send_once(name, "42", "gh", WEBHOOK, payload, request)
            self.assertEqual(request.call_count, count)

    @unittest.skipUnless(shutil.which("pwsh"), "PowerShell Core required for signature fixture")
    def test_generated_signature_and_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            material = base / "catalog.json"
            key = base / "key.pem"
            trust = base / "trust.json"
            envelope = base / "signed.json"
            material.write_text(json.dumps(catalog()), encoding="utf-8")
            subprocess.run(
                [
                    "pwsh",
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    (
                        "$r=[Security.Cryptography.RSA]::Create(3072); "
                        "[IO.File]::WriteAllText('key.pem',$r.ExportPkcs8PrivateKeyPem()); "
                        "@{public_keys=@{test=$r.ExportSubjectPublicKeyInfoPem()}} | "
                        "ConvertTo-Json | Set-Content -Encoding utf8 trust.json; $r.Dispose()"
                    ),
                ],
                cwd=base,
                check=True,
                capture_output=True,
                timeout=30,
            )
            subprocess.run(
                [
                    "pwsh",
                    "-NoProfile",
                    "-File",
                    str(da.ROOT / "tools/mw3-remaster-launcher/sign_runtime_update.ps1"),
                    "-Manifest",
                    str(material),
                    "-SigningKey",
                    str(key),
                    "-KeyId",
                    "test",
                    "-OutputFile",
                    str(envelope),
                ],
                check=True,
                capture_output=True,
                timeout=30,
            )
            signed = json.loads(envelope.read_text(encoding="utf-8"))
            self.assertEqual(da.verified_catalog(signed, trust), catalog())
            with self.assertRaises(da.ChangelogError):
                da.verified_catalog({**signed, "payload": "e30="}, trust)


if __name__ == "__main__":
    unittest.main()
