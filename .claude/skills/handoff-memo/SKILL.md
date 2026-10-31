---
name: handoff-memo
description: Use when writing a handoff memo for the next agent.
category: documentation
---

A handoff memo puts the resume point first, then conclusions, then method, then what could not be checked. A reader who stops after the first section must know where to start and what not to re-measure.

- Open with the current state and the first step to take, then the list of results that must not be re-run before any new measurement.
- Separate three things: conclusions, method (how each number was produced, with the command and the file it came from), and open questions. Every figure must be recomputable from a named file.
- Before committing, check every file path and symbol the memo cites with `ls` and `grep -n`. A wrong path sends the next agent to the wrong place with full confidence. Cite paths from the repo root (`src/soiluat/answer.py`, not `answer.py`): a bare basename fails the `ls` check even when the file exists, so write the full path in the memo and run the check on that form.
- Name what this environment could not check (hardware, network, a missing dependency) and what the next run must measure again.
- List the other documents the next reader needs, in the order to read them, and say which sections of each to read first.
