---
name: execute-approved-plan
description: Use when told to carry out an approved plan.
category: workflow
---

An approved plan is the go-ahead. Run its steps in order without asking for permission on each one.

- Track steps as tasks. Mark a step done only after it is verified, not when it starts.
- Stop only for a real blocker: missing credentials, an action outside the plan's scope (for example deleting data or pushing somewhere not planned), or a result that changes the plan.
- Before step 1, scan the plan for decisions it marks open and for steps whose wording conflicts with a written project rule (CLAUDE.md or a skill). Ask those in one question at the start. Approving the plan does not approve a decision the plan leaves open, and the step that needs it is the wrong place to ask.
- If an agent is rewriting the plan file while you build a step, re-read that step's section after it finishes and before you commit the step. The rewrite can change what the step must do.
- A subagent's report that a step is done is a claim, not a result. Before the step is committed, run its tests yourself, read the diff, and look at the screenshots or numbers it cites. For a claim that matters, have a read-only reviewer check it without seeing the builder's conclusion.
- When stopping, name the blocker in one message and say what was already done.
- At the end, report what finished, what is still running, and what is blocked, using the plan's step names.
- Record each step's status and its measured result in the plan file itself, in the commit that finishes the step. Chat is not the plan's record. A step with a gate is done only when it passes, or when its failure branch is written into the plan and taken.
