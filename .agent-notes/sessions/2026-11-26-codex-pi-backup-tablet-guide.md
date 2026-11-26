# Pi backup and tablet guide — completed

- Date: 2026-11-26, America/Los_Angeles. Agent: Codex. Session ID unknown.
- Project: /home/david/Projects/avianvisitors, branch frame-views-sync.
- User requested an SD backup here and tablet setup instructions, confirmed
  the Pi system card, then clarified a whole-card image was unnecessary.
- Verified private file-based backup completed06:04 PST under
  device-backups/pi-20261126/ on the development computer. Parent0700,
  archive/metadata0600, excluded from Git. Private capture logs/helper scripts
  are in capture-logs. Temporary rootfs staging removed only after verification.
  Never deploy this bundle into a web root, publish it or commit it.
- Captures system files, all historical recordings, reference library, detection
  database, configuration/private state,946-package inventory, enabled services,
  partition layout and original FAT boot partition, retaining numeric ownership,
  ACLs and xattrs. Virtual mounts, temporary files, common caches, swap and Git
  reflog cache omitted. User explicitly authorized the device backup; original
  private-state permissions preserved and credential contents never printed.
- All eight source Git refs and their reachable objects verified locally; one
  missing source-only tip fetched without creating a public ref. Local objects
  and tracked files seeded to avoid retransferring history; rsync reconciled
  source/device-only files. Git connectivity check passed.
- Boot partition captured read-only then returned read-write. Package inventory
  compared unchanged afterward. Initial live rsync returned24 for transient
  files; subsequent live refresh and quiesced final sync returned0. No raw
  writes or restore operation performed on the source card.
- Application units paused05:58:19, final sync finished05:58:35, all restored
  05:58:39 (about20 seconds).15-minute recovery watchdog arranged before pause,
  disabled after restart. SSH/network/discovery remained available.
- Snapshot revision a804697. pi-rootfs.tar.zst is6,563,944,645 bytes. Compressed
  boot partition and SHA256SUMS accompany it. manifest.json status complete.
- Passed detection SQLite quick_check, Git connectivity, boot size/signature/
  gzip integrity, zstd integrity, tar header scan, restoration of five critical
  files with exact bytes/UID/GID/modes/xattrs comparison and archive checksums.
  Sample selector initially lacked root access; corrected without loosening
  permissions or repeating the device pause. Verification continuation context
  repaired; completion succeeded. Detailed reports remain private.
- All originally active application units/user audio service running afterward;
  VNC reconnected, Pi-only ADB serial matched and frame keyboard hidden. Pi-only
  model/labels_flickr.txt preserved. Development checkout is the only worktree.
- Added TABLET-SETUP.md (startup, Wi-Fi, native Menu/USB recovery, gestures/audio,
  updates/replacement provisioning) and BACKUP-RESTORE.md (bundle checks and
  Linux replacement-card restoration). Guides included in backup. Documentation
  committed/pushed and Pi synced; untracked user-owned handoff preserved.
- Physical spare-card restoration/boot test remains outstanding. Archive checks
  do not satisfy that shipping check. Tablet cold-start/audio checks and the
  undeployed10:30 PM/5:30 AM panel schedule remain pending as documented.
