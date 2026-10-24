"""Wrap page fragments in the shared head, header, footer and JSON-LD.

Usage, from the repo root: python3 -I _build/build.py _build/src .
"""
import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

SRC = Path(sys.argv[1])
OUT = Path(sys.argv[2])

# The entity name, domain and contact address, each set once here. Page sources write the name
# as the token [ENTITY NAME]; render() swaps in ENTITY.
ENTITY = "Laurel Way Partners"
ORIGIN = "https://laurelwaypartners.com"
EMAIL = "hello@laurelwaypartners.com"
# Where the contact form sends: a form endpoint URL (e.g. Formspree) or an inbox address.
FORM_TARGET = EMAIL
DISCLOSURE = (f"{ENTITY} LLC is not a law firm and does not provide legal services. The firms we "
              "work with are independently owned and operated by licensed attorneys.")
DESCRIPTION = (f"{ENTITY} is an attorney-led platform that partners with elder law, estate planning "
               "and probate firms in the New York metro area and northern New Jersey.")
PUBLISHED = "2026-10-23"

ORG = {
    "@type": "Organization",
    "@id": ORIGIN + "/#organization",
    "name": ENTITY,
    "url": ORIGIN + "/",
    "logo": ORIGIN + "/logo.png",
    "image": ORIGIN + "/og-image.png",
    "description": DESCRIPTION,
    "email": EMAIL,
    "areaServed": ["New York City", "Nassau County, NY", "Suffolk County, NY",
                   "Westchester County, NY", "Northern New Jersey"],
    "knowsAbout": ["Elder law practice succession",
                   "Estate planning practice succession",
                   "Probate and trust administration practices",
                   "Sale of a law practice under Rule 1.17"],
}

# path: output file; url: public path; kind: website | page | contact | about | faq | notfound
PAGES = [
    dict(src="home", out="index.html", url="/", kind="website", modified="2026-10-23",
         title=f"Partner or Sell Your Estate Planning Practice | {ENTITY}",
         og_title="Your practice. Your clients. A partner who'll still be there.",
         desc="Sell your estate planning, elder law or probate practice in New York or northern NJ on your timeline, or sell a minority stake and keep practicing.",
         og_desc="A partner to elder law, estate planning and probate firms across the New York area and northern New Jersey.",
         cta=False),
    dict(src="partner", url="/partner", kind="page", nav="partner", modified="2026-10-23",
         title=f"Elder Law Practice Succession, Long Island to NJ | {ENTITY}",
         desc="Own an elder law, estate planning or probate firm on Long Island, in Westchester, NYC or northern NJ? Sell a minority stake to an attorney and keep practicing."),
    dict(src="retire", url="/retire", kind="page", nav="retire", modified="2026-10-23",
         title=f"Sell Your Elder Law or Probate Practice in NY/NJ | {ENTITY}",
         desc="Planning retirement from an elder law, estate planning or probate practice in Westchester, Long Island, NYC or northern NJ? A fair purchase under the rules."),
    dict(src="about", url="/about", kind="about", nav="about", modified="2026-10-23",
         title=f"About {ENTITY} | Attorney-led, NY Metro and Northern NJ",
         desc="An attorney-led platform partnering with elder law, estate planning and probate firms in the New York metro area and northern New Jersey: what it does and why."),
    dict(src="faq", url="/faq", kind="faq", nav="faq", modified="2026-10-23",
         title=f"Estate Planning and Elder Law Practice Owner FAQ | {ENTITY}",
         desc="Who owns the firm, what happens to staff, client files and original wills, how price and financing work, timing, fees and confidentiality. Plain answers."),
    dict(src="contact", url="/contact", kind="contact", nav=None, cta=False, modified="2026-10-23",
         title=f"Start a Confidential Conversation | {ENTITY}",
         desc="Tell us about your elder law, estate planning or probate practice. You'll hear back within two business days, and nothing goes to anyone else without an NDA."),
    dict(src="404", out="404.html", url="/404", kind="notfound", noindex=True, cta=False,
         title=f"Page not found | {ENTITY}",
         desc="This page doesn't exist. Read about partnering or retiring, see common questions, or start a confidential conversation."),
]

FAQ_PREVIEW = ["Who will own my firm?", "Do I have to stop practicing?", "Is this confidential?",
               "Do you charge sellers anything?", "What if I'm not ready yet?"]

NAV = [("partner", "/partner", "Keep practicing"),
       ("retire", "/retire", "Retire"),
       ("about", "/about", "About"),
       ("faq", "/faq", "FAQ")]

LOGO_SVG = ('<svg width="30" height="30" viewBox="0 0 28 28" fill="none" stroke="#7A2E2A" '
            'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            '<path d="M14 26V5"/><path d="M14 21C10 21 7.5 18.5 7 15C10.5 15.2 13 17.5 14 21Z"/>'
            '<path d="M14 21C18 21 20.5 18.5 21 15C17.5 15.2 15 17.5 14 21Z"/>'
            '<path d="M14 14C10.5 14 8.5 11.8 8 8.8C11 9 13.2 11 14 14Z"/>'
            '<path d="M14 14C17.5 14 19.5 11.8 20 8.8C17 9 14.8 11 14 14Z"/>'
            '<path d="M14 7.5C12.5 6.5 12.2 4.5 14 2.5C15.8 4.5 15.5 6.5 14 7.5Z"/></svg>')


