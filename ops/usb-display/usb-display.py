#!/usr/bin/env python3
"""Reconnect the one configured Android frame to a private local VNC display."""
import logging
import os
import re
import socket
import subprocess
import time

SERIAL = os.environ.get("AVIAN_FRAME_SERIAL", "")
PORT = 5901
URI = "vnc://127.0.0.1:5901?ConnectionName=AvianVisitorsUSB"
ADB = os.environ.get("AVIAN_ADB_PATH", "/usr/bin/adb")


def adb(*args):
    return subprocess.run(
        [ADB, "-s", SERIAL, *args],
        capture_output=True, text=True, timeout=15,
    )


def display_ready():
    try:
        with socket.create_connection(("127.0.0.1", PORT), timeout=2) as conn:
            return conn.recv(12).startswith(b"RFB ")
    except OSError:
        return False


def hide_viewer_keyboard():
    # Android 6 may reopen its IME when AVNC reconnects and focuses its input
    # view. Dismiss only a visible keyboard belonging to the foreground viewer;
    # leave Settings and recovery applications alone.
    window = adb("shell", "dumpsys window windows").stdout
    focus = re.search(r"mCurrentFocus=.*", window)
    if not focus or "com.gaurav.avnc.ui.vnc.VncActivity" not in focus.group():
        return
    ime = adb("shell", "dumpsys input_method").stdout
    if re.search(r"\bmInputShown=true\b", ime):
        adb("shell", "input keyevent 4")


def main():
    if not SERIAL or not SERIAL.isalnum():
        raise SystemExit("Configure AVIAN_FRAME_SERIAL for the intended USB frame")
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    boot = None
    launched = False
    waiting = False
    while True:
        try:
            state = adb("get-state")
            if state.returncode or state.stdout.strip() != "device":
                if not waiting:
                    logging.info("Waiting for the configured USB frame")
                waiting, launched, boot = True, False, None
                time.sleep(3)
                continue
            waiting = False
            # USB enumeration can precede Android's package-manager readiness.
            if adb("shell", "getprop sys.boot_completed").stdout.strip() != "1":
                time.sleep(3)
                continue
            current = adb("shell", "cat /proc/sys/kernel/random/boot_id").stdout.strip()
            if not current:
                time.sleep(3)
                continue
            if current != boot:
                boot, launched = current, False
            mappings = adb("reverse", "--list")
            if f"tcp:{PORT} tcp:{PORT}" not in mappings.stdout:
                result = adb("reverse", f"tcp:{PORT}", f"tcp:{PORT}")
                if result.returncode:
                    logging.warning("USB tunnel unavailable; retrying")
                    time.sleep(3)
                    continue
                launched = False
                logging.info("Private USB display tunnel restored")
            if not launched and display_ready():
                # The saved AVNC profile owns its password; never put credentials in intents.
                result = adb("shell", "am start -a android.intent.action.VIEW "
                             f"-d '{URI}' -p com.gaurav.avnc")
                if not result.returncode and "Error:" not in result.stdout:
                    launched = True
                    logging.info("Saved VNC viewer launched")
                else:
                    logging.warning("Viewer unavailable; retrying")
            if launched:
                hide_viewer_keyboard()
        except (OSError, subprocess.TimeoutExpired):
            logging.warning("USB temporarily unavailable; retrying")
            launched = False
        time.sleep(3)


if __name__ == "__main__":
    main()
