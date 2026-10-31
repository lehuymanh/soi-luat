---
name: vietnamese-legal-qa-bench
description: Use when measuring Soi Luật search or answer quality.
category: llm-eval
---

Measure Soi Luật only through the bench scripts, and keep the unlicensed gold set out of the repo.

- Build result tables with `bench/llm/bang.py` from the raw JSON that `run.py` writes. Never copy a figure by hand.
- Before any model run, measure the built context offline with `bench/llm/bang_chung.py` on the train split. Spend model runs only on the chosen design.
- Trap questions are generated from the corpus and are not split by default. List the test ids they touched in the summary.
- Gold `vle` questions have no license: never commit them. Commit only results derived from them.
- Advance mode needs `SOILUAT_MODEL_DIR` and `SOILUAT_RERANK_DIR`. Without them a run is not Advance; see benchmark-split-hygiene.
- `bench/stress10/run.py` needs `SOILUAT_TESSDATA=/usr/share/tesseract-ocr/5/tessdata` for the JPG pages. Without it the Vietnamese OCR pack is missing, s07 reports "Thiếu gói tiếng Việt", and the score reads 18/20 instead of 20/20.
- Read the method section of `GHI-NHO-NGHIEN-CUU.md` before changing a split or a metric.
- Before adding a metric to `bench/zalo/eval.py` or `bench/van-ban-that/eval_real.py`, rerun the existing baseline method (`hien_tai`) on the same build and confirm it reproduces the committed numbers exactly. A change that moves the baseline is a bug.
- Pass `--tag` to every eval run. Without it the script overwrites the committed `bench/zalo/ket_qua_test.json`. Delete smoke-run tagged JSON before `git add`, because tagged files are not gitignored.
- Run `bench/van-ban-that/eval_real.py` only on a copy of its data dir: it writes `search_mode` into the DB, and each build gets its own realdocs copy.
- When several methods share one cached search per query, the first method pays the search time and the rest read the cache. Report one latency for the shared step; per-method p50 values are artifacts of call order.
- Normalize set-valued results before membership tests: `k in want` with a `frozenset` key is always false, so Recall reads 0 without an error. Check one known-positive query by hand.
