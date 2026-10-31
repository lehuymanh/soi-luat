---
name: html-mockup-visual-check
description: Use when checking an HTML UI mockup or a locally served web page in Playwright.
category: frontend-design
---

A static HTML mockup is verified by rendering it, not by reading its code: run `scripts/shoot.js` on the file, then open every PNG with Read before claiming it looks right.
- When the user says the current UI is unusable, rebuild the mockup from scratch with the taste-skill design rules instead of patching the old file, then verify the new file with this check.
- A mockup may draw only what the approved plan builds. Every label, state, pill, or promise on screen must map to a plan task. Remove the rest before the user reviews it: a promised feature the plan does not build makes the approval meaningless.

- Add `[hidden] { display: none !important; }` once to the stylesheet. A class rule such as `.overlay { display: flex }` overrides the browser's `[hidden]` default, so a closed dialog stays on top of the page.
- Run `NODE_PATH=$(npm root -g) node scripts/shoot.js <file.html> <outdir>`. It renders 1440, 1100, 768 and 390 px, light and dark, and prints `overflowX` (must be 0), the `h1` count, and any page or console error. Exit code 1 means something needs a look.
- Playwright may be installed only for Node. Check it first with `NODE_PATH=$(npm root -g) node -e "require('playwright')"`. Do not write a Python Playwright script until `python3 -c "import playwright"` passes, because the Python import can fail while Node works.
- The script captures only the default state. For each other state (open reader, overlay, empty result, error), copy the script and add a `page.click(...)` before the screenshot.
- A click timeout whose log says `<div class="scrim"> intercepts pointer events` means an overlay from the previous step is still open, not that the selector is wrong. Close it through the real UI (Esc or its close button) before the next click. Do not wrap clicks in `.catch(() => {})` to skip past them: that hid a second click on an already-deleted row and cost a full timeout run.
- If the project's design-check script (for example taste-skill's) is blocked by the run guard because it is downloaded code, do not bypass the guard. Use this check, read the code against the design rules, and state in the report that the official script was not run.
- Report a visual finding only with evidence: the selector or line, the screenshot name, or a measured number. Drop aesthetic opinions with no trace. Before fixing, have a second pass try to refute each finding.
- A mockup that clips a field to "…" at a narrow width can hide approved content (a date, a file name, an effective-from line). Before copying a clipped row into the app, check the screenshot for lost content, wrap the text if content would be lost, and report the deviation from the mockup.

- A served app page (uvicorn or FastAPI on 127.0.0.1) gets the same check. Start it on a throwaway data dir, open it in Playwright, and record `console` errors, `pageerror`s, and any request whose host is not 127.0.0.1. Then drive one real action, such as sending a question or clicking a button that posts. When starting the server, write `$!` to a pid file and later kill that PID. A `pgrep -f`/`pkill -f` pattern matches any process whose command line contains the port string, including the shell running the command when that same line also starts the server or names the port, so it can kill itself. A 403 that the test provoked on purpose is expected; say so in the report.

- A panel that opens beside the content (a reader, drawer or side column) needs three captures: open at desktop width (a third column), at 1100 px, and at 390 px where it becomes an overlay with a scrim. Then press Esc and confirm focus returns to the trigger.

Reference: `scripts/shoot.js`
