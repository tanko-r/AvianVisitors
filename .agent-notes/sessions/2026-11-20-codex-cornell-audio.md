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

## Song/call follow-up and tailnet fix

- User requested separate song/call examples and classification per local
  recording, then reported all examples unavailable.
- Reproduced a 403 from direct Tailscale access while loopback worked. Added
  an audio-endpoint-only direct tailnet gate with address/host checks and
  rejection of extra forwarding headers; unchanged global admin gates.
- Reimported 908 species: 549 song, 890 call, 132 other examples. Mixed and
  mechanical tracks are never mislabeled as pure song/call. Files verified.
- Species API now explicitly reports null vocalization_type/unclassified;
  UI shows that status per recording. Automatic inference is NOT installed.
  Discovered EMSN-Nijverdal/emsn-vocalization targets 232 Dutch species and
  is not validated for Oregon. Further model evaluation/training remains.
- Separate library installed and verified: direct Tailscale song and call
  requests return 206 for byte ranges. Live Chromium at 100.88.155.15 played
  both American Robin examples with advancing audio time and showed local
  recording status as Song/call: unclassified. Forwarded header rejected 403.
- Display refreshed; existing midnight-reset tests passed, core services active.

## Cloudflare follow-up

- User clarified access is via Cloudflare, not Tailscale. Reproduced 403 at
  birdnet.rigid-dreamy-sweep.us. Public/proxied reference audio now requires
  the existing menu admin session instead of rejecting every proxy request.
  Purchased media remains unavailable anonymously; no new auth secrets.
- Song/call buttons grouped in one non-wrapping flex row; version URLs bumped.
- A 401 explains remote unlock and opens the existing menu after dismissing
  the species dialog; successful menu unlock refreshes reference availability.
- Verified real Cloudflare HTTPS login, metadata, and song/call byte ranges
  (206 / 64 bytes). Logout returns 401. Test session cookies stayed in memory;
  credentials were neither printed nor copied. Initial Python default UA was
  rejected by Cloudflare; a browser UA passed. No access policy weakened.
- Live Cloudflare browser checks at 1280 and 390 px confirmed same-row,
  non-overlapping buttons, accurate unlock guidance, and visible login after
  tapping a reference button while signed out. Pi refreshed and synced.
