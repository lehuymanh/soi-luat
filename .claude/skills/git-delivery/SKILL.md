---
name: git-delivery
description: Use when ending a turn after repo edits, or before any git commit, git push, or Co-Authored-By trailer.
category: git-workflow
---

Every repo edit is committed and pushed before the turn ends or a status message goes out.

- After the last edit, run `git status --short`. If anything shows, commit and push it before replying.
- Before starting a long background job (a benchmark, an export), commit and push the code it runs. A container restart kills every process, and the pushed commit is also the hash the results are reported against.
- A "small" follow-up edit (a constant, a comment, a test tweak) re-dirties the tree. Check again after it.
- When a Stop hook reports uncommitted changes or unpushed commits, commit and push, then finish. Do not end with a dirty tree or unpushed commits.
- Do not hold a finished commit back to push it "together" with a later step. Push each commit when its check passes, even if the next step is blocked. A wait on another step is not a reason to stack local commits.
- Do not end the turn while a background agent you launched can still write to the tree. Wait for its completion notification, then run `git status` again. A "do not spawn a duplicate" notice means it is still running, not that the turn is done.
- A file a background agent or workflow wrote (a new plan or report `.md`) is untracked until you add it. Check `git status --short` after the agent reports done, and commit it with the rest. "Not yet committed, a restart would lose it" is a reason to commit now, not a status to report while the tree stays dirty.
- Report only what is actually pushed. Do not describe PR or CI state you have not checked.
- Commit trailers (`Co-Authored-By`, `Claude-Session`) are copied verbatim from the session's current attribution reminder. Do not write the model name you believe you run as. Before `git commit`, compare the trailer line with the reminder's line; a different model name (for example Opus where the reminder says Haiku) is a wrong trailer, even when earlier commits in the same session used it.
- After `git commit` and before `git push`, run `git log -1 --format=%B` and check each trailer against the reminder again. Keep these as separate shell calls: a chained `git commit -F - <<'EOF' ... EOF` plus `git push` in one call leaves no point to check. Write the message to a file first, run `grep -E '^(Co-Authored-By|Claude-Session):' <file>`, compare with the reminder, and only then call `git commit -F <file>`. This happened in this session: two commits pushed with `Co-Authored-By: Claude Opus 5.5` while the reminder named Haiku 5.5. It recurred in a later turn after this note existed, so the check is mandatory, never skipped for a "small" commit. If one differs, `git commit --amend` with the corrected line, then push. A commit already pushed with a wrong trailer is reported as such, not silently left.
