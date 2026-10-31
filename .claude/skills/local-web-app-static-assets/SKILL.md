---
name: local-web-app-static-assets
description: Use when moving JS, CSS or fonts out of a FastAPI template.
category: frontend-design
---

Serve JS, CSS and fonts as files under the package's `static/` folder, mounted by the app. Keep the HTML template free of inline script and style.

- Mount with a `StaticFiles` subclass that sets `Cache-Control: no-cache`. After an upgrade the browser then refetches `app.js` instead of running the old copy.
- Register MIME types at import with `mimetypes.add_type` for `.js`, `.css` and `.woff2`. Windows reads them from the registry; a broken registry serves JS as `text/plain`, and the browser silently refuses to run it.
- Pass per-page values (CSRF token, allowed file suffixes) as `data-*` attributes on `<body>`, and have the static script read them. Jinja expressions such as `tojson` do not run inside a static file.
- A POST helper that gets 403 re-reads the CSRF cookie that the 403 response refreshed and retries once. Test that the 403 carries the new `Set-Cookie`.
- The host and CSRF guards must cover `/static/*` too. Test that a non-local Host gets 400 there.
- Add `static/*` and `static/fonts/*` to package-data in `pyproject.toml`, and make the PyInstaller spec collect every file under `static/`. A missing folder fails when the app mounts, so add a test that the spec mentions `static`.
- Put global resets (`*, *::before, *::after { box-sizing: border-box; }`) in the shared static stylesheet, not only in an included base template. A new standalone page that skips the include silently loses them and its widths drift.
- Verify in a real browser, not only in pytest: follow `html-mockup-visual-check` for a served page.
- Bundling web fonts for an offline app: follow `references/offline-fonts.md`.
