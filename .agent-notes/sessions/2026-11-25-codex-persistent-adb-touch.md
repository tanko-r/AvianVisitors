# Persistent ADB, VNC view switching and touch/contrast work

- Date: 2026-11-25 America/Los_Angeles; agent Codex; session unknown.
- Project /home/david/Projects/avianvisitors. User explicitly required persistent
  wireless ADB, smoother view switches, a touch test and stronger contrast.
  Later corrected palette preference to original warm gray-beige, only darker.
- Implemented root Java MaintenanceGuard (app_process), deny-first shell boot
  guard, dedicated Pi SHA256/RSA signed nonce endpoint, pinned public key.
  Private signing key stays /etc/avian-frame-maintenance/signing.pem root:caddy
  0640; directory 0750. Original private-state permissions untouched. Public
  PEM on frame /system/etc/frame-maintenance.pub. Built using Windows Android
  SDK/JDK, installed root-owned guard JAR and boot scripts; /system read-only.
- On-device original hook backup is root-only under
  /data/local/frame-maintenance-backup-20261125/. Existing deferred Wi-Fi,
  time sync, MAC repair, recovery launchers and display hook preserved.
- Verified guard recovery after frame reboot; exact serial over Pi ADB and
  live AVNC/VNC confirmed. Signed proof tamper test rejects modified payload.
- Address-change test: conflict-checked temporary Pi .250 address; blocked
  proof on normal .69; guard revoked .69 and discovered/verified .250. ADB
  worked with .250 source route. On return to .69 Android retained a stale
  TCP ADB transport. Added adbd restart on a newly authorized address; rebuilt
  and installed final JAR, restarted guard via its boot supervisor. Repeated
  the test: ADB worked through .250 and automatically recovered through .69.
  Both temporary alias/source route and test firewall rule removed. Non-Pi
  host rejected; no persistent unguarded TCP property (persist port stays -1).
- Frame-lite UI now uses only one visible view, no horizontal translated
  strip; warm Stats is reused until data changes. Initial Pi browser handlers
  were ~20–130 ms, supporting a display-path contribution to perceived lag.
  AVNC profile checked selectively: raw encoding OFF, quality 5, zoom 1:1,
  touchscreen gesture mode; credentials neither read nor copied.
- Help touch alignment test provides five targets, average X/Y offset and max
  miss; does NOT silently alter calibration. Synthetic browser samples tested.
  Actual frame screenshot confirms 1280x800, correct new UI and warm track.
- User reported guide X unresponsive, requested outside-tap dismissal. Closed
  it via Pi Escape, added outside-click dismissal and sticky 48px close target,
  explicitly focuses close and resets scroll position on opening. Deployed.
- Current source on frame-views-sync includes commits 3e8f090, 01fadf3,
  197e2a0, 6e5a701, 8f3153d. AGENTS and untracked PROJECT-HANDOFF updated.
- Actual Android-injected touches through AVNC→Pi completed the five-target
  test: mean offset ~0 px, largest miss 0.4 px. This validates coordinate
  mapping, NOT the physical digitizer/finger calibration. User finger samples
  remain needed. Help X and outside dismissal are implemented; an automated
  corner-pixel dismissal probe was inconclusive (open sample equaled baseline),
  so do not claim that probe as evidence of successful physical dismissal.
- User accepted the softened palette. Final code includes sticky 48px guide
  close target, outside dismissal, scroll reset, and larger view buttons.
- Final guard reboot check passed after waiting for Android boot completion
  and retrying fail-closed initialization. Pi wireless serial verified, guard
  process running, only Pi source allowed, /system read-only, AVNC foreground.
- Nightly screen schedule remains pending; unrelated private state preserved.

## Swipe navigation, species contrast and frame speaker (same session)

- User requested horizontal swipes, large far-left/right navigation targets,
  short lightweight animation and stronger species-card control contrast.
  Implemented cyclic edge navigation and horizontal swipe recognition excluding
  interactive controls/open dialogs/species boxes. Frame animates only arriving
  pane by 14px for 140ms; reduced-motion honored, rapid switches cancel animation.
  Species controls match accepted warm #c9c2b6 palette, white active states;
  recording play targets now 44px with matching enlarged control rows.
- VNC did not carry sound. Added companion loopback-only FrameAudio receiver
  and Pi private playback sink/PCM relay via serial-verified Pi-only ADB forward.
  No microphone capture or new LAN audio listener. Built/installed signed APK
  on Windows; enabled Pi user audio service and user lingering. Browser startup
  selects private playback sink for future launches; existing playback rerouted.
- Browser checks passed six edge switches (exactly one pane visible), horizontal
  swipe, blocking view changes while species modal open, help X and outside
  dismissal. Reference audio played with advancing currentTime. Frame showed
  active native AudioTrack; Pi forward bound127.0.0.1 only.
- User initially heard sound and approved species colors, then requested another
  sound test after clearing keyboard. APK update reset accessibility_enabled=0;
  restored1, then one Back dismissed IME and supplied AVNC window event. Verified
  mInputShown=false, AVNC foreground, native Menu accessibility overlay present.
  Awaiting second listening confirmation; do not claim physical audio retest done.
- User's second listening test was silent. Diagnostic browser used the user
  PulseAudio session while the actual kiosk used a separate session. Installed
  the updated startup script (explicit PULSE_SERVER and PULSE_SINK), restarted
  kiosk and audio relay; live VNC reconnected and IME remained hidden. Asked
  user to repeat listening with actual kiosk; awaiting confirmation. Closed
  diagnostic headless browser to prevent its playback confusing physical tests.
- Subscription routing ignores client connect/disconnect events from its own
  pactl queries to avoid a feedback loop. New sink-input events wake routing
  immediately; periodic checks retain bounded recovery.
- New audio path not yet cold-boot tested. Earlier persistent maintenance reboot
  and Pi-address-change tests are separate; do not conflate them.
- Final actual-kiosk verification: injected frame tap opened American Robin
  and played Typical Song. Its Chromium sink-input was routed to avian_frame;
  monitored sample peak13556 (nonzero). User subsequently confirmed “Yes, it
  plays.” Keyboard hidden, native Menu available. Species colors approved.
  Help X/outside, swipe/modal exclusions, six consecutive edge switches and
  one-visible-pane behavior passed browser checks. Final work committed/pushed
  on frame-views-sync and Pi pulled forward; untracked handoff preserved.
