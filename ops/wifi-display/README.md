# Pi-rendered display over Wi-Fi — trial

Android runs AVNC 3.3.1; the Pi still runs the same loopback-only TigerVNC /
Chromium desktop documented in `../usb-display`. USB power/data is unnecessary
after Wi-Fi works; the frame uses its original wall adapter.

## Components

The app accepts horizontal wheel bursts as view swipes because AVNC touchscreen
mode forwards its configured `gesture_swipe1=remote-scroll` this way. Pointer-only
swipe tests do not exercise the frame path. Keep vertical scrolling enabled;
one horizontal burst advances one view. Side navigation targets are invisible
but tappable halfway down either edge. Android-injected left/right swipes and
edge taps were verified through the live frame on 2026-11-25.

- `com.avianvisitors.display` (Bird display), min SDK 23 / target 28, is an
  opt-in companion. It retains Home HQ as Android Home and leaves the vendor
  launcher unchanged. Build on the Windows development host with `build.ps1`
  using Android Studio's JDK, platform 36 and build-tools 36.1.0.
- Open the companion once and select **Open bird display** to enable it.
  On this frame the ordinary boot receiver did not start the service in a reboot
  test. `frame-bird-display.sh` is invoked by the existing system boot hook;
  after boot completion and vendor initialization it starts the native activity,
  restores the navigation accessibility service, then requests automatic display
  startup. The helper's saved opt-in is checked before doing this.
  **Android Settings** and **Home HQ** explicitly pause discovery until the
  owner selects Open bird display again. Installation alone enables nothing.
- The system boot hook also starts `frame-display-schedule.sh`.  It sends the
  Android panel an explicit sleep event at 22:30 and wake event at 05:30 every
  day, using the frame's local clock.  Android, Wi-Fi, AVNC and the Pi's bird
  analysis remain running overnight.  Both helper scripts must be installed at
  `/system/bin/` with owner `root:root` and mode `0755`, then `/system` must be
  remounted read-only again.  Test the two key events manually before relying
  on the schedule: `input keyevent 223` (sleep) and `input keyevent 224` (wake).
- The foreground service discovers exactly `AvianVisitors-Dad-491`,
  `_http._tcp`. This vendor Android 6 build returns zero TXT attributes, so
  discovery requires the exact service instance name and the subsequent SSH
  connection requires the independently pinned Pi key. It reuses the reviewed
  Home HQ discovery state machine: serial resolution, bounded retries, network
  changes, periodic address checks and stale-callback rejection.
- A discovery result launches saved AVNC profile `AvianVisitorsWiFi`, updating
  its SSH host to the discovered address. No credential is put in an intent.
  `SaveConnection=true` matters: AVNC launches stored profiles by database ID,
  so URI overrides must be saved before the viewer reloads that ID.
- AVNC's built-in SSH tunnel connects as `frameview`. The Pi account has a
  generated private password, no usable shell, and forwarding limited to
  `127.0.0.1:5901`. `/etc/ssh/sshd_config.d/00-avian-frame.conf` configures it.
  Admin SSH remains separate. VNC never needs to listen on the LAN.
- AVNC's private `files/known-hosts` pins the Pi's independently retrieved SSH
  host keys. The address pattern is `*`, allowing DHCP changes while still
  requiring an exact Pi key. An unrelated key is not automatically trusted.
- The optional `ViewerNavigation` accessibility service supplies a native Menu
  overlay in AVNC and dismisses Android 6's automatically reopened keyboard.
  Settings and other apps retain normal keyboard behavior. Enable the **full**
  component name `com.avianvisitors.display/com.avianvisitors.display.ViewerNavigation`
  in `enabled_accessibility_services`, preserving other enabled entries, and set
  `accessibility_enabled=1` **after launching the updated helper once**.
  It subscribes to window-change events to keep Android's window cache current.
  Recheck after APK updates. UIAutomator temporarily
  suppresses accessibility services; use plain screencap for verification.

`provision-profile.py` runs on the private ADB host, reads the dedicated SSH
password from a file, backs up AVNC's stopped database, creates the Wi-Fi profile,
checks database integrity/readback, and installs the pinned host keys. Its
initial host is this test Pi's address; discovery replaces that at launch.
Database backups and all credentials belong outside this repository.

## Verification so far

- APK compiled and installed on the PF1007L; existing Home HQ retained.
- The reused discovery harness passed 56 checks against host fakes.
- Real AVNC connected through SSH, with saved credentials and pinned Pi keys.
- Live NSD resolved the Pi over Wi-Fi. Pi SSH logs confirm a connection from
  frame LAN address 192.168.68.59, with USB display reverse mappings removed.
- All three nanoclaw-box prototype SSH relay units stopped. The Pi USB display
  watcher is now disabled; only the virtual desktop remains enabled.
- The dedicated account allows the display forward, refuses other ports,
  and refuses shell commands.
- Native Menu overlay observed. The keyboard workaround checks actual visible
  input-method windows, checks the active app, and debounces duplicate events;
  a VNC-server restart recovered without closing the viewer.
