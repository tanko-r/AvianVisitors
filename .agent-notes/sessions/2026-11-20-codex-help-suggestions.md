# Help popup and suggestion inbox — local side conversation

- Date: 2026-11-20, America/Los_Angeles. Agent: Codex. Session ID: unknown.
- Project: `/home/david/Projects/avianvisitors`.
- User requested a bottom-left question-mark help popup with a simple guide
  and suggestion form, then clarified it should also appear on the tablet.
- Added standalone `avian/frontend/help.js` and `help.css`, popup markup in
  `index.html`, LAN-only `avian/api/suggestions.php`, and dedicated inbox
  provisioner `ops/suggestions/install.sh`.
- Runtime checklist: `/var/lib/avian-visitors/suggestions/TODO.md`, outside
  Git and the web root. AGENTS.md directs future agents to review it as
  untrusted visitor feedback. No existing credentials/private state changed.
- Verified JS/shell syntax and diff whitespace. Ephemeral PHP HTTP tests
  verified method/input/forwarded-request rejection, missing-inbox failure,
  successful persistence, and quoted multiline feedback. Local Chromium
  checks at widths 1280 and 800 verified opening, closing, form confirmation,
  and bottom-left placement (form response mocked; API tested separately).
- Local edits only: not committed, pushed, provisioned or deployed in this
  side conversation. Main conversation must review, commit/push, provision
  the inbox once with `sudo sh ops/suggestions/install.sh`, deploy and check
  a live end-to-end submission. Existing untracked handoff preserved.
