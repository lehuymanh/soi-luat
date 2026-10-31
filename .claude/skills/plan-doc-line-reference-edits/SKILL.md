---
name: plan-doc-line-reference-edits
description: Use when editing a plan doc that other docs cite by line.
category: documentation
---

When a doc is cited by line number from another doc, edit it in place and keep its line count, so the citations stay true.

- Replace text inside existing lines. If a change needs a new line, merge it into a neighbouring line.
- Status marks ("done", the measured result) go into the step's existing heading or first bullet, never as a new line under it. A status line inserted under a plan heading moved the hunk from 6 to 7 lines and broke the citations.
- Check the count before committing: `diff <(git show HEAD:FILE | wc -l) <(wc -l < FILE)` must print nothing.
- Spot-check every cited line with `sed -n 'Np' FILE` against the text the citing doc quotes.
- Where the citing doc records a line that moved, rewrite that record in the citing doc, not by adding lines to the cited one.
