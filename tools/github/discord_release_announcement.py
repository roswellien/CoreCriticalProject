"""Qualify published releases against the signed update feed before announcing."""

import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from discord_changelog import (
    CHANNEL,
    GUILD,
    REF,
    REPO,
    SNOWFLAKE,
    ChangelogError,
    check_webhook,
    read_json,
    reservations,
)

ORIGIN = "https://core-critical-updates.jcblackwell84.workers.dev"
FEED = f"{ORIGIN}/channels/playtest/catalog.json"
API = f"https://api.github.com/repos/{REPO}"
WORKFLOW = ".github/workflows/discord-release-detect.yml"
AGE_LIMIT = dt.timedelta(hours=24)
VERSION = r"(?:0|[1-9][0-9]{0,4})\.(?:0|[1-9][0-9]{0,4})\.(?:0|[1-9][0-9]{0,4})"
TAG = re.compile(rf"v({VERSION})(-preview)?")
TARGETS = {
    "corecritical": ("launcher", "launcher-inno-v1", "ccupdate", None),
    "mw3": ("mw3", "mw3-local-runtime-v1", "mw3update", "mw3"),
}
MARKER = re.compile(
    rf"<!-- corecritical-discord-targets: ((?:corecritical|mw3)={VERSION}(?:,(?:corecritical|mw3)={VERSION})?) -->"
)
ROOT = Path(__file__).resolve().parents[2]


class FeedPending(ChangelogError):
    """The expected release is not promoted yet."""


def timestamp(value):
    try:
        parsed = dt.datetime.fromisoformat(value)
        if parsed.utcoffset() is None:
            raise ValueError
        return parsed.astimezone(dt.UTC)
    except (TypeError, ValueError, OverflowError):
        raise ChangelogError("Missing or invalid timestamp") from None


def version_tuple(value):
    if not isinstance(value, str) or not re.fullmatch(VERSION, value):
        raise ChangelogError("Invalid product version")
    return tuple(map(int, value.split(".")))


def activation_config(raw, now):
    try:
        value = json.loads(raw)
    except (TypeError, ValueError):
        raise ChangelogError("Release announcements are not configured") from None
    if not isinstance(value, dict) or set(value) != {"since", *TARGETS}:
        raise ChangelogError("Set the activation date and both current product versions")
    since = timestamp(value["since"])
    if since > now:
        raise ChangelogError("Release announcements are not active yet")
    return since, {key: version_tuple(value[key]) for key in TARGETS}


def verified_catalog(envelope, trust=None):
    script = Path(__file__).with_name("verify_discord_release_catalog.ps1")
    try:
        result = subprocess.run(
            [
                "pwsh",
                "-NoProfile",
                "-NonInteractive",
                "-File",
                str(script),
                "-Trust",
                str(trust or ROOT / "tools/mw3-remaster-launcher/update-trust.json"),
            ],
            input=json.dumps(envelope).encode("utf-8"),
            capture_output=True,
            timeout=15,
            check=True,
        )
        return json.loads(result.stdout)
    except (OSError, subprocess.SubprocessError, ValueError, RecursionError):
        raise ChangelogError("Live catalog signature could not be verified") from None


