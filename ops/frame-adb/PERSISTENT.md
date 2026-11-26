# Persistent, pinned-Pi wireless maintenance

The user explicitly requested reboot-safe wireless maintenance on 2026-11-25.
This replaces the USB-only re-enablement requirement for the new boot guard;
the older `avian-frame-network-adb enable` wrapper remains a temporary tool.

The frame boot hook launches `frame-maintenance-boot.sh` before the display
helper. It installs IPv4 deny rules and an IPv6 rejection **before** starting
TCP ADB. `persist.adb.tcp.port` remains -1: Android must never start an
unguarded TCP listener by itself. The root Java guard grants only one verified
Pi IPv4 address. It discovers candidates from SSH sockets and a DNS-SD query
for the exact service instance; neither is trusted without a fresh signature.

The Pi's local-only `frame-maintenance.php` signs a fresh 128-bit nonce and
its WLAN destination address using a dedicated RSA key. The frame pins only
the public key. A new candidate must return a valid SHA256/RSA signature
covering the exact nonce, protocol prefix and candidate address. Responses are
bounded, timed out, and never followed to another URL. Failed verification
revokes access; the guard retries after five seconds. The shell supervisor
reinstalls deny rules and restarts the guard if Java exits. Discovery works
without requiring the AVNC window to stay open. No Internet ADB exposure.

## Files

- Pi private key: `/etc/avian-frame-maintenance/signing.pem`, root:caddy 0640,
  dedicated directory root:caddy 0750. Never print/copy/commit the private key.
- Frame public key: `/system/etc/frame-maintenance.pub`, root:root 0644 (PEM).
- Frame guard: `/system/bin/frame-maintenance.jar`, root:root 0644, compiled
  using `build-guard.ps1` (SDK 36 tools, min Android API 23).
- Boot helper and modified boot hook: root:root 0755 under `/system/bin/`.
- Original hook backup: `/data/local/frame-maintenance-backup-20261125/`,
  root-only. Keep the original deferred-Wi-Fi, clock and MAC hooks intact.

Provision a new RSA 2048 key with openssl on the Pi; derive only the public
PEM for the frame. Never reuse the SSH, VNC or notification secrets. Publish
the reviewed API through `scripts/update_caddyfile.sh`. Build the guard on
the Windows development host and push through serial-scoped USB ADB. Back up
the existing hook privately before replacing it. Remount `/system` read-only
after installing and verify a reboot while USB recovery is available.

## Verification and recovery

Verify Pi wireless ADB serial, non-Pi rejection, live AVNC, and automatic
recovery after a frame reboot. Exercise address discovery with a conflict-
checked temporary Pi WLAN address while retaining the primary address; never
take down the working SSH/network configuration just to simulate DHCP.

If the proof endpoint/key is unavailable, ADB is blocked rather than exposed.
Use USB recovery, inspect `/data/local/tmp/frame-maintenance.log` and Android
log tag `frame-maintenance`, and confirm key pairing and API reachability.
To roll back, restore the exact original hook from the private on-device
backup and disable TCP ADB over USB, then reboot. Do not disable the firewall
while the TCP listener is running. Do not change the original private-state
directory permissions to make the new signing key readable.
