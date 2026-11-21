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
- Deployment and browser regression verification in progress.