def catalog_versions(catalog, now):
    if (
        not isinstance(catalog, dict)
        or catalog.get("schema_version") != 1
        or catalog.get("type") != "corecritical-release-catalog-v1"
        or catalog.get("channel") != "playtest"
        or type(catalog.get("sequence")) is not int
        or catalog["sequence"] <= 0
    ):
        raise ChangelogError("Unsupported live catalog")
    issued = timestamp(catalog.get("issued_utc"))
    expires = timestamp(catalog.get("expires_utc"))
    if not issued <= now < expires or expires - issued > dt.timedelta(days=30):
        raise ChangelogError("Live catalog is expired, future-dated or inconsistent")
    releases = catalog.get("releases")
    if not isinstance(releases, list) or len(releases) > 16:
        raise ChangelogError("Invalid release records in live catalog")
    current = {}
    for item in releases:
        if not isinstance(item, dict):
            raise ChangelogError("Invalid release record in live catalog")
        product = item.get("product_id")
        if not isinstance(product, str) or product not in TARGETS:
            continue
        path, contract, ext, game = TARGETS[product]
        version = item.get("numeric_version")
        version_tuple(version)
        if (
            product in current
            or item.get("status") != "promoted"
            or item.get("os") != "windows"
            or item.get("architecture") != "x64"
            or item.get("version") != version
            or item.get("contract") != contract
            or item.get("game_id") != game
        ):
            raise ChangelogError("Ambiguous or unsupported promoted release")
        for key, extension in (("metadata", ext), ("payload", "zip")):
            filename = f"{version}.{extension}"
            entry = item.get(key)
            if (
                not isinstance(entry, dict)
                or entry.get("filename") != filename
                or entry.get("url") != f"{ORIGIN}/{path}/{version}/{filename}"
                or type(entry.get("bytes")) is not int
                or entry["bytes"] <= 0
                or not isinstance(entry.get("sha256"), str)
                or not re.fullmatch(r"[a-f0-9]{64}", entry["sha256"])
            ):
                raise ChangelogError("Promoted package record is invalid")
        current[product] = version
    if not current:
        raise ChangelogError("No supported products in the live catalog")
    return current


def public_blurb(notes):
    notes = MARKER.sub("", notes).strip()
    paragraph = re.split(r"\n[ \t]*\n", notes, maxsplit=1)[0]
    # Remove links and HTML; block leftover URLs rather than forwarding them.
    paragraph = re.sub(r"\[([^\]\n]{1,150})\]\([^) \n]{1,800}\)", r"\1", paragraph)
    paragraph = re.sub(r"<[^>\n]{1,500}>", "", paragraph)
    paragraph = " ".join(paragraph.split())
    if (
        not paragraph
        or re.search(r"://|www\.|discord\.gg|playtest\.corecritical", paragraph, re.IGNORECASE)
        or any(ord(c) < 32 or 127 <= ord(c) <= 159 or 0xD800 <= ord(c) <= 0xDFFF for c in paragraph)
    ):
        raise ChangelogError("First public release-note paragraph is missing or unsafe")
    paragraph = re.sub(r"[\x60*_~|#@<>\[\]\\]", "", paragraph)
    # Shorten at a whole sentence or word; don't cut a multi-byte character.
    sentences = re.split(r"(?<=[.!?])\s+", paragraph)
    compact = " ".join(sentences[:2])
    if len(compact) > 420:
        compact = compact[:416].rsplit(" ", 1)[0].rstrip(".,;:") + "…"
    if len(compact.strip()) < 12:
        raise ChangelogError("No usable release-note change summary")
    return compact


def affected_targets(notes, tag_version, current):
    markers = MARKER.findall(notes)
    if len(markers) > 1 or ("corecritical-discord-targets" in notes and not markers):
        raise ChangelogError("Release target metadata is ambiguous or malformed")
    if markers:
        pairs = [item.split("=") for item in markers[0].split(",")]
        targets = dict(pairs)
        if len(targets) != len(pairs) or tag_version not in targets.values():
            raise ChangelogError("Release metadata must uniquely identify affected versions")
        return targets
    first = re.split(r"\n[ \t]*\n", notes.strip(), maxsplit=1)[0]
    if re.search(r"bundl(?:ed|es|ing).{0,100}\bruntime\b", first, re.IGNORECASE):
        # A matching version for both signed products is unambiguous. Otherwise
        # the public notes must explicitly bind the other affected version.
        if all(current.get(key) == tag_version for key in TARGETS):
            return dict.fromkeys(TARGETS, tag_version)
        explicit = re.search(
            rf"\bruntime(?:\s+version)?\s+v?({VERSION})(?![\d.])", first, re.IGNORECASE
        )
        if explicit:
            return {"corecritical": tag_version, "mw3": explicit[1]}
        raise ChangelogError("Bundled release needs explicit independently versioned targets")
    launcher = bool(
        re.search(
            r"\b(?:updates?|fixes?|improves?)\s+(?:the\s+)?(?:Core Critical\s+)?launcher\b",
            first,
            re.IGNORECASE,
        )
    )
    runtime = bool(
        re.search(
            r"\b(?:updates?|fixes?|improves?)\s+(?:the\s+)?(?:MW3-RE\s+)?runtime\b",
            first,
            re.IGNORECASE,
        )
    )
    if launcher == runtime:
        raise ChangelogError("Release notes do not identify a launcher or runtime update")
    return {"corecritical" if launcher else "mw3": tag_version}


