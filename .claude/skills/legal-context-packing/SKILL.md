---
name: legal-context-packing
description: Use when trimming legal articles to a prompt budget.
category: legal-qa
---

Keep the lines that match the question together with the lead-in each kept child depends on. Trim by whole lines, never mid-clause.

- When a kept point (`điểm`) or clause (`khoản`) is kept, keep its parent lead-in too. Without the lead-in a penalty amount loses its meaning.
- If the best-matching line does not fit, skip it and its neighbours. Do not spend budget on the neighbours of a line that was not kept.
- Dedupe identical Điều across documents by a key of title plus body. Body alone merges Điều with the same clauses but different titles (`viên chức` versus `công chức`).
- Measure the budget in the model's tokens, not characters, per the measure-token-budget skill.
- After a long article is cut to budget, check whether the kept lines still contain the line that holds the cited figure. Word overlap with the question is a weak picker: weight rarer words higher. In a real-document run, most wrong citations had lost that line before the model saw the context.