class TextOf(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def text_of(fragment):
    p = TextOf()
    p.feed(fragment)
    return re.sub(r"\s+", " ", "".join(p.parts)).strip()


def faq_entities(body):
    out = []
    for q, a in re.findall(r"<details[^>]*>\s*<summary>(.*?)</summary>(.*?)</details>", body, re.S):
        out.append({"@type": "Question", "name": text_of(q),
                    "acceptedAnswer": {"@type": "Answer", "text": text_of(a)}})
    return out


def h1_of(body):
    m = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S)
    return text_of(m.group(1)) if m else ""


def schema_for(page, body):
    url = ORIGIN + page["url"]
    graph = [ORG]
    kind = page["kind"]
    if kind == "website":
        graph.append({"@type": "WebSite", "@id": ORIGIN + "/#website", "name": ENTITY,
                      "url": ORIGIN + "/", "publisher": {"@id": ORG["@id"]}})
        graph.append({"@type": "WebPage", "@id": url + "#page", "url": url, "name": page["og_title"],
                      "description": page["desc"], "isPartOf": {"@id": ORIGIN + "/#website"},
                      "about": {"@id": ORG["@id"]}})
    elif kind == "faq":
        graph.append({"@type": "FAQPage", "@id": url + "#faq", "url": url,
                      "mainEntity": faq_entities(body)})
    elif kind in ("page", "contact"):
        graph.append({"@type": "ContactPage" if kind == "contact" else "WebPage", "@id": url + "#page", "url": url, "name": h1_of(body),
                      "description": page["desc"], "about": {"@id": ORG["@id"]}})
    elif kind == "about":
        graph.append({"@type": "AboutPage", "@id": url + "#page", "url": url, "name": h1_of(body),
                      "description": page["desc"], "about": {"@id": ORG["@id"]}})
    data = {"@context": "https://schema.org", "@graph": graph}
    return json.dumps(data, indent=1, ensure_ascii=False).replace("</", "<\\/")


def header(page):
    links = []
    for key, href, label in NAV:
        if page["url"] == href:
            cur = ' aria-current="page"'
        elif page.get("nav") == key:
            cur = ' aria-current="true"'
        else:
            cur = ""
        links.append(f'<a class="link" href="{href}"{cur}>{label}</a>')
    return f"""<header class="site-header">
<div class="wrap row">
<a class="brand" href="/">
{LOGO_SVG}
<span>{ENTITY}</span>
</a>
<nav class="row site-nav" aria-label="Main">
{chr(10).join(links)}
<a class="btn btn-primary" href="/contact">Start a confidential conversation</a>
</nav>
</div>
</header>"""


CTA = """<section class="dark cta-band">
<div class="wrap row">
<h2>Thinking about what comes next for your practice? A first call is confidential and commits you to nothing.</h2>
<a class="btn btn-primary" href="/contact" style="font-size:17px">Start a confidential conversation</a>
</div>
</section>"""

FOOTER = f"""<footer class="dark site-footer">
<div class="wrap">
<div class="row footer-cols">
<div class="footer-about">
<h2>{ENTITY}</h2>
<p>{DESCRIPTION}</p>
<p><a href="mailto:{EMAIL}">{EMAIL}</a></p>
</div>
<div>
<h2>Two ways to work together</h2>
<ul>
<li><a href="/partner">Partner and keep practicing</a></li>
<li><a href="/retire">Retire on your timeline</a></li>
</ul>
</div>
<div>
<h2>More</h2>
<ul>
<li><a href="/#how">How a conversation works</a></li>
<li><a href="/about">About</a></li>
<li><a href="/faq">FAQ</a></li>
<li><a href="/contact">Start a confidential conversation</a></li>
</ul>
</div>
</div>
<div class="row footer-legal">
<p>© 2026 {ENTITY}. All rights reserved.</p>
<p>{DISCLOSURE} Nothing on this site is legal or tax advice.</p>
</div>
</div>
</footer>"""

ANALYTICS = """<script>window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };</script>
<script defer src="/_vercel/insights/script.js"></script>"""


def form_action():
    if not (FORM_TARGET == "[FORM ENDPOINT OR INBOX]" or FORM_TARGET.startswith("https://")
            or re.fullmatch(r"[^\s@\[\]:]+@[^\s@\[\]]+", FORM_TARGET)):
        sys.exit(f"FORM_TARGET must be an https:// endpoint or a bare inbox address, got {FORM_TARGET!r}")
    if FORM_TARGET.startswith("https://"):
        return f' action="{FORM_TARGET}"'
    if re.fullmatch(r"[^\s@\[\]]+@[^\s@\[\]]+", FORM_TARGET):
        return f' action="mailto:{FORM_TARGET}?subject=Confidential%20inquiry" enctype="text/plain"'
    return ""


