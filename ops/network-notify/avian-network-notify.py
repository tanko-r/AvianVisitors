#!/usr/bin/env python3
"""Send one private status message when wlan0 joins a different SSID.

The bridge token and recipient live in a root-readable configuration file that
is deployed outside the repository. WAHA remains on nanoclaw-box; this program
uses its authenticated Tailscale-facing bridge, never WAHA directly.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import urllib.request

CONFIG = Path("/etc/avianvisitors/network-notify.env")
STATE = Path("/var/lib/avianvisitors/network-notify.json")
INTERFACE = "wlan0"


def run(*args: str) -> str:
    return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL).strip()


def config() -> dict[str, str]:
    values: dict[str, str] = {}
    for line in CONFIG.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    required = {"BRIDGE_URL", "BRIDGE_TOKEN", "CHAT_ID"}
    missing = required - values.keys()
    if missing:
        raise RuntimeError("missing notification configuration")
    return values


def current_network() -> tuple[str, str] | None:
    connection = run("/usr/bin/nmcli", "-g", "GENERAL.CONNECTION", "device", "show", INTERFACE)
    if not connection or connection == "--":
        return None
    ssid = run("/usr/bin/nmcli", "-g", "802-11-wireless.ssid", "connection", "show", connection)
    ip = run("/usr/bin/nmcli", "-g", "IP4.ADDRESS", "device", "show", INTERFACE).splitlines()
    address = next((entry.split("/", 1)[0] for entry in ip if entry), "unassigned")
    return ssid or connection, address


def tailscale_ip() -> str:
    try:
        return run("/usr/bin/tailscale", "ip", "-4")
    except (FileNotFoundError, subprocess.CalledProcessError):
        return "unavailable"


def load_state() -> dict[str, str]:
    try:
        parsed = json.loads(STATE.read_text(encoding="utf-8"))
        return parsed if isinstance(parsed, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_state(ssid: str) -> None:
    STATE.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temp = STATE.with_suffix(".tmp")
    temp.write_text(json.dumps({"ssid": ssid, "at": int(time.time())}) + "\n", encoding="utf-8")
    temp.chmod(0o600)
    temp.replace(STATE)


def send(values: dict[str, str], text: str) -> None:
    body = json.dumps({"chatId": values["CHAT_ID"], "text": text}).encode()
    request = urllib.request.Request(
        values["BRIDGE_URL"],
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "X-Bridge-Token": values["BRIDGE_TOKEN"]},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        if not 200 <= response.status < 300:
            raise RuntimeError("bridge rejected notification")


def main() -> int:
    if os.geteuid() != 0:
        raise RuntimeError("must run as root to protect bridge credentials")
    network = current_network()
    if not network:
        return 0
    ssid, lan_ip = network
    old = load_state().get("ssid")
    if old == ssid:
        return 0
    values = config()
    tail_ip = tailscale_ip()
    message = (
        "AvianVisitors Pi joined Wi-Fi\n"
        f"SSID: {ssid}\nLAN: {lan_ip}\nTailscale: {tail_ip}\n"
        f"SSH: ssh david@{tail_ip}" if tail_ip != "unavailable" else
        "AvianVisitors Pi joined Wi-Fi\n"
        f"SSID: {ssid}\nLAN: {lan_ip}\nTailscale: unavailable"
    )
    send(values, message)
    save_state(ssid)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.CalledProcessError, urllib.error.URLError) as error:
        print(f"avian-network-notify: {error}", file=sys.stderr)
        raise SystemExit(1)