def qualify(release, hint, catalog, activation, now, dry=False):
    tag = hint["tag"]
    numeric, preview = TAG.fullmatch(tag).groups()
    link = f"https://github.com/{REPO}/releases/tag/{tag}"
    if (
        release.get("id") != hint["id"]
        or release.get("tag_name") != tag
        or release.get("html_url") != link
        or release.get("draft") is not False
        or release.get("prerelease") is not bool(preview)
    ):
        raise ChangelogError("GitHub release is not the expected public launcher/runtime release")
    published = timestamp(release.get("published_at"))
    if published > now:
        raise ChangelogError("GitHub release has a future publication date")
    if not dry:
        since, baseline = activation_config(activation, now)
        if published <= since or now - published > AGE_LIMIT:
            raise ChangelogError("Release is not eligible after activation or is too old")
    current = catalog_versions(catalog, now)
    notes = release.get("body")
    if not isinstance(notes, str) or not 1 <= len(notes) <= 24000:
        raise ChangelogError("Published notes are missing or too large")
    targets = affected_targets(notes, numeric, current)
    if not dry and not any(version_tuple(v) > baseline[k] for k, v in targets.items()):
        raise ChangelogError("No new product version after activation")
    if any(current.get(key) != version for key, version in targets.items()):
        raise FeedPending("Affected versions have not matched the signed live feed")
    version = numeric + (" Preview" if preview else "")
    payload = {
        "content": (
            f"**CoreCritical {version} is live.** {public_blurb(notes)}\n"
            f"Open the launcher and choose **Check for Updates**. [What changed]({link})"
        ),
        "flags": 4096 | 4,
        "allowed_mentions": {"parse": []},
    }
    return f"discord-release-reservation-{numeric}", payload


def guard_event(event, env):
    run = event.get("workflow_run") or {}
    head = run.get("head_repository") or {}
    repo = event.get("repository") or {}
    if (
        env.get("GITHUB_REPOSITORY") != REPO
        or env.get("GITHUB_REF") != REF
        or env.get("GITHUB_EVENT_NAME") != "workflow_run"
        or env.get("GITHUB_RUN_ATTEMPT") != "1"
        or event.get("action") != "completed"
        or run.get("event") != "release"
        or run.get("conclusion") != "success"
        or run.get("run_attempt") != 1
        or head.get("full_name") != REPO
        or type(head.get("id")) is not int
        or head["id"] != repo.get("id")
        or repo.get("full_name") != REPO
        or run.get("name") != "Observe CoreCritical release"
        or not isinstance(run.get("path"), str)
        or run["path"].split("@", 1)[0] != WORKFLOW
    ):
        raise ChangelogError("Not a trusted release-observer completion on develop")


def read_hint(path):
    with path.open("rb") as stream:
        raw = stream.read(257)
    if len(raw) > 256:
        raise ChangelogError("Release hint is too large")
    hint = json.loads(raw)
    if (
        not isinstance(hint, dict)
        or set(hint) != {"id", "tag"}
        or type(hint["id"]) is not int
        or not 1 <= hint["id"] < 10**20
        or not isinstance(hint["tag"], str)
        or not TAG.fullmatch(hint["tag"])
    ):
        raise ChangelogError("Release hint does not identify a supported release tag")
    return hint


def check_observer_tag(run, tag, request=read_json):
    branch = run.get("head_branch")
    if branch is not None and branch not in (tag, f"refs/tags/{tag}"):
        raise ChangelogError("Observer tag identity does not match the release hint")
    ref = request(f"{API}/git/ref/tags/{tag}")
    if ref.get("ref") != f"refs/tags/{tag}":
        raise ChangelogError("Release tag could not be confirmed")
    obj = ref.get("object")
    for _ in range(4):
        if not isinstance(obj, dict):
            break
        sha = obj.get("sha")
        if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
            break
        if obj.get("type") == "commit" and sha == run.get("head_sha"):
            return
        if obj.get("type") != "tag":
            break
        obj = request(f"{API}/git/tags/{sha}").get("object")
    raise ChangelogError("Release tag does not identify the observing commit")