- Wi-Fi recovered automatically after a normal frame reboot and after an
  explicit disable/enable test. Clock synchronization also returned after reboot.
- Final APK reboot test passed with the boot hook: Wi-Fi returned, live discovery
  opened AVNC, the native Menu appeared, and the keyboard was hidden. The installed
  APK was read back byte-for-byte and matched SHA-256
  `11abde9d912805eb876dcdb44ede73e713a53e83753a3906f8df8630558e2bb3`.
- The factory Wi-Fi configuration was privately backed up. Test network Biznet
  and recipient RubenNET were added using WPA2 PSKs derived privately from the
  Pi's saved connections; no plaintext password is in this source tree.
- Only com.yhk.qeota was disabled before enabling Wi-Fi. AiMOR, DeviceTest,
  Rootless and Home HQ remain available. Removing frame-nowifi enables the
  existing deferred-Wi-Fi boot script. Network ADB remains disabled.
- Home HQ fallback now also discovers the named Pi, replacing the Windows
  loopback web-proxy dependency. Its optional TXT constraint is unset.

The owner authorized the Wi-Fi trial before the physical Settings check was
completed. The earlier blanket offline gate was narrowed for this trial: only
the updater was disabled, preserving all recovery launchers and USB access.
Physical Settings confirmation is still required before final launcher lockdown.

## Remaining deployment checks

### Speaker relay added 2026-11-25

VNC carries the picture and input, not audio. `FrameAudio` in the companion
accepts 22050 Hz mono signed 16-bit little-endian PCM on **127.0.0.1:8766 only**.
The Pi user service `avian-frame-audio.service` creates a separate PulseAudio
playback sink and moves Chromium playback into it. `frame-audio-relay.py`
captures that sink's monitor (never the microphone), and sends it through a
Pi-loopback ADB forward on 18766 to the frame. It checks the exact frame serial
before forwarding; address candidates come from current inbound SSH sessions
and must route over wlan0. No audio listener is exposed to the LAN.

This requires the persistent Pi-only ADB guard in `../frame-adb/PERSISTENT.md`.
Install the rebuilt companion with the existing Windows signing key. After an
APK update, restore the existing accessibility-service entry and set
`accessibility_enabled=1`; verify the native Menu and hidden keyboard. The
vendor can reset this flag on update. A visible keyboard may need one Back
event to generate the AVNC window event after rebinding the service.

Install the audio unit under `/home/david/.config/systemd/user/`, enable user
lingering, and enable/start `avian-frame-audio.service` as david. The updated
`../usb-display/start-desktop` explicitly selects the private PulseAudio socket
and frame sink for future kiosk launches; install it to the existing private
desktop-start path. The relay also routes already-running Chromium streams.
It retries after connection loss, frame restart, or the guarded ADB transport
restart. Music volume remains the frame's normal media volume.

Verified: APK build/install, active frame AudioTrack and loopback-only forward,
reference audio progressing in Chromium. The first actual-kiosk retest was
silent because it used a separate PulseAudio session; installed the startup
script with explicit PULSE_SERVER/PULSE_SINK and restarted the kiosk. Actual
frame-injected playback then produced nonzero samples in the private sink,
and the user confirmed “Yes, it plays.” Full cold-boot ordering with this new audio service
is still a shipping check. To roll back audio, stop/disable its Pi user unit;
remove the PULSE_SINK line from the kiosk startup if returning to a Pi speaker.
No Wi-Fi, VNC credentials, microphone configuration or capture jobs are changed.

1. Owner physically opens Android Settings by touch; final gift lockdown is
   not configured by this trial. Native Menu is deliberately available.
2. Confirm real wall-adapter cold starts with the PC unplugged, both Pi/frame
   boot orders, Wi-Fi/router restart, and changed Pi DHCP address.
3. Recipient profile is provisioned, not physically tested on RubenNET. Test
   the recipient SSID/password on an isolated AP and check peer/multicast access.
4. Confirm recipient location, secure remote frame maintenance, Pi Tailscale
   expiry policy, and create/test the spare Pi microSD before shipping.

## Temporary bridge / rollback

The offline crypto test used Windows ADB reverse tcp:2222 and a nanoclaw-box
SSH relay to Pi SSH. These display mappings and all relay units have now been
removed/stopped. The saved Wi-Fi profile is updated by live discovery to the
Pi LAN address on port22. Windows AvianVisitors-USB-Test still keeps USB ADB
alive and provides the old web-proxy fallback for development, but the running
Wi-Fi viewer and Home HQ discovery do not use it. Remove this scheduled task
when device development is finished.

To roll back, pause the companion, disable its accessibility entry, stop its
service, and open Home HQ. Uninstalling the companion leaves AVNC, Home HQ,
backups, firmware and Wi-Fi settings intact. Re-enable the updater with
pm enable com.yhk.qeota only if reverting the appliance setup. Original private
Wi-Fi configuration: Windows backup/wpa_supplicant-before-wifi-trial.conf.
Re-create frame-nowifi and disable Wi-Fi to restore the offline development mode.
