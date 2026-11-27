#!/usr/bin/env python3
"""Keep a private, last-known Pi access note on the operator computer."""
from __future__ import annotations

from datetime import datetime
import ipaddress
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
NOTE = ROOT / 'REMOTE-ACCESS.txt'
PI = 'david@100.88.155.15'
REMOTE = "hostname; nmcli -g IP4.ADDRESS device show wlan0; tailscale ip -4"


def main() -> None:
    now = datetime.now().astimezone().strftime('%Y-%m-%d %I:%M:%S %p %Z')
    try:
        result = subprocess.run(
            ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10',
             '-o', 'ServerAliveInterval=5', '-o', 'ServerAliveCountMax=2',
             PI, REMOTE], capture_output=True, text=True, timeout=25, check=True,
        )
        lines = result.stdout.strip().splitlines()
        if len(lines) != 3 or lines[0] != 'birdnet':
            raise ValueError('Unexpected Pi response')
        lan = str(ipaddress.IPv4Interface(lines[1]).ip)
        tailnet = str(ipaddress.IPv4Address(lines[2]))
        if tailnet != '100.88.155.15':
            raise ValueError('Unexpected Tailscale address')
    except (OSError, subprocess.SubprocessError, ValueError):
        # Preserve the last successful note; its timestamp shows its age.
        if NOTE.exists():
            return
        content = ('Pi access details have not yet been retrieved.\n'
                   f'Last attempt: {now}\n'
                   f'Try SSH: ssh {PI}\n')
    else:
        content = (
            'AvianVisitors Pi — last successful check\n'
            f'Updated: {now}\n'
            f'Wi-Fi LAN IP: {lan}\n'
            f'Tailscale IP: {tailnet}\n'
            f'Remote SSH: ssh david@{tailnet}\n'
            f'Local-network SSH: ssh david@{lan}\n\n'
            'This file is refreshed on this computer every two hours while it is on.\n'
            'If the Pi is unreachable, these are the last known details; check the timestamp.\n'
            'Tailscale SSH requires the Pi and your device to be online and authorized.\n'
        )
    fd, name = tempfile.mkstemp(prefix='.remote-access-', dir=ROOT, text=True)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            handle.write(content)
        os.replace(name, NOTE)
    finally:
        if os.path.exists(name):
            os.unlink(name)


if __name__ == '__main__':
    main()
