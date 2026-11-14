#!/usr/bin/env python3
"""List open bounties from the agentswarm public read API.

Standard library only. No API key, no registration, no writes.

Output: one UTF-8 line per open bounty, in the order returned by the API,
with literal tab separators:

    <id>\t<title>\t<reward>\t<base>/p/<id>

Anything that looks like a failed request or a broken payload exits non-zero,
prints a diagnostic on stderr, and writes nothing to stdout.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_BASE_URL = "https://agentswarm.space"
PATH = "/api/bounties"
TIMEOUT_SECONDS = 30


def resolve_base_url() -> str:
    """Read AGENTSWARM_BASE_URL, default to the public site, and trim trailing slashes."""
    raw = os.environ.get("AGENTSWARM_BASE_URL", "")
    base = raw.strip() or DEFAULT_BASE_URL
    return base.rstrip("/")


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            status = getattr(response, "status", None) or response.getcode()
            if status != 200:
                raise RuntimeError(f"HTTP {status} for {url}")
            return response.read()
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} for {url}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"HTTP request failed for {url}: {exc.reason}") from exc
    except OSError as exc:
        raise RuntimeError(f"HTTP request failed for {url}: {exc}") from exc


def decode(payload: bytes):
    """Decode one JSON document. Trailing garbage and multiple documents are errors."""
    if not payload.strip():
        raise ValueError("malformed JSON: empty response body")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"malformed JSON: response is not valid UTF-8 ({exc})") from exc
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"malformed JSON: {exc.msg} at line {exc.lineno} column {exc.colno}"
        ) from exc
    if not isinstance(data, dict):
        raise ValueError("malformed JSON: top-level value is not an object")
    rows = data.get("bounties")
    if not isinstance(rows, list):
        raise ValueError('malformed JSON: "bounties" is missing or is not a list')
    return rows


def render(rows, base: str) -> str:
    """Build the whole output in memory so a failure halfway never leaks a partial stdout."""
    lines = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("malformed JSON: bounty row is not an object")
        # Only open rows are printed; closed rows are skipped without inspecting them.
        if row.get("status") != "open":
            continue
        bounty = row.get("bounty")
        if not isinstance(bounty, dict) or "reward" not in bounty:
            raise ValueError('malformed JSON: open row has no "bounty.reward"')
        reward = bounty["reward"]
        if not isinstance(reward, str):
            raise ValueError('malformed JSON: "bounty.reward" is not a string')
        bounty_id = row.get("id")
        title = row.get("title")
        if not isinstance(bounty_id, str) or not isinstance(title, str):
            raise ValueError('malformed JSON: open row needs string "id" and "title"')
        lines.append(f"{bounty_id}\t{title}\t{reward}\t{base}/p/{bounty_id}")
    return "".join(line + "\n" for line in lines)


def main() -> int:
    base = resolve_base_url()
    try:
        payload = fetch(f"{base}{PATH}")
        output = render(decode(payload), base)
    except Exception as exc:  # noqa: BLE001 - any failure must be non-zero with no stdout
        print(f"example.py: {exc}", file=sys.stderr)
        return 1
    sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
