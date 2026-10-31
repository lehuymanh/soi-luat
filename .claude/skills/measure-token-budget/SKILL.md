---
name: measure-token-budget
description: Use when sizing Vietnamese prompts in tokens.
category: llm-eval
---

Measure token counts with the target model's tokenizer on real text. Do not trust an English ratio or an earlier estimate.

- Measure chars-per-token on the target-language corpus with the model's own tokenizer. Non-English ratios differ a lot from English ones.
- Count the whole rendered prompt: system prompt, question, and template text all count against the cap. Take the endpoint's reported `prompt_tokens` from a real run and subtract the fixed overhead.
- Pick one measured figure and use it everywhere it is cited (code comment, README, PR body). When the figure changes, update all of them in the same commit.
- Figures from one measurement (Qwen3-VL tokenizer): legal Vietnamese with headings ran about 3.1 characters per token; Vietnamese JSON about 2.5–3. Use them as a first estimate only. Re-measure for each model.
- Re-measure after any change to the prompt or the output schema.
