# Direct PF1007L USB ADB from the Pi

This wrapper uses the exact known frame serial and the Pi's installed Android
platform tools. It is a local maintenance tool, not a network service:

```sh
avian-frame-adb wait 120
avian-frame-adb status
avian-frame-adb shell getprop sys.boot_completed
```

The Pi has an existing udev rule granting `plugdev` access to the frame's
Allwinner USB interface. The wrapper runs as the normal `david` user, which is
in that group.

The PF1007L has one USB-C port. Since its final configuration is wall-powered,
a direct-Pi USB data connection is not physically available all the time. Do
not replace it with unrestricted Wi-Fi ADB: this frame's ADB shell is root and
unauthenticated. For permanent direct Pi ADB, use a tested USB-C PD/data hub or
dock that supports power pass-through and Android device-mode data; otherwise
use it temporarily as an attended maintenance cable arrangement.

## Restricted temporary Wi-Fi ADB

`avian-frame-network-adb` supports an attended maintenance session on a new
Wi-Fi network. It requires direct USB only while enabling or disabling access:

```sh
avian-frame-network-adb enable
avian-frame-network-adb discover
avian-frame-network-adb connect FRAME_ADDRESS
# perform the needed maintenance
adb disconnect FRAME_ADDRESS:5555
avian-frame-network-adb disable
```

`discover` does not scan the LAN. It returns only addresses that have recently
made an authenticated `frameview` SSH connection to this Pi on `wlan0`; select
that address for `connect`.

The enable step installs a frame-side firewall chain that accepts TCP 5555 only
from the Pi's *current* `wlan0` IPv4 address, rejects every other IPv4 source,
and rejects IPv6. It then starts Android's TCP ADB listener. The rule and
listener are intentionally volatile: repeat this direct-USB enablement after a
frame reboot or when the Pi changes Wi-Fi. Do not make the listener persistent,
allow a subnet, or use a LAN scan—the frame's root ADB has no authentication.

## Verified maintenance session — 2026-11-25

USB ADB through the Windows development host reached the exact frame serial.
The frame initially had no Wi-Fi interface and logged AIC radio power-on
failures. An unmounted SD card also produced separate MMC timeouts. Removing
the SD card and restarting restored Wi-Fi; the exact cause is not established.

Installed the IPv4 Pi-only accept/reject chain and IPv6 rejection before using
`adb tcpip 5555`. The Pi discovered the frame from its authenticated frameview
connection, connected over wireless ADB, and verified the serial. A connection
from the non-Pi operator host was rejected. AVNC was confirmed foreground,
with an active loopback VNC connection on the Pi.

This is a **temporary session**, not persistent remote maintenance. Rebooting
the frame or changing the Pi WLAN address requires attended USB enablement
again. Do not treat temporary ADB as a verified reboot-safe deployment.
