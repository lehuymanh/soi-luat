# Bundling a web font for an offline app

1. Request the Google Fonts CSS with a desktop-browser User-Agent. The API picks the file format from the User-Agent, so a bare request does not return the woff2 list.
   `curl -sS -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36" "https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600&display=swap" -o family.css`
2. Each subset is preceded by a comment: `/* vietnamese */`, `/* latin-ext */`, `/* latin */`. Keep one `@font-face` per subset and weight, with its `unicode-range`.
3. Download each woff2 into `static/fonts/` under a name such as `be-vietnam-pro-400-vietnamese.woff2`. Write `src: url("fonts/<name>") format("woff2")` in the stylesheet: a relative `fonts/...` in `/static/app.css` resolves to `/static/fonts/`.
4. Save the family's `OFL.txt` next to the files. The license ships with the font.
5. Check the count and size. Be Vietnam Pro at weights 400, 500 and 600 across three subsets gave 9 files, about 141 KB.
