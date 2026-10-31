---
name: sqlite-table-rebuild
description: Use when rebuilding a SQLite table or migrating user data.
category: database
---

Rebuild a table inside one transaction, and prove the rollback with a test that fails midway.

- Create the new table, copy rows, drop the old one and rename, all inside one `BEGIN` ... `COMMIT`. On any exception, `ROLLBACK`, so the old rows survive.
- Before the rebuild, list the user-approved rows (confirmed hints, saved states) and assert that they come through with the same ids and values.
- Test the failure path: inject an exception after the copy step, then assert the original table and rows are still there.
- Run that test against the old code first. A rebuild that drops approved rows, or leaves a half-finished transaction, must fail it.
- Run `PRAGMA foreign_key_check` after the rename, and time the migration on a copy of the real database.
