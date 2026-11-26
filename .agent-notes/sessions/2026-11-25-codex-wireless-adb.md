# Temporary wireless ADB and VNC recovery

- Date: 2026-11-25 America/Los_Angeles; Codex; session ID unknown.
- Project: /home/david/Projects/avianvisitors.
- Resumed user-authorized wireless ADB setup after frame connected to Windows
  development host. Root USB shell verified against the exact project serial.
- Frame was in Android Wi-Fi settings, with no WLAN interface and repeated
  AIC radio power-on errors. Sent Back, opened Bird display. Identified separate
  SD-card MMC timeouts; checked card unmounted before user removed it.
- Rebooted once after card removal. Wi-Fi eventually connected. Cause of the
  earlier failure is not established; do not assert USB power was inadequate.
- Set frame firewall to accept TCP 5555 only from the current Pi WLAN IP,
  reject other IPv4 sources and reject IPv6, then enabled `adb tcpip 5555`.
- Pi discovery from authenticated frameview returned the same frame IP as USB.
  Pi wireless ADB matched serial; foreground AVNC; active loopback VNC sockets.
  Non-Pi operator-host TCP attempt was refused. No credentials read or copied.
- Important: temporary runtime rules/listener, no persistent boot edits. USB
  enablement must be repeated after frame reboot or Pi WLAN address change.
- Daily screen-off/wake schedule remains pending deployment and physical test.
- Updated ops/frame-adb/README.md; preserved untracked handoff and Pi data.
