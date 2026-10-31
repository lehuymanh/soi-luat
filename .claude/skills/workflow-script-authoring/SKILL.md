---
name: workflow-script-authoring
description: Use when editing a .claude/workflows/*.js Workflow script.
category: workflow
---

Parse every edited Workflow script before running it, keep session-specific paths out of it, and pass the attribution trailer in as an argument.

- Syntax-check each edited script from the repo root with `node .claude/skills/workflow-script-authoring/scripts/check_syntax.js .claude/workflows/*.js` before the first run. A syntax error otherwise appears only after its agents have already spent their time.
- Before committing, grep the scripts for session paths and ids (`/tmp/claude`, `/root/`, `session_`, `Co-Authored-By: Claude`). A hard-coded session path breaks the next session.
- Sub-agents do not see the coordinator's attribution reminder. Take the two trailer lines as `args.trailer`, copied verbatim from that reminder, and stop with a clear error when it is missing.
- A step whose check needs a measurement longer than 10 minutes must not wait for it inside an agent. The agent commits its change and returns the marker `CHỜ ĐO:` with the command to run. The coordinator runs that command in the background, and the script collects those step ids into a `pending` field and logs them.
- Check the agent count against the limit in the script before launching, and fail with a message that says how to split the run.
- Validate `args` at the top of the script and throw before any agent starts: `args.python` must be the project venv interpreter (the system `python` has no pytest), and `args.trailer` must be present.
- Match the `CHỜ ĐO` marker loosely in the coordinator: accept lowercase, decomposed-accent forms (normalize with NFC first) and a missing colon.
- A killed or stopped run resumes with `Workflow({scriptPath, resumeFromRunId})` and the same args. Keep the runId from the launch result. Completed agents replay from cache, and a cached result can be empty, so read the journal before assuming nothing is left to recover.
- A step that fails after its agents already ran must still return the commit list it produced, so the next step does not lose the work.

Syntax check script: `scripts/check_syntax.js`.
