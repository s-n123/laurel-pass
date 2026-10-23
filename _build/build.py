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

# Placeholders until the entity name, domain and contact address are final. Set each once here.
ENTITY = "[ENTITY NAME]"
ORIGIN = "https://[DOMAIN]"
EMAIL = "[CONTACT EMAIL]"
# Where the contact form sends: a form endpoint URL (e.g. Formspree) or an inbox address.
FORM_TARGET = "[FORM ENDPOINT OR INBOX]"
DISCLOSURE = (f"{ENTITY} LLC is not a law firm and does not provide legal services. The firms we "
              "work with are independently owned and operated by licensed attorneys.")
DESCRIPTION = (f"{ENTITY} is an attorney-led platform that partners with elder law, estate planning "
               "and probate firms in the New York metro area and northern New Jersey.")
PUBLISHED = "2026-10-18"

ORG = {
    "@type": "Organization",
    "@id": ORIGIN + "/#organization",
    "name": ENTITY,
    "url": ORIGIN + "/",
    "logo": ORIGIN + "/logo.png",
    "image": ORIGIN + "/og-image.png",
    "description": DESCRIPTION,
    "email": EMAIL,
    "address": {"@type": "PostalAddress", "addressLocality": "New York",
                "addressRegion": "NY", "addressCountry": "US"},
    "areaServed": ["New York City", "Nassau County, NY", "Suffolk County, NY",
                   "Westchester County, NY"],
    "knowsAbout": ["Law practice acquisitions",
                   "Sale of a law practice under New York Rule 1.17",
                   "DWI defense practices"],
}

