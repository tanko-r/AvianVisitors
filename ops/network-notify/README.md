# Wi-Fi join notification

`avian-network-notify.py` is deployed to the Pi and invoked by NetworkManager
when `wlan0` comes up or gets a DHCP address. It sends a single WhatsApp
self-message only when the SSID is different from the last successfully
notified SSID. The message includes the SSID, LAN IP, Tailscale IP, and a
ready-to-copy SSH command.

It sends through the existing WhatsApp bridge on nanoclaw-box over Tailscale:
`http://100.89.131.81:3011/send`. WAHA's API stays localhost-only on
nanoclaw-box. The bridge token and WhatsApp self-chat ID are stored only in
`/etc/avianvisitors/network-notify.env` on the Pi, mode 0600, and must never be
committed or printed.

State is `/var/lib/avianvisitors/network-notify.json`, mode 0600. Removing that
file causes the next successful Wi-Fi association to notify again.

The dispatcher runs the worker in a transient systemd unit so it does not block
NetworkManager. Failed sends do not update state; a later Wi-Fi event retries.
There is deliberately no tight retry loop, both to avoid duplicate alerts and
to keep WhatsApp traffic low.

## Operator computer access note

On the operator computer, `update-access-details.py` polls the Pi over SSH and
writes the ignored, mode-0600 `REMOTE-ACCESS.txt` in the checkout. It records
the Wi-Fi LAN IP, Tailscale IP, SSH commands, and last successful check time.
When the Pi is unreachable the last successful note is retained. A user
systemd timer on that computer runs it every two minutes; the computer must be
on and connected to Tailscale. This is separate from the WhatsApp notifier.

## Frame ADB from the Pi

The Pi already has Android platform tools, the exact PF1007L serial, and a
`plugdev` udev rule prepared. Use direct USB ADB only when the frame is attached
as a USB device to the Pi:

```sh
adb devices -l
adb -s a0082c68081700000000 shell getprop sys.boot_completed
```

The frame has one USB-C port and uses it for wall power. A normal direct USB
connection to the Pi conflicts with that wall-power arrangement and the Pi USB
port should not be assumed to supply adequate display power. For unattended
Wi-Fi operation no USB cable is needed. A permanent direct-Pi ADB maintenance
connection requires a tested USB-C data hub/dock with PD pass-through, or a
deliberate temporary maintenance wiring procedure. Never enable root ADB over
Wi-Fi as a substitute.
