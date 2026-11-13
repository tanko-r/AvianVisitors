# Pi-rendered USB display

The station has moved to the [Wi-Fi display trial](../wifi-display/README.md).
The USB watcher is disabled and prototype relay units have been stopped.
This document retains the wired experiment and its recovery instructions.

The Pi runs Chromium on a 1280×800 TigerVNC virtual screen. Android runs AVNC
3.3.1 (official release APK, compatible ARMv7/Android 6). ADB reverse carries
tablet localhost:5901 to Pi localhost:5901. The tablet does no website layout.

## Station deployment

- `avian-display.service` starts the private virtual desktop as user `david`.
  Desktop launcher: `~/.local/lib/avianvisitors/start-desktop`.
- VNC listens only on loopback and requires authentication. Credential files
  are private under `~/.config/avian-display` and `~/.local/state/avianvisitors`;
  never put passwords in launch URLs, scripts, or source control.
- `avian-usb-display.service` runs `usb-display.py` as `david`. The private
  `~/.config/avian-display/usb.env` supplies the intended device serial.
- A narrowly scoped udev rule grants `plugdev` access to the frame's Allwinner
  USB interface. The watcher always specifies the configured serial.
- AVNC profile `AvianVisitorsUSB` saves its password. Fullscreen, landscape,
  direct touch, quick taps, and auto-reconnect are configured. Onboarding and
  the virtual keyboard are hidden. A one-finger swipe scrolls the website.
- Home HQ remains the recovery Home app. No vendor app is disabled by this
  display trial. The frame's Wi-Fi remains off.

The watcher waits for Android boot completion, restores the reverse mapping
after USB reconnect/reboot, and launches the saved profile once per connection.
AVNC handles VNC server reconnects. Physical cold-start tests are required.
The watcher also dismisses Android 6's automatically reopened keyboard while
AVNC is the foreground application. It leaves other applications alone.

## Prototype arrangement

Before moving the cable, the frame remains on the Windows PC. Private SSH
forwarding relays Windows loopback:5901 through nanoclaw-box to Pi loopback:5901,
then Windows ADB reverse reaches the tablet. These relay processes are temporary
test dependencies, not the shipping setup. Remove them after direct USB works.
The prototype relay uses transient user services `avian-vnc-test-pi` and
`avian-vnc-test-windows` on nanoclaw-box. Stop both with `systemctl --user stop`
after moving the cable. The Windows `AvianVisitors-USB-Test` scheduled task
also runs this watcher using `AVIAN_ADB_PATH` for the Windows ADB executable.

## Power

Pi 4 USB-A supplies 5 V with a 1.2 A shared peripheral budget; its USB-C connector
is a power input, not a PD output for the frame. The microphone shares that
budget. Verify the frame adapter rating, actual port arrangement, Pi PSU, and
cold-start stability before choosing direct USB power.

If external power is needed, use a designed powered data hub whose downstream
port supports sufficient simultaneous current and data. Charging-only ports
cannot carry ADB. Do not assume a hub's aggregate wattage is its per-data-port
rating. A separate frame DC input, if present, could simplify power wiring.

## Recovery

Stop the two display services to return CPU/RAM to the original listening
station. Launch `com.wesbos.homehq/.MainActivity` over ADB to restore the original
tablet viewer. Existing application data and verified firmware backups remain.

## Verified on the prototype

- The Pi renders the page at 1280×800; a tablet tap switches the page on the Pi.
- The saved AVNC profile reconnects without asking for its password.
- A restarted VNC server recovers; the watcher dismisses Android's reopened IME.
- BirdNET recording/analysis remain active and the Pi reports no throttling.
- Direct Pi USB enumeration, power draw, both cold-start orders, and unattended
  physical power recovery are pending hardware tests. This is not yet a shipping
  configuration.