# path: output file; url: public path; kind: website | guide | article | faq | about | page
PAGES = [
    dict(src="home", out="index.html", url="/", kind="website", modified="2026-10-23",
         title=f"Partner or Sell Your Estate Planning Practice in New York and New Jersey | {ENTITY}",
         og_title="Your practice. Your clients. A partner who'll still be there.",
         desc="Liquidity for elder law, estate planning and probate firm owners who want to keep practicing, and a structured handoff for those ready to retire. NY metro and NJ.",
         og_desc="A partner to elder law, estate planning and probate firms across the New York area and northern New Jersey.",
         cta=False),
    dict(src="how-a-sale-works", url="/how-a-sale-works", kind="guide", nav="how",
         title=f"How a Law Practice Sale Works in New York | {ENTITY}",
         desc=f"How selling your New York law practice to {ENTITY} works: the confidential first call, what we review, the letter of intent, client notices and closing."),
    dict(src="selling-a-dwi-practice-in-new-york", url="/selling-a-dwi-practice-in-new-york", kind="guide", nav="guides",
         title=f"Selling a DWI Practice in New York: A Guide for Owners | {ENTITY}",
         desc="How to sell a DWI defense practice in New York under Rule 1.17: client notice, open matters and prepaid fees, staff, timeline and choosing the right buyer."),
    dict(src="what-is-my-practice-worth", url="/what-is-my-practice-worth", kind="guide", nav="guides",
         title=f"What Is My Law Practice Worth? Valuing a Flat-Fee Practice | {ENTITY}",
         desc="What drives the value of a DWI or other flat-fee law practice, how buyers measure earnings, how payment terms change the price, and what to gather first."),
    dict(src="how-the-sale-is-taxed", url="/how-the-sale-is-taxed", kind="guide", nav="guides",
         title=f"How Is the Sale of a Law Practice Taxed? | {ENTITY}",
         desc="Questions for your accountant before you sell a law practice: price allocation and Form 8594, personal goodwill, seller notes, earnouts and transition pay."),
    dict(src="your-options", url="/your-options", kind="guide", nav="guides",
         title=f"Private Equity or a Lawyer? Your Options for Selling a New York Law Practice | {ENTITY}",
         desc="Attorney buyer, merger, broker, private equity through an MSO, or winding down: how each option works for a New York law practice owner."),
    dict(src="faq", url="/faq", kind="faq", nav="faq", modified="2026-10-23",
         title=f"FAQ: Partnering or Retiring From an Estate Planning or Elder Law Practice | {ENTITY}",
         desc="Who owns the firm, what happens to staff, client files and original wills, how price and financing work, timing, fees and confidentiality. Plain answers."),
    dict(src="about", url="/about", kind="about", nav="about", modified="2026-10-23",
         title=f"About {ENTITY} | Attorney-led partner to elder law and estate planning firms",
         desc="An attorney-led platform that partners with elder law, estate planning and probate firms in the New York metro area and northern New Jersey, and why."),
    dict(src="referral-partners", url="/referral-partners", kind="page", nav=None,
         title=f"Law Practice Buyer in New York: For Brokers, CPAs and Advisors | {ENTITY}",
         desc=f"What {ENTITY} buys, what we need for a first look, and how we treat the practice owners that brokers, CPAs and bar succession advisors introduce."),
    dict(src="insights", url="/insights", kind="page", nav="guides",
         title=f"Guides and Insights for Law Practice Owners | {ENTITY}",
         desc="Plain-English guides and dated articles for New York lawyers thinking about selling a practice: the sale process, valuation, taxes, client notice and succession."),
    dict(src="article-clients", url="/insights/what-happens-to-your-clients-when-you-sell", kind="article", nav="guides",
         title=f"What Happens to Your Clients When You Sell a New York Practice | {ENTITY}",
         desc="Under New York Rule 1.17, clients get a joint written notice, can choose other counsel, and keep their fee agreements. How that works in practice."),
    dict(src="article-firm-name", url="/insights/can-your-firm-name-stay-on-the-door", kind="article", nav="guides",
         title=f"Can Your Firm Name Stay on the Door After You Sell? | {ENTITY}",
         desc="What New York allows when a buyer wants to keep a selling lawyer's firm name, and how to plan a name change."),
    dict(src="partner", url="/partner", kind="page", nav="partner", modified="2026-10-23",
         title=f"Elder Law Practice Succession: Partner and Keep Practicing | {ENTITY}",
         desc="Own an elder law, estate planning or probate firm on Long Island, in Westchester, NYC or northern NJ? Sell a minority stake, keep practicing, get a services team."),
    dict(src="retire", url="/retire", kind="page", nav="retire", modified="2026-10-23",
         title=f"Sell Your Estate Planning, Elder Law or Probate Practice in NY or NJ | {ENTITY}",
         desc="Retiring from an estate planning, elder law or probate practice in New York or northern New Jersey? A fair purchase under the sale-of-practice rules, staff kept."),
    dict(src="contact", url="/contact", kind="page", nav=None, cta=False, modified="2026-10-23",
         title=f"Start a Confidential Conversation | {ENTITY}",
         desc="Tell us about your elder law, estate planning or probate practice. You'll hear back within two business days, and nothing is shared without an NDA."),
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
    elif kind in ("guide", "article"):
        graph.append({"@type": "Article", "@id": url + "#article", "headline": h1_of(body),
                      "description": page["desc"], "url": url, "mainEntityOfPage": url,
                      "image": ORIGIN + "/og-image.png", "inLanguage": "en-US",
                      "datePublished": page.get("published", PUBLISHED),
                      "dateModified": page.get("modified", PUBLISHED),
                      "author": {"@id": ORG["@id"]}, "publisher": {"@id": ORG["@id"]}})
    elif kind == "faq":
        graph.append({"@type": "FAQPage", "@id": url + "#faq", "url": url,
                      "mainEntity": faq_entities(body)})
    elif kind == "about":
        graph.append({"@type": "AboutPage", "@id": url + "#page", "url": url, "name": h1_of(body),
                      "about": {"@id": ORG["@id"]}})
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
<h2>Thinking about what comes next for your practice? Start with a confidential conversation.</h2>
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
<li><a href="/#how">How a conversation works</a></li>
</ul>
</div>
<div>
<h2>More</h2>
<ul>
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
    if FORM_TARGET.startswith(("https://", "http://")):
        return f' action="{FORM_TARGET}"'
    if re.fullmatch(r"[^\s@\[\]]+@[^\s@\[\]]+", FORM_TARGET):
        return f' action="mailto:{FORM_TARGET}" enctype="text/plain"'
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
        form = (SRC / "partials" / "contact-form.html").read_text().replace("{action}", form_action())
        body = body.replace("<!--CONTACT_FORM-->", form.strip())
        script += (SRC / "partials" / "contact-form-script.html").read_text().replace("{target}", FORM_TARGET)
    url = ORIGIN + page["url"]
    og_type = "article" if page["kind"] in ("guide", "article") else "website"
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
<meta property="og:image:alt" content="{ENTITY}: attorney-led law practice acquisitions in New York">
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
    groups = {"guide": [], "article": [], "rest": []}
    for p in PAGES:
        if p.get("noindex") or p["url"] == "/":
            continue
        name = p["title"].split(" | ")[0]
        line = f"- [{name}]({ORIGIN}{p['url']}): {p['desc']}"
        groups[p["kind"] if p["kind"] in groups else "rest"].append(line)
    text = f"""# {ENTITY}

> {DESCRIPTION}

{ENTITY} is an attorney-led firm that buys and runs established DWI, criminal-defense and other flat-fee practices in New York City, Long Island and Westchester. Practices stay lawyer-owned, staff and client relationships carry over, and every conversation is confidential. Most of the price is paid at closing. Contact: {EMAIL}

## Start here

- [{ENTITY}]({ORIGIN}/): Who we are, what we look for (DWI/DUI defense first, other flat-fee practices welcome; $500K–$5M in annual fees; New York City, Long Island and Westchester) and how to start a confidential conversation.

## Guides for practice owners

{chr(10).join(groups["guide"])}

## About and contact

{chr(10).join(groups["rest"])}

## Articles

{chr(10).join(groups["article"])}
"""
    (OUT / "llms.txt").write_text(text)


if __name__ == "__main__":
    for p in PAGES:
        if (SRC / (p["src"] + ".html")).exists():
            print("wrote", render(p).relative_to(OUT))
        else:
            print("skip (no source yet)", p["src"])
    sitemap()
    llms()
