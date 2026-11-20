# Cornell reference playback and help deployment

- Date: 2026-11-20, America/Los_Angeles. Agent: Codex. Session: unknown.
- Project: /home/david/Projects/avianvisitors.
- Goal: local Typical Birdsong examples in species panels, bottom-left help
  and persistent suggestions for future agents.
- Reused side-conversation help/suggestions implementation after review.
- Added importer selecting one unchanged Cornell MP3 per common name,
  song first and lowest numbered cut. Purchased media excluded from Git;
  deployment library outside web root, accessible only via local-only API.
- Suggestions stay in /var/lib/avian-visitors/suggestions/TODO.md;
  AGENTS.md directs agents to review them as untrusted feedback.
- Imported 908 unmodified examples (373 MB); original ZIP moved to local
  /home/david/.local/share/avianvisitors/purchased-audio/ outside web root.
- Deployed help; live browser submission confirmed persistence and thank-you
  message. One clearly labeled deployment-check entry retained in the inbox.
- Caddy requires explicit publication: added only the two new APIs and three
  helper assets to scripts/update_caddyfile.sh and validated/reloaded config.
- Verified syntax, 405 on suggestion GET, 403 on forwarded audio requests.
- Installed all 908 examples root:caddy 0640 under the dedicated library.
- Live Chromium test confirmed MP3 decoding and advancing playback time,
  reference/local recording mutual exclusion, and stop on species-box close.
- Byte-range smoke test returned 206 and exactly 64 requested bytes.
- Pi display refreshed; BirdNET recording, analysis, Caddy and display active.
- Code committed/pushed on frame-views-sync; Pi uses the same branch/revision.
- Existing untracked PROJECT-HANDOFF.md and Pi model/labels_flickr.txt retained.