def render(page):
    body = (SRC / (page["src"] + ".html")).read_text()
    script = ""
    if "<!--SCRIPT-->" in body:
        body, script = body.split("<!--SCRIPT-->", 1)
    if "<!--FAQ_PREVIEW-->" in body:
        faq = (SRC / "faq.html").read_text()
        blocks = {text_of(q): m for m, q in re.findall(r"(<details><summary>(.*?)</summary>.*?</details>)", faq, re.S)}
        body = body.replace("<!--FAQ_PREVIEW-->", "\n".join(blocks[q] for q in FAQ_PREVIEW))
    if "<!--CONTACT_FORM-->" in body:
        noscript = "" if form_action() else (
            '<noscript><p style="margin:0;font-size:14px;color:var(--muted)">This form isn\'t connected '
            f'yet. Please write to {EMAIL} instead.</p></noscript>')
        form = (SRC / "partials" / "contact-form.html").read_text()
        form = form.replace("{action}", form_action()).replace("{noscript}", noscript)
        body = body.replace("<!--CONTACT_FORM-->", form.strip())
        script += (SRC / "partials" / "contact-form-script.html").read_text().replace("{target}", FORM_TARGET).replace("{email}", EMAIL)
    body = body.replace("[ENTITY NAME]", ENTITY)
    url = ORIGIN + page["url"]
    og_type = "website"
    e = html.escape
    if page.get("noindex"):
        robots, og_url = '<meta name="robots" content="noindex">\n', ""
    else:
        robots = f'<link rel="canonical" href="{url}">\n'
        og_url = f'<meta property="og:url" content="{url}">\n'
    head = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(page["title"])}</title>
<meta name="description" content="{e(page["desc"])}">
{robots}<meta property="og:site_name" content="{ENTITY}">
<meta property="og:title" content="{e(page.get("og_title", h1_of(body)))}">
<meta property="og:description" content="{e(page.get("og_desc", page["desc"]))}">
<meta property="og:type" content="{og_type}">
{og_url}<meta property="og:image" content="{ORIGIN}/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{ENTITY}: a partner to elder law, estate planning and probate firms in the New York area and northern New Jersey">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon-48.png" sizes="48x48" type="image/png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/styles.css">
<script type="application/ld+json">
{schema_for(page, body)}
</script>
{ANALYTICS}
</head>
<body>

{header(page)}

<main>
{body.strip()}

{CTA if page.get("cta", True) else ""}
</main>

{FOOTER}
{script.strip()}
</body>
</html>
"""
    head = re.sub(r"\n{3,}", "\n\n", head)
    dest = OUT / page["out"] if "out" in page else OUT / (page["url"].lstrip("/") + ".html")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(head)
    return dest


def sitemap():
    rows = []
    for p in PAGES:
        if p.get("noindex"):
            continue
        rows.append(f"  <url>\n    <loc>{ORIGIN}{p['url']}</loc>\n"
                    f"    <lastmod>{p.get('modified', PUBLISHED)}</lastmod>\n  </url>")
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(rows) + "\n</urlset>\n")


def llms():
    pages = [p for p in PAGES if not p.get("noindex") and p["url"] != "/"]
    lines = "\n".join(f"- [{p['title'].split(' | ')[0]}]({ORIGIN}{p['url']}): {p['desc']}" for p in pages)
    text = f"""# {ENTITY}

> {DESCRIPTION}

{ENTITY} works with owner-operators of elder law, estate planning, and probate and trust administration firms on Long Island, in Westchester, in the five boroughs and in northern New Jersey, typically with roughly $750K–$3M in revenue and one to five attorneys. Owners choose one of two paths: partner and keep practicing (sell a minority stake to an attorney licensed in the firm's state for liquidity, keep running the practice, have a services team handle marketing, intake, administration and technology under the firm's direction, and hold equity in the platform), or retire on their own timeline (a purchase by an attorney licensed in the owner's state, structured under the professional rules on the sale of a law practice, staff kept, a structured handoff). Firms stay owned by attorneys; {ENTITY} holds no stake in any law firm. Conversations are confidential and covered by an NDA before any details are shared. {DISCLOSURE} Contact: {EMAIL}

## Start here

- [{ENTITY}]({ORIGIN}/): The two paths, what stays the same, what the services team handles, what we look for, and how a conversation works.

## Pages

{lines}
"""
    (OUT / "llms.txt").write_text(text)


def robots():
    (OUT / "robots.txt").write_text(
        "# Open to every crawler, including search and AI crawlers:\n"
        "# Googlebot, Bingbot, OAI-SearchBot, ChatGPT-User, GPTBot,\n"
        "# Claude-SearchBot, Claude-User, ClaudeBot and PerplexityBot.\n"
        "User-agent: *\nAllow: /\n\n"
        f"Sitemap: {ORIGIN}/sitemap.xml\n")


if __name__ == "__main__":
    for p in PAGES:
        if (SRC / (p["src"] + ".html")).exists():
            print("wrote", render(p).relative_to(OUT))
        else:
            print("skip (no source yet)", p["src"])
    sitemap()
    llms()
    robots()
