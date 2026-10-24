# How these pages are built

The HTML pages at the repo root are generated, then committed. Vercel serves them as
plain static files; there is no build step on Vercel. This folder is excluded from
deployment by `.vercelignore`.

- `src/*.html` holds each page's body. Edit these, not the root HTML files.
- `src/partials/` holds the contact form and its script. `build.py` drops them into any
  page containing `<!--CONTACT_FORM-->`. The homepage's `<!--FAQ_PREVIEW-->` is filled
  from `src/faq.html` using the questions listed in `FAQ_PREVIEW`, so answers match.
- `build.py` adds the shared head, header, footer and JSON-LD, and writes `sitemap.xml`,
  `llms.txt` and `robots.txt`. Page titles, meta descriptions and dates live in its `PAGES` list.
  The FAQ's structured data is generated from the visible questions and answers, so
  the two can't drift apart.
- `check.py` checks links, anchors, JSON-LD, title and description lengths, that structured
  data matches the visible text, that retired or banned wording hasn't crept back, and that
  "LLC" appears only in the footer disclosure. It also lists placeholders still to fill.

From the repo root:

    python3 -I _build/build.py _build/src .
    python3 -I _build/check.py .

When you change a page's content, update its visible "Updated" date and its `modified`
value in `build.py` together.

## Name, domain and contact settings

Each is set once at the top of `build.py`; change it there and rebuild:

- `ENTITY` — the company name. Page sources write it as the token `[ENTITY NAME]`, which
  the build replaces. The footer disclosure adds "LLC" after it; nowhere else does.
- `ORIGIN` — the site's address, `https://[DOMAIN]`. `check.py` reads it from `build.py`, and
  `robots.txt` is regenerated from it on every build, so don't edit either by hand.
- `EMAIL` — the public contact address shown in the footer and structured data.
- `FORM_TARGET` — where the contact form sends: an `https://` form endpoint (for example
  Formspree), or an inbox address (currently `EMAIL`), which opens the visitor's email app.

`check.py` fails if a bracketed placeholder ever reaches a built page.

After setting `ENTITY`, also set it in `og-image.mjs` and run `node _build/og-image.mjs`
from the repo root to redraw the share image, which has the name drawn into it.

Removed pages are redirected in `/vercel.json`.

When the LinkedIn company page and Crunchbase profile exist, add their URLs as
`"sameAs": [...]` in the `ORG` dict in `build.py` and rebuild. Every page updates at once.
