# Pi file backup and tablet guide

- Date: 2026-11-26, America/Los_Angeles. Agent: Codex. Session ID unknown.
- Project: /home/david/Projects/avianvisitors, branch frame-views-sync.
- User requested an SD backup here and tablet setup instructions; clarified
  source is the Pi system SD and that a whole-card image is unnecessary.
- Read PROJECT-HANDOFF and persistent maintenance guide. Card mmcblk0 is
  63,281,561,600 bytes, root ext4 plus 512 MiB FAT boot. Local free space ~95 GiB.
- File-based backup chosen: rsync -aHAXSx with numeric ownership, root access,
  excluding virtual mounts, caches, temporary files and /var/swap. Initial sync
  runs while applications are up; final sync will pause application writers.
- Private staging/bundle directory device-backups/pi-20261126, parent0700,
  ignored from Git. No credentials/private state contents printed or committed.
  User explicitly requested the device backup; it necessarily includes its
  private state, with original permissions preserved inside a private bundle.
- Initial Tailscale rsync stopped safely and resumed over known-key LAN SSH
  using HostKeyAlias; previously copied files reused. Source card untouched.
- TABLET-SETUP.md covers prepared-frame startup, Wi-Fi, true VNC/audio path,
  gestures, native Menu, scoped USB recovery, updates, replacement provisioning,
  and still-pending overnight schedule/cold-boot tests. BACKUP-RESTORE.md records
  bundle format, checksum checks and Linux replacement-card restore procedure.
- Backup completion/verification pending. Do not describe as completed yet.
