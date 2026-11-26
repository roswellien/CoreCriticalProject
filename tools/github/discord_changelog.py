"""Validate and send a curated CoreCritical changelog, once per Mountain date."""

import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = "roswellien/CoreCriticalProject"
REF = "refs/heads/develop"
GUILD = "1562413268843110492"
CHANNEL = "1575495199998742598"
WEBSITE = "https://corecritical.dev/"
YOUTUBE = "https://www.youtube.com/channel/UC0YGz5FEh7-ij1miUmXECiw/videos"
WEBHOOK = re.compile(
    r"https://discord\.com/api(?:/v10)?/webhooks/[0-9]{17,22}/[\w-]{30,200}", re.ASCII
)
VERSION = re.compile(r"[0-9]{1,5}\.[0-9]{1,5}\.[0-9]{1,5}(?:[- ]preview)?", re.IGNORECASE)
SNOWFLAKE = re.compile(r"[0-9]{17,22}")
DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


class ChangelogError(Exception):
    """A safe, fixed diagnostic that never includes transport details."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def today_mountain():
    return dt.datetime.now(ZoneInfo("America/Denver")).date().isoformat()


def units(text):
    return len(text.encode("utf-16-le")) // 2


def format_payload(inputs, today):
    if not isinstance(inputs, dict):
        raise ChangelogError("Inputs are missing")
    day = inputs.get("date")
    if not isinstance(day, str) or not DATE.fullmatch(day) or day != today:
        raise ChangelogError("Use the current Mountain calendar date")
    version = inputs.get("version")
    if not isinstance(version, str) or not VERSION.fullmatch(version):
        raise ChangelogError("Use a verified public version number")
    raw = inputs.get("bullets")
    if not isinstance(raw, str) or len(raw) > 24000:
        raise ChangelogError("Bullet input must be a bounded JSON array")
    try:
        bullets = json.loads(raw)
    except (ValueError, RecursionError):
        raise ChangelogError("Bullet input must be a JSON array") from None
    if not isinstance(bullets, list) or not 1 <= len(bullets) <= 60:
        raise ChangelogError("Supply 1 to 60 substantive bullets")
    for bullet in bullets:
        if not isinstance(bullet, str) or not bullet.strip():
            raise ChangelogError("Every bullet must be nonempty text")
        if any(ord(c) < 32 or 127 <= ord(c) <= 159 or 0xD800 <= ord(c) <= 0xDFFF for c in bullet):
            raise ChangelogError("Use a single line without control characters per bullet")
    heading = f"CoreCritical MW3 Recomp | What Changed Today | {day}"
    changes = "\n".join(f"- {bullet.strip()}" for bullet in bullets)
    footer = (
        f"*Latest version: {version}. Don’t forget to update!*\n\n"
        f"Enjoying CoreCritical? Share the [project website]({WEBSITE}) "
        f"or our [YouTube channel]({YOUTUBE})."
    )
    body = f"{changes}\n\n{footer}"
    content = f"**{heading}**\n\n{body}"
    payload = {"allowed_mentions": {"parse": []}, "flags": 4096}
    if units(content) <= 2000:
        payload["content"] = content
        payload["flags"] |= 4
    elif units(body) <= 4096:
        payload["embeds"] = [{"title": heading, "description": body}]
    else:
        raise ChangelogError("Changelog exceeds a single Discord post; nothing was truncated")
    return day, payload


def read_json(url, *, headers=None, payload=None, max_bytes=131072):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "CoreCritical-Discord-Changelog", **(headers or {})},
        data=None if payload is None else json.dumps(payload).encode("utf-8"),
    )
    if payload is not None:
        request.add_header("Content-Type", "application/json")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(request, timeout=12) as response:
            raw = response.read(max_bytes + 1)
            if len(raw) > max_bytes:
                raise ChangelogError("Provider response exceeded the limit")
            result = json.loads(raw)
    except urllib.error.HTTPError as error:
        with error:
            raise ChangelogError(f"Provider rejected request (HTTP {error.code})") from None
    except (OSError, ValueError, RecursionError):
        raise ChangelogError("Provider response unavailable or invalid") from None
    if not isinstance(result, dict):
        raise ChangelogError("Provider returned unexpected data")
    return result


def check_webhook(url, request=read_json):
    if not WEBHOOK.fullmatch(url):
        raise ChangelogError("A valid Discord webhook secret is required")
    webhook = request(url)
    if (
        webhook.get("type") != 1
        or webhook.get("guild_id") != GUILD
        or webhook.get("channel_id") != CHANNEL
    ):
        raise ChangelogError("Discord destination mismatch; no message sent")


def reservations(name, token, request=read_json):
    if not token:
        raise ChangelogError("GitHub reservation access is unavailable")
    query = urllib.parse.urlencode({"name": name, "per_page": 100})
    data = request(
        f"https://api.github.com/repos/{REPO}/actions/artifacts?{query}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    artifacts = data.get("artifacts")
    if not isinstance(artifacts, list) or data.get("total_count") != len(artifacts):
        raise ChangelogError("Unable to verify the complete reservation list")
    if any(
        not isinstance(item, dict)
        or item.get("name") != name
        or type(item.get("id")) is not int
        or type(item.get("expired")) is not bool
        for item in artifacts
    ):
        raise ChangelogError("Unexpected GitHub reservation data")
    return [item["id"] for item in artifacts if not item["expired"]]


def reserve_preflight(name, token, webhook, request=read_json):
    if reservations(name, token, request):
        raise ChangelogError("This date already has a send reservation")
    check_webhook(webhook, request)


def send_once(
    name, day, artifact_id, token, webhook, payload, request=read_json, today=today_mountain
):
    if not re.fullmatch(r"[1-9][0-9]{0,21}", artifact_id):
        raise ChangelogError("A verified reservation ID is required")
    if reservations(name, token, request) != [int(artifact_id)]:
        raise ChangelogError("The unique send reservation is not visible")
    if today() != day:
        raise ChangelogError("The report date is no longer current")
    check_webhook(webhook, request)
    if today() != day:
        raise ChangelogError("The report date is no longer current")
    try:
        delivered = request(webhook + "?wait=true", payload=payload)
    except ChangelogError:
        raise ChangelogError("Discord delivery not confirmed; do not rerun") from None
    message_id = delivered.get("id")
    if (
        not isinstance(message_id, str)
        or not SNOWFLAKE.fullmatch(message_id)
        or delivered.get("channel_id") != CHANNEL
    ):
        raise ChangelogError("Discord delivery not confirmed; do not rerun")
    return f"https://discord.com/channels/{GUILD}/{CHANNEL}/{message_id}"


def check_live_context(inputs, environment):
    if (
        inputs.get("live") not in (True, "true")
        or environment.get("GITHUB_EVENT_NAME") != "workflow_dispatch"
        or environment.get("GITHUB_REPOSITORY") != REPO
        or environment.get("GITHUB_REF") != REF
        or environment.get("GITHUB_RUN_ATTEMPT") != "1"
    ):
        raise ChangelogError("Live sending requires an explicit first dispatch on develop")


def main(argv):
    if len(argv) != 2 or argv[1] not in ("dry", "reserve", "send"):
        raise ChangelogError("Expected dry, reserve, or send mode")
    mode = argv[1]
    try:
        event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
    except (KeyError, OSError, ValueError):
        raise ChangelogError("Cannot read the workflow dispatch inputs") from None
    inputs = event.get("inputs") if isinstance(event, dict) else None
    day, payload = format_payload(inputs, today_mountain())
    if mode == "dry":
        print("Dry run: changelog payload validated; no Discord request or reservation")
        return

    check_live_context(inputs, os.environ)
    name = f"discord-changelog-reservation-{day}"
    token = os.environ.get("GH_TOKEN", "")
    webhook = os.environ.get("DISCORD_CHANGELOG_WEBHOOK_URL", "")
    if mode == "reserve":
        reserve_preflight(name, token, webhook)
        marker = Path(os.environ["RUNNER_TEMP"]) / "discord-changelog-reservation.txt"
        marker.write_text(day + "\n", encoding="ascii")
        with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as output:
            print(f"name={name}", file=output)
        return

    link = send_once(name, day, os.environ.get("RESERVATION_ID", ""), token, webhook, payload)
    print(f"Posted: {link}")
    with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as summary:
        print(f"[Verified Discord message]({link})", file=summary)


if __name__ == "__main__":
    try:
        main(sys.argv)
    except (ChangelogError, OSError, KeyError) as error:
        print(
            str(error) if isinstance(error, ChangelogError) else "Runner configuration failed",
            file=sys.stderr,
        )
        sys.exit(1)
