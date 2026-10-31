---
name: release-version-sync
description: Use when bumping the version or tagging a release.
category: git-workflow
---

Before tagging, the version must match in every place it lives, and the user must have confirmed the number.

- Grep the version in `src/soiluat/__init__.py` (`__version__`), `pyproject.toml`, `pack/SoiLuat.iss`, and the README. Set all of them in one commit. Versions drift: one check found `0.8.0` in pyproject and `0.7.0` in `__init__`.
- Run `git tag` and list the GitHub releases first, and compare them with the version already in the app.
- If the requested number is lower than the version the app already reports, ask the user before changing anything. Installed copies would show a downgrade.
- Build the wheel and sdist locally. The Windows installer must be built by `pack/build.ps1` on a Windows machine; say so in the report instead of claiming it exists.
- A fresh venv does not have the `build` package, so `python -m build` fails with `No module named build`. Install it first. Build from `git archive HEAD` in a scratch folder so untracked files stay out.
- After building, list the wheel. Every non-`.py` package file must be inside it (`schema.sql`, `synonyms_seed.csv`, `static/`, `templates/`); the 0.9.0 check found 61 entries and the fonts present.
- Name installer and artifact files only as the build config produces them: read the output name in `pack/SoiLuat.iss` (or the build script) before writing it into notes. A guessed name (`SoiLuat-0.9-setup.exe`) was caught and corrected only on re-read.
- If the tag push is refused (HTTP 403 when the session may push only to its own branch), do not retry or route around it. Keep the tag local, record the target commit hash in the PR body and release notes, and give the user the Release-page steps: new tag name, target commit, attached wheel and sdist with sha256.
- Push the tag and the release notes. If no tool can create the GitHub Release object, tell the user to create it from the tag.
- Do not merge the PR yourself; the user decides the merge.
- Recount every figure in the release notes (findings found, confirmed, fixed, deferred) from the ledger or the commit list just before writing it. A hand count gave 31 where the list held 32.
- Each measured number in the notes comes from a run on the final commit, and the notes name that commit. A number taken before the last fix is stale.
- Keep the release-notes draft as `CHANGELOG.md` inside the repo and commit it early. A draft kept only in the scratchpad is lost with the container.
