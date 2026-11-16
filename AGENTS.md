# Agent instructions

Before changing, troubleshooting, deploying, or handing off this project, read
[PROJECT-HANDOFF.md](PROJECT-HANDOFF.md) in full. It is the source of truth for
the Pi, PF1007L frame, private-state locations, recovery paths, verified tests,
and work still required before the gift ships.

Do not print, commit, copy, or broaden access to credentials, device backups,
or private state referenced by that memo. Preserve the existing dirty worktree:
the performance patch and display-operation files are intentional local work.

## Follow-up reminder

Remind David at the next frame maintenance session to deploy and physically
test the 10:30 PM screen-sleep / 5:30 AM wake schedule. The scripts in
`ops/wifi-display/` are prepared but have not been installed or verified on
the frame. Check its local timezone, panel sleep/wake, and reboot persistence
through the approved ADB recovery path before marking this complete.
