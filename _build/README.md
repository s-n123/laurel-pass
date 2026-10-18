# How these pages are built

The HTML pages at the repo root are generated, then committed. Vercel serves them as
plain static files; there is no build step on Vercel. This folder is excluded from
deployment by `.vercelignore`.

- `src/*.html` holds each page's body. Edit these, not the root HTML files.
- `build.py` adds the shared head, header, footer and JSON-LD, and writes `sitemap.xml`
  and `llms.txt`. Page titles, meta descriptions and dates live in its `PAGES` list.
  The FAQ's structured data is generated from the visible questions and answers, so
  the two can't drift apart.
- `check.py` checks links, anchors, JSON-LD, and that structured data matches the visible text.

From the repo root:

    python3 -I _build/build.py _build/src .
    python3 -I _build/check.py .

When you change a page's content, update its visible "Updated" date, its card date on
`insights.html`, and its `modified` value in `build.py` together.

When the LinkedIn company page and Crunchbase profile exist, add their URLs as
`"sameAs": [...]` in the `ORG` dict in `build.py` and rebuild. Every page updates at once.
