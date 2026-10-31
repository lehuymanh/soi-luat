---
name: vietnamese-legal-number-check
description: Use when checking Vietnamese legal amounts or dates.
category: legal-qa
---

Extract numbers only after replacing structural references and passage markers with labelled tokens, and read Vietnamese amounts and dates the way Vietnamese writes them.

- A dot is a thousands separator when exactly three digits follow it (`5.000.000`). A dot followed by one or two digits is a decimal (`1.5 triệu`, `0.5%`).
- Dates normalize to one key whether written `dd/mm/yyyy`, `dd.mm.yyyy` (`01.08.2030`), `ngày X tháng Y năm Z`, or ISO.
- Replace `Điều N`, `khoản N`, `điểm x`, `[n]` chips and `đoạn N` with tokens (`dieu:5`, `khoan:2`) before extracting values. They then match only references, never amounts.
- Document numbers (`36/2024/QH15`) are not amounts. In lenient source mode, take digits only when they are not attached to letters, so `QH15` yields nothing.
- In a range, the first number borrows the second number's unit only when it is a plain count below 1000 with no thousands separator and only a range word sits between them: `1 đến 2 triệu` → {1e6, 2e6}, `1.5 đến 2 triệu` → {1.5e6, 2e6}. A full amount never borrows: `500.000 đến 1 triệu` → {500000, 1000000}, not 5e11.
- Read number words as values: `mười lăm tuổi` is 15. A checker that ignores words flags a faithful answer as an invented number.
- `mười năm` is ten years, not fifteen. After `mười` or `mươi`, a bare `năm` is the unit (year); fifteen is `mười lăm`. Reading `năm` as the digit 5 turns a faithful answer into an invented number. This was the most serious bug an independent review found in the round-2 checker.
- A letter reference (`điểm a`, `khoản a`) is a structural token like `khoan:2`. The answer and the source may use either word for the same letter (`khoản a` for `điểm a`), so match the letter and its containing clause, not the word, and never read it as an amount.
- A document number cut by a length cap (`155/2020/NĐ-`) is not an amount. Strip document numbers before checking, including truncated ones.
- Add one test per case before changing the regex. Case list: `references/number-cases.md`.
