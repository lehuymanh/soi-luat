---
name: pdf-page-render-serving
description: Use when rendering PDF pages to images in FastAPI routes.
category: backend
---

Serialize every pdfium call (open, render, close) behind one process-wide lock. pdfium is not thread-safe: concurrent `/page` requests crashed the server.

- Hold the lock across the whole open-render-close sequence, not only the render.
- Add a test that fires parallel page requests; it must fail before the lock and pass after.
- Keep the lock in the single module that imports pdfium, so no route can bypass it.
