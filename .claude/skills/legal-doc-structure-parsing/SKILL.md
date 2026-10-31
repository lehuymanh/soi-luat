---
name: legal-doc-structure-parsing
description: Use when splitting Vietnamese legal text into Điều units, Phụ lục cards, signature or "Nơi nhận" blocks, or OCR-broken headings.
category: document-parsing
---

Judge a parser change by hand-counted article truth on real scanned documents, never by the structure score alone.

- Keep a per-document truth file: the last Điều number a reader sees on the scan, plus known OCR breakages. Compare Điều found against truth per document. A structure score of 0,94 to 0,99 hid 20 lost articles in two documents.
- Check each failure class before calling the parser good: an OCR opening quote (“) with no closing quote swallows every later article; the "Nơi nhận" block and signatures land in the last unit; a Phụ lục is dropped or merged into the last article, although it can hold most of a thông tư; a quoted amendment ("Điều 15.") is taken as the document's own article; OCR breaks headings ("Điều §.", "Điều 3,").
- A gain found on the documents where the bug showed is in-sample for them. Report it as found on that set, and confirm it on documents the fix was not derived from before calling it a gain.
- Before any full benchmark run, rebuild the whole corpus parse-only and compare a hash of the unit table with the committed one. Zero changed documents means the benchmark result is unchanged; any change means rerun. Bump the parser revision once per batch of changes.
- Ship each candidate fix as its own patch that passes `git apply --check` on HEAD, plus one combined patch with its own tests. A fix that stops applying after another landed is reported as conflicting, not forced.
- When several parts of one Phụ lục merge into one search card, the card's page span is the union of all merged parts' pages, not the first part's. Keeping the first part's page dropped a question's rank in the bench; check per-question rank after any merge.
- Laws and Nghị quyết of the Quốc hội have no "Nơi nhận" block. Their signature block opens at the closing sentence "… này được Quốc hội nước Cộng hòa … thông qua" (not when that sentence sits inside a quoted amendment), and a Phụ lục after it must become its own unit. Without that cut, the signatures and the Phụ lục collapse into the last Điều.
- Strip page-number-only lines ("12", "- 13 -") at display and snippet time only. Keep the indexed text raw, so search results and the measured numbers do not change and no rerun is needed.
