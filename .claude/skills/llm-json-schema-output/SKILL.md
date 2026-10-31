---
name: llm-json-schema-output
description: Use when constraining LLM output with a JSON schema.
category: llm-eval
---

Design the schema so every allowed output fits the token cap, and so each field is generated after the facts it depends on.

- Property order is generation order. Put the check before the decision that depends on it. Example: `tien_de_sai` (is the question's premise wrong?) goes before `du_can_cu` (do the passages answer it?). With the flag first, the model marks a false-premise question as unanswerable and then cannot cite.
- Branch with `anyOf` on a `const` flag so each value of the flag forces a consistent shape. Answerable means 1–2 cited points (`minItems: 1`); unanswerable means `maxItems: 0`.
- Make source ids an `enum` of exactly the passage numbers given, then check them again after generation.
- Cap every string with `maxLength` and every list with `maxItems`, sized so the worst case fits `n_predict`. Without caps, a verbose answer is cut mid-item and the JSON is invalid.
- Caps can still miss. On a 4,096-context run with `n_predict` 200, every invalid output in the Zalo test split hit 200 tokens even with caps on every field, and about 12% of calls stayed invalid. Count truncated outputs per run and report that rate next to accuracy. If it stays above a few percent, shorten the caps further before touching the token limit.
- When JSON validity drops, look at `completion_tokens` first. If the bad outputs all hit `n_predict`, the cause is truncation, not format. Fix it with the caps above, or by asking for short points that do not repeat the answer, not by raising the token cap past the latency budget.
- Add the worst-case caps in tokens, not per field. Measure the output's characters per token (Vietnamese JSON ran 2.5–3 characters per token) and compare the total with `n_predict`. Caps that sum to about 1,000 characters ran 330–400 tokens against an `n_predict` of 200, so they could not prevent truncation.
- Block the wrong script in the grammar, not in the prompt. Give every string a `pattern` that excludes the CJK, Kana and Hangul Unicode blocks. A Qwen model answered in Chinese on a probe question; the pattern stopped it at generation time without slowing decode. Check the pattern compiles on the server and that a Chinese-eliciting question still gets a Vietnamese answer.
- A JSON output cut at `n_predict` can be salvaged: keep the closed items, drop the partial one, and score it as salvaged, not as valid. Salvage can leave zero cited points (15 of 20 cut answers did), so report that count separately.
- Validate each schema change with one short run before a scored run. Confirm the grammar compiles on the server in use (llama-cpp-python and llama-server both accept `response_format: {"type": "json_object", "schema": …}`).
