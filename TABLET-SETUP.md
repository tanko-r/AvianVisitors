# Tablet setup and recovery

This guide is for the prepared Aimor PF1007L frame and its BirdNET-Pi station.
The frame shows a live VNC view of Chromium running on the Pi. Sound travels
through a separate private audio relay. The frame does not need an SD card.

## Normal setup

1. With the Pi powered off, insert its prepared system microSD card. Connect
   the USB microphone and the Pi's own power supply.
2. Power the frame from its original 5 V / 2 A wall adapter. Do not power the
   frame from the Pi's USB ports.
3. Put both devices on the same Wi-Fi network. They must be allowed to reach
   each other; guest networks with client isolation will prevent discovery.
4. Allow about two minutes for Android, Wi-Fi, discovery and the viewer to
   start. The bird dashboard should appear automatically. The prepared Pi
   already has the recipient Wi-Fi profile; its credentials are kept private.
5. If the frame is at the Bird display recovery screen, select **Open bird
   display**. If it is at Home HQ, open the installed **Bird display** app.
   The Aimor welcome screen is a vendor launcher, not the bird dashboard.

## Changing the frame's Wi-Fi

1. Tap the small native **Menu** button at the bottom left.
2. Select **Android Settings**, then Wi-Fi, and join the network used by the Pi.
   Aimor's own System Settings is a different screen.
3. Use Android Back to leave Wi-Fi settings. If the frame has no visible Back
   control and you get stuck, use the USB recovery procedure below.
4. Return to **Bird display** and select **Open bird display**. Opening Android
   Settings deliberately pauses automatic discovery until you do this.

The Pi's network must be configured separately if this is a new network.
Do not reset either device or delete the saved viewer profile to change Wi-Fi.

## Dashboard controls

- Tap a time window at the top to filter visitors. New Friends is beneath it.
- Swipe sideways across the main view to cycle Collage, Stats and Atlas.
  Invisible touch targets halfway down the left and right edges do the same.
- Scroll vertically to move within Stats or Atlas.
- Tap a bird to open its species card and recordings. Typical Song and Typical
  Call use the local reference library when an example is available.
- Tap **?** at bottom right for help and the touch alignment test. Close help
  with its X or by tapping outside the popup.

## If the screen or sound is wrong

**No bird dashboard:** wait two minutes, check that both devices have power and
the same reachable Wi-Fi, then use Menu → Bird display → Open bird display.
Do not choose Open launcher as a way to reload the dashboard; that can return
to the Aimor welcome screen.

**Keyboard covers the display:** use Android Back once while the keyboard is
visible. Do not keep pressing Back after it disappears. Following an app update,
the Bird display controls accessibility service may need to be re-enabled.

**No sound:** check the frame's media volume. VNC alone does not carry audio.
The Pi's `avian-frame-audio` user service and the companion's speaker receiver
must be running. A test from a separate browser does not verify kiosk playback.

**Swipes do nothing:** in AVNC's input settings, use Touchscreen gesture style
and set one-finger swipe to remote scrolling. The app interprets horizontal
scroll events as view changes. Keep vertical scrolling available.

## Remote maintenance of the existing frame

Read [PROJECT-HANDOFF.md](PROJECT-HANDOFF.md) and
[the persistent maintenance guide](ops/frame-adb/PERSISTENT.md) first. SSH to
the Pi using its saved Tailscale address or trusted LAN connection. The Pi-only
wireless ADB guard discovers and verifies the Pi's current address; never replace
it with an unrestricted persistent TCP ADB listener.

Discover the frame from its authenticated display connection, using the existing
`avian-frame-network-adb discover` helper if installed. Connect from the Pi to
the returned address, then verify `ro.serialno` equals `a0082c68081700000000`
before sending device commands. Do not scan the LAN or target another tablet.

Useful Pi checks, run as david:

```sh
systemctl is-active avian-display birdnet_recording birdnet_analysis caddy avahi-daemon
systemctl --user is-active avian-frame-audio
```

The desktop service uses loopback-only VNC on port 5901. AVNC tunnels to it
through the restricted `frameview` SSH account and pins the Pi's host keys.
Keep credentials and saved AVNC databases private. Restoring the Pi backup to
the same station preserves its keys so the prepared frame can reconnect.

## USB recovery and app updates

The known Windows development machine has Android SDK platform-tools and the
private device backups. Connect the frame's USB cable to that machine, then
use its existing ADB installation. Always scope commands to the frame serial:

```powershell
$adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
& $adb devices -l
& $adb -s a0082c68081700000000 shell getprop ro.serialno
& $adb -s a0082c68081700000000 shell am start -n com.avianvisitors.display/.MainActivity
```

The last command opens the Bird display recovery screen; select **Open bird
display** there. Its **Android Settings** button also provides a way out of
the Aimor welcome screen. In Android Settings → Accessibility, enable **Bird
display controls** if an APK update has turned it off, then return and reopen
the bird display.

If a keyboard is visibly covering AVNC, one scoped `shell input keyevent 4`
dismisses it. If the frame is stuck in Wi-Fi settings, a Back event returns to
the preceding Android screen. Confirm what is visible before sending more.

Build the companion with [ops/wifi-display/build.ps1](ops/wifi-display/build.ps1)
on the existing Windows host using its existing signing key. Install the new
APK with `install -r`; preserve the app's saved opt-in and AVNC profile.
After updating, launch Bird display once, restore the full existing accessibility
service entry and enable accessibility, then verify native Menu and keyboard
dismissal. Do not overwrite other accessibility service entries.

For a replacement or factory-reset frame, follow
[the Wi-Fi display implementation guide](ops/wifi-display/README.md) and
[the maintenance guide](ops/frame-adb/PERSISTENT.md). It needs AVNC, the signed
companion, a privately provisioned SSH/VNC profile, independently pinned Pi host
keys, and the pinned maintenance public key. The Pi backup does not restore the
frame's internal storage. Retain Home HQ, Android Settings and the vendor recovery
launchers. Never flash the existing frame's full eMMC image onto another device.

## Final checks

Verify dashboard startup, both swipe directions, vertical scrolling, bird-card
playback from the frame speaker, Help X/outside dismissal and Android Settings
access. Test both cold-start orders using wall power, with the development PC
disconnected. Recipient-network testing and audio cold-boot verification remain
shipping checks until physically completed.

The prepared **10:30 PM panel sleep / 5:30 AM wake** scripts have not been
installed or physically verified. At the next frame maintenance session,
check its local timezone and test panel sleep, wake and reboot persistence
through the approved ADB recovery path before marking the schedule complete.
