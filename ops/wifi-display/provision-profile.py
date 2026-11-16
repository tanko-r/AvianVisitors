"""Run on the ADB host. Secrets are read from private files, never command arguments."""
import pathlib
import re
import sqlite3
import subprocess
import sys

base = pathlib.Path(sys.argv[1])
adb = pathlib.Path(sys.argv[2])
serial = sys.argv[3]
prefix = [str(adb), "-s", serial]
target = "/data/data/com.gaurav.avnc/databases/main"


def run(*args):
    return subprocess.check_output(prefix + list(args), timeout=40)


run("shell", "am force-stop com.gaurav.avnc")
backup = base / "backup" / "avnc-before-wifi.db"
raw = run("exec-out", "cat " + target + " 2>/dev/null")
if not backup.exists():
    backup.write_bytes(raw)
stage = base / "downloads" / "avnc-wifi.db"
stage.write_bytes(raw)
db = sqlite3.connect(stage)
db.row_factory = sqlite3.Row
profile = dict(db.execute("SELECT * FROM profiles WHERE name=?", ("AvianVisitorsUSB",)).fetchone())
profile.update(name="AvianVisitorsWiFi", host="127.0.0.1", port=5901,
               channelType=24, sshHost="192.168.68.80", sshPort=22,
               sshUsername="frameview", sshAuthType=2,
               sshPassword=(base / "downloads" / "frame-ssh-password.txt").read_text().strip(),
               sshPrivateKey="", gestureStyle="touchscreen", screenOrientation="landscape")
profile.pop("ID")
db.execute("DELETE FROM profiles WHERE name=?", (profile["name"],))
db.execute("INSERT INTO profiles (" + ",".join('"'+k+'"' for k in profile) + ") VALUES (" +
           ",".join("?" for k in profile) + ")", list(profile.values()))
db.commit()
assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
db.close()
uid = re.search(r"userId=(\d+)", run("shell", "dumpsys package com.gaurav.avnc").decode()).group(1)
run("push", str(stage), "/data/local/tmp/avnc-wifi.db")
run("shell", f"cp /data/local/tmp/avnc-wifi.db {target} && chown {uid}:{uid} {target} && chmod 600 {target}")
assert run("exec-out", "cat " + target + " 2>/dev/null") == stage.read_bytes()
run("shell", "rm /data/local/tmp/avnc-wifi.db")

# Wildcard address matching still requires the exact independently fetched Pi
# host key. This lets a DHCP address change without an unattended trust prompt.
keys = base / "downloads" / "pi-public-hostkeys.txt"
known = base / "downloads" / "avnc-known-hosts"
known.write_text("".join("* " + " ".join(line.split()[:2]) + "\n"
                         for line in keys.read_text().splitlines() if line.strip()))
run("push", str(known), "/data/local/tmp/avnc-known-hosts")
directory = "/data/data/com.gaurav.avnc/files"
run("shell", f"mkdir -p {directory} && chown {uid}:{uid} {directory} && chmod 700 {directory} && "
    f"cp /data/local/tmp/avnc-known-hosts {directory}/known-hosts && "
    f"chown {uid}:{uid} {directory}/known-hosts && chmod 600 {directory}/known-hosts")
assert run("exec-out", f"cat {directory}/known-hosts 2>/dev/null") == known.read_bytes()
run("shell", "rm /data/local/tmp/avnc-known-hosts")
stage.unlink()
print("Saved Wi-Fi SSH profile and pinned the Pi host keys; original database backed up privately.")
