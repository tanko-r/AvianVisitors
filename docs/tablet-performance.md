# PF1007L lightweight display profile

The Android 6 AEEZO frame uses a lightweight frontend profile automatically.
Other browsers retain the regular presentation. `?performance=lite` opts in;
`?performance=full` opts out for comparison.

The profile:

- Removes SVG ink filters, blurred shadows, backdrop filters, and transitions.
- Skips entrance animations and defaults Atlas to its existing classic cards.
  An explicitly selected Atlas style still takes precedence.
- Defers hidden collage/Atlas/statistics rendering until that page is opened.
- Avoids rendering the collage twice during a single refresh.
- Reuses collage positions when the species, viewport, label setting, bundle,
  scope, and time window are unchanged and normalized weights have moved less
  than 2.5 percentage points since packing. Exact counts and tooltips still
  refresh. New species and meaningful distribution changes trigger packing.

The original packing algorithm is retained. A coarser packing experiment was
rejected after an unacceptable stall. Initial loading, a new species, or a
changed time window can still require noticeable layout work on this hardware.

Verification uses the actual frame, WebView 106, native screenshot/graphics
diagnostics, and DevTools responsiveness measurements. It does not rely on the
desktop browser as a proxy for tablet performance. The populated collage was
checked with all 23 tiles visible; view switching and routine refreshes were
exercised. JavaScript syntax is checked with `node --check`.

Deployment is a local change to `avian/frontend/apt.js` on the station. Preserve
or reapply it when updating upstream; the project's updater can refuse tracked
local changes. The station's original file is saved privately at
`~/.local/state/avianvisitors/apt.js.before-tablet-performance` for rollback.
Temporary WebView debugging and its ADB forwarding are removed after testing.
