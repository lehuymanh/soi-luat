---
name: background-job-orchestration
description: Use when a long background job or workflow runs on a low-RAM machine, or its result is missing.
category: background-jobs
---

Check memory before starting a heavy job, and wait on background jobs through an explicit exit marker.

- Before a second heavy job, check free RAM (`free -g`) and CPU (`ps aux --sort=-%cpu | head`). RAM alone is not enough: a second CPU-bound job starves the first, and its client requests time out. If either is tight, stop the model server, run the heavy job alone, then restart the server. An exit 137 means the OOM killer ran; rerun that step alone.
- Launch as `( cmd > log 2>&1; echo "EXIT=$?" >> log ) &`, then wait with `until grep -q "^EXIT=" log; do sleep 5; done` under a timeout.
- Use absolute paths in every backgrounded command. A `cd` inside a background job does not change the session cwd.
- Put each job's log, database copy and result files under the session scratchpad directory, not `/tmp`, unless the user asks for `/tmp`. Give every job its own output path so a rerun cannot overwrite another job's result.
- Before copying a multi-GB database for a measurement, run `df -h /`. Old scratch copies filled the disk to 99%. Delete a copy as soon as its measurement is recorded, and keep at least 1 GB free before the next copy.
- Stop a job with TaskStop, or `kill` the PID from `ps aux | grep "[r]un.py"`. Never run `pkill -f <pattern>` from a shell whose own command line contains the pattern: it kills that shell (exit 144) and every command after it.
- A foreground command is cut at 600 s whatever `timeout` you pass. A long `until grep` wait run in the foreground gets moved to background partway, and the wait's output is then only a notice. For any wait longer than 10 minutes, set `run_in_background: true` from the start and act on its completion notification.
- A background command has a hard time cap (2 hours). Estimate the total first (calls × seconds per call). Split a longer chain into steps that each fit. A chain whose total fits in one script (`a; b`) runs back to back without waiting for a notification; otherwise start the next step when the previous one's completion notification arrives.
- Make a rerunnable job skip items whose output already exists, and have it start the model server itself if the server is down. Then a restart resumes the work instead of redoing it.
- Do not edit source files while a reviewer or workflow is reading them. Wait for it to finish, then edit.
- If a file-changed-on-disk notice appears, run `git diff` to confirm what changed before going on.
- After a container restart, every background task is dead. Run `git status`, list which intermediate outputs exist under the work directory, and rerun only the steps whose outputs are missing.
- When a fix changes what a running job measures, stop that job with TaskStop and rerun it on the final code. Never report numbers from a run that started before the fix.
- `grep -c` prints `0` and exits 1 on no match, so `$(grep -c … || echo 0)` expands to two zeros. `[ … -ge 2 ]` then fails with `too many arguments`, the condition is never true, and the wait runs silently to its timeout. Use `n=$(grep -c … log); n=${n:-0}` (or `|| true`), and check the wait's exit condition in a one-off run before relying on it.
- A background workflow's `<task-notification>` output file may hold only a log, with no parseable result. Do not regex that file for the JSON. Read the workflow's `subagents/workflows/wf_*/journal.jsonl` instead: a `started` line maps `key` to `label`, and the `result` line with the same `key` carries the payload. Join by key, and take `find:` and `refute:` labels as separate results.
