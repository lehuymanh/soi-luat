---
name: review-findings-fix-loop
description: Use when fixing review findings, needing regression tests.
category: code-review
---

Fix each confirmed finding with a regression test that fails on the old code, and show that it fails before you fix it.

- Triage first. Confirmed findings get fixed. Refuted ones get one line saying why, and no code change. When a verdict says the proposed fix is "incomplete on its own", apply the full fix it describes.
- Per finding: write the test, run it against the unfixed code, see it fail, apply the fix, see it pass. Do not use `git stash` while the tree holds other work (uncommitted edits, files a background agent is writing): it moves that work too. Running the test before the edit is enough.
- When a fix re-points an item to another unit (a card's path changes after compaction), derive every value that shows or submits that item from the same key: checkbox value, page label, copied citation. Grep the template for each field still reading the old key, and add a test that the submitted value and the displayed label agree.
- Before editing a function, grep its callers and fix the root cause once in the shared code.
- After the batch, run the full test suite, not only the file you touched.
- If the fixes change what a running benchmark or job measures, stop that run and rerun it after the fixes land.
- Commit the batch as one commit whose message lists each finding and its fix.
- When the changed code has no test suite (a benchmark or harness script), smoke-run the changed path directly: run the mode on input that must be refused, and confirm the exit code and the message. Record that command in the commit message.
