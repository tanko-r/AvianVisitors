# Frame fallback rendering and spectrogram compatibility

- Date: 2026-11-21 America/Los_Angeles; agent Codex; session unknown.
- Project: /home/david/Projects/avianvisitors.
- User reported stale physical frame, vendor dashboard menu, then a power
  cycle restoring current UI. Pi still has NO frame SSH/VNC connection after
  that reboot. Thus do not claim live VNC mirroring is restored; the frame
  appears to be using the local recovery dashboard. Exact installed app and
  reason companion is not launching require device access; no ADB target.
- User requested Help bottom right and reported frame-only missing recording
  spectrograms. Moved Help and bumped asset version URLs. Added exact stored
  BirdNET PNG path for Android/performance=lite; desktop keeps WebAudio STFT.
  Guarded AudioContext construction and callback-only decodeAudioData support.
- Verified latest Robin PNG endpoint returns 200/image/png. No device-side
  changes or widened network maintenance access. Screen schedule still pending.
- Deployed and verified in live Chromium: lite profile loads an IMG with
  naturalWidth 940 and hides the loading text; full profile paints a ready
  CANVAS width 472. Help sits 18 px from right and bottom in both profiles.
- Refreshed Pi display; core services active. Still no VNC connection after
  user-reported frame reboot; do not represent browser emulation as a test on
  physical hardware. Frame local dashboard needs Reload dashboard to load
  current assets. Restoring true AVNC mode remains unresolved.