def send_once(name, artifact_id, token, webhook, payload, request=read_json):
    if not re.fullmatch(r"[1-9][0-9]{0,21}", artifact_id) or reservations(name, token, request) != [
        int(artifact_id)
    ]:
        raise ChangelogError("The unique release reservation is not visible")
    check_webhook(webhook, request)
    try:
        receipt = request(webhook + "?wait=true", payload=payload)
    except ChangelogError:
        raise ChangelogError("Discord release delivery not confirmed; do not resend") from None
    message = receipt.get("id")
    if (
        not isinstance(message, str)
        or not SNOWFLAKE.fullmatch(message)
        or receipt.get("channel_id") != CHANNEL
    ):
        raise ChangelogError("Discord release delivery not confirmed; do not resend")
    return f"https://discord.com/channels/{GUILD}/{CHANNEL}/{message}"


def get_announcement(hint, activation, *, dry=False, attempts=1):
    for attempt in range(attempts):
        release = read_json(f"{API}/releases/{hint['id']}")
        if not hint.get("tag"):
            tag = release.get("tag_name")
            if not isinstance(tag, str) or not TAG.fullmatch(tag):
                raise ChangelogError("Not a supported public release tag")
            hint = {**hint, "tag": tag}
        catalog = verified_catalog(read_json(FEED, max_bytes=1_500_000))
        try:
            return qualify(release, hint, catalog, activation, dt.datetime.now(dt.UTC), dry)
        except FeedPending:
            if attempt + 1 == attempts:
                raise
            time.sleep(30)
    raise ChangelogError("No release qualified")


def main(argv):
    if len(argv) != 2 or argv[1] not in ("dry", "reserve", "send"):
        raise ChangelogError("Expected dry, reserve, or send")
    mode = argv[1]
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_bytes())
    if mode == "dry":
        ident = (event.get("inputs") or {}).get("release_id")
        if not isinstance(ident, str) or not re.fullmatch(r"[1-9][0-9]{0,19}", ident):
            raise ChangelogError("Provide a numeric public GitHub release ID")
        get_announcement({"id": int(ident), "tag": ""}, "", dry=True)
        print("Dry run: published release and signed feed agree; no message sent")
        return
    guard_event(event, os.environ)
    activation = os.environ.get("DISCORD_RELEASE_ACTIVATION", "")
    activation_config(activation, dt.datetime.now(dt.UTC))
    hint = read_hint(Path(os.environ["RUNNER_TEMP"]) / "corecritical-release-hint" / "hint.json")
    upstream = event["workflow_run"]
    check_observer_tag(upstream, hint["tag"])
    name, payload = get_announcement(hint, activation, attempts=5 if mode == "reserve" else 1)
    token = os.environ.get("GH_TOKEN", "")
    webhook = os.environ.get("DISCORD_CHANGELOG_WEBHOOK_URL", "")
    if mode == "reserve":
        if reservations(name, token):
            raise ChangelogError("This release already has a send reservation")
        check_webhook(webhook)
        marker = Path(os.environ["RUNNER_TEMP"]) / "corecritical-release-reservation.txt"
        marker.write_text(name + "\n", encoding="ascii")
        with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as output:
            print(f"name={name}", file=output)
        return
    link = send_once(name, os.environ.get("RESERVATION_ID", ""), token, webhook, payload)
    print(f"Posted: {link}")
    with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as output:
        print(f"[Verified Discord release announcement]({link})", file=output)


if __name__ == "__main__":
    try:
        main(sys.argv)
    except (ChangelogError, KeyError, TypeError, ValueError, OSError, AttributeError) as error:
        print(
            str(error) if isinstance(error, ChangelogError) else "Invalid runtime input",
            file=sys.stderr,
        )
        sys.exit(1)
