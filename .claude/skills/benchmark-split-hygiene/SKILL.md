---
name: benchmark-split-hygiene
description: Use when tuning on an eval set or reporting scores.
category: evaluation
---

Choose settings on train or dev data. Report quality only from a held-out test split, scored once after the last change.

- Run A/B variants on the same sample with the same settings, changing one thing per variant.
- Label every reported number with its split (train, dev, test).
- Compare modes only on one corpus build. If the corpus was rebuilt on another machine, measure every arm on that build and state its parse accuracy beside the numbers.
- Keep machine-graded quality metrics separate from hardware-dependent latency. Label latency with the machine it came from.
- A dev-split number can justify a choice. It is never reported as quality.
- Before an A/B run, check that nothing else loads the CPU (`ps aux --sort=-%cpu | head`). A run whose LLM calls time out (`TimeoutError` at the client limit) was starved, not measured: discard it, rerun on an idle machine, and report nothing from it.
- A run labelled with a mode (advance, normal, one A/B arm) must fail fast when that mode is not really active, for example when vectors or the model are missing. A silent fallback reports one mode while measuring another.
- Before trusting a grader, feed it a deliberately wrong answer (the question's own number, a near-duplicate passage) and confirm it scores wrong.
- Before calling a failed answer a model error, rebuild the exact context it was shown (the context builder is deterministic) and have two independent judges classify each failure as supported by the passages, partly supported, or unsupported. Report the split. In a removed-gold "should refuse" test, most failures can be benchmark noise: the answer is supported by another passage in the corpus.
- Report each quality rate with its denominator. Accuracy over valid outputs and accuracy over all calls are different numbers; state which one you report, and report the valid-output rate beside it.
- Before blaming the model for a gate failure, count the harness's own failures first: outputs truncated at the token limit, and contexts that dropped the evidence line. Re-score after fixing them, and report both numbers.
- Say what a timer covers. An in-process timing (a test client, no browser) excludes page rendering. Label it server-side, and leave the browser figure as unmeasured until someone measures it.
- Put the sample size beside every rate. With 15–30 questions per split, one rate can move roughly ±16–25 points at 95%. Do not present a small gap as a ranking.
- Before publishing a summary, recompute every figure and comparative word (most, largest, better, ahead) from the raw result file with a script, or have a separate check do it. Quote ranges exactly. When a metric has a loose and a strict definition, label both.
- A question bank generated once and reused (trap or should-refuse items) is not split by default. If any of its items were loaded while tuning, they are not held-out. Split the bank by item before tuning, or report the touched test items as their own row and say so in the summary.
- Before writing "chosen on train, scored once on test", list the test item ids that every tuning run loaded and compare them. A claim about the split is a figure too.
- A figure is valid only for the commit it ran on. Record that commit beside each number. A claim that a later fix leaves the figures unchanged must be checked by diffing the measured path, not asserted; if the diff touches it, rerun.
- A fix found by reading the documents where the bug showed is in-sample for those documents. Report its gain as found on that set, and confirm it on documents the fix was not derived from before calling it a gain.
- Name the percentile method. Nearest-rank (`sorted[int(n*p)]`) and linear interpolation (numpy default) differ by seconds at p95 with 30–80 calls. Pick one, state it, and recompute with it.
- Compare two models or variants on the same items with a paired test on the discordant items (McNemar) before calling one better. With about 65 items, a gap of a few items is noise; report the p-value beside it.
- Wall-clock latency from a shared machine is comparable only within one time window, even on the same box. Report output tokens and seconds per output token beside the time: a model that writes fewer tokens looks faster for that reason alone.
- When the owner sets a keep-or-revert condition on a fix (for example, keep only if the Zalo and gold scores do not drop), run the same split before and after on one build. Write both numbers and the keep or revert decision into the plan or commit message before the push, and revert if the condition fails.
- When a combined change lowers a metric, measure each component alone before deciding what to keep. Sentence-splitting and window cutting can interact; one fix can hide the other's loss.
- Choose a context or prompt design with a deterministic offline proxy on the train split (for example, evidence coverage in the built context). Spend model runs only on the design the proxy picked.
- A figure about someone else's study (a paper's recall gain, a vendor's benchmark score) goes into a roadmap or report only with a link you opened this session. A figure recalled from memory is written as "chưa kiểm nguồn" or left out, and never mixed into the project's own measured numbers.
