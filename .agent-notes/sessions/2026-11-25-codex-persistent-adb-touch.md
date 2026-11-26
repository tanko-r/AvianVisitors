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
- Final guard reboot check after transport fix is in progress. Test UI was
  closed with Escape before reboot so the dashboard can return cleanly.
- Nightly screen schedule remains pending; unrelated private state preserved.
