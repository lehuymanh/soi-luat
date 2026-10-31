---
name: query-reference-parsing
description: Use when search queries cite số hiệu, dates, Điều or khoản.
category: legal-qa
---

Read the reference in a user query with exact-key rules: a date is never a document number, and every lookup key is normalized before comparison.

- A day/month/year group in a date (`05/02/2021`, `tháng 10/2020`) is not the prefix of a số hiệu. Test the prefix regex with a query that contains a date and one without, and confirm the date does not narrow the search to one document.
- Pad numeric parts before matching: `2/2021/TT-BTC` must find a document written `02/2021/TT-BTC`.
- Normalize Unicode to NFC and compare text case-insensitively. Pasted NFD text must match `Điều`, and `Điều 1A` must match `điều 1a`.
- A `khoản n` or `điểm x` next to `Điều m` narrows only as far as the card text allows. Until the clause is a lookup key, report the result as the whole Điều and keep a `shortcut:` comment in the code naming the limit and the upgrade step.
- Each rule gets a test that fails on the old code. A test with a date-free query proves nothing about the date rule.
