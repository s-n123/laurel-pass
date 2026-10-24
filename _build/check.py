"""Static checks for the built site. Usage: python3 -I check.py <repo_dir>"""
import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(sys.argv[1])
ORIGIN = re.search(r'^ORIGIN = "(.*)"$', (Path(__file__).parent / "build.py").read_text(), re.M).group(1)
problems = []

# Wording the positioning rules out. Checked in everything a visitor or crawler can read,
# including meta tags, JSON-LD, llms.txt, robots.txt and the sitemap. vercel.json is exempt:
# its redirects must name the old URLs.
BANNED = [r"\bDWI\b", r"\bDUI\b", r"criminal", r"personal injury", r"\bacquir", r"\bacquisition",
          r"private equity", r"\bMSO\b", r"roll-?up", r"\bpremier\b", r"\bpremium\b", r"\bleading\b",
          r"\bcheaper\b", r"platform play", r"\bour (attorneys|lawyers|law firms?|team)\b",
          r"we handle cases", r"paid at closing", r"cash at closing", r"\bmultiples?\b", r"laurel\s?pass",
          r"spencer", r"\bM&(amp;)?A\b", r"large-firm",
          r"\bflat[- ]fee", r"\bretainer", r"\bSBA\b", r"letter of intent", r"\bLOI\b", r"one business day",
          r"90 to 120", r"\$500K", r"\$5M", r"fee revenue", r"\bbrokers?\b", r"\bfunds?\b", r"\btraffic\b",
          r"misdemeanor", r"bankruptcy", r"divorce", r"\bwe buy\b", r"\bat closing\b", r"formspree",
          r"how-a-sale-works", r"what-is-my-practice-worth", r"\bguides?\b", r"(?<!_vercel/)insights"]
DISCLOSURE_RE = r"\S+(?: \S+)*? LLC is not a law firm and does not provide legal services\."


def banned_in(name, content):
    for pat in BANNED:
        for m in re.finditer(pat, content, re.I):
            problems.append(f"{name}: banned or stale wording '{m.group(0)}'")


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.ids, self.text, self.ld = [], set(), [], []
        self._skip = 0
        self._ld = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "a" and "href" in a:
            self.links.append(a["href"])
        if tag == "script":
            self._skip += 1
            if a.get("type") == "application/ld+json":
                self._ld = []
        if tag in ("style", "head"):
            self._skip += 1

    def handle_endtag(self, tag):
        if tag == "script":
            self._skip -= 1
            if self._ld is not None:
                self.ld.append("".join(self._ld))
                self._ld = None
        if tag in ("style", "head"):
            self._skip -= 1

    def handle_data(self, data):
        if self._ld is not None:
            self._ld.append(data)
        elif not self._skip:
            self.text.append(data)


def url_to_file(path):
    path = path.split("#")[0].split("?")[0]
    if path in ("", "/"):
        return ROOT / "index.html"
    f = ROOT / path.lstrip("/")
    if f.suffix:
        return f
    return f.with_suffix(".html")


html_files = sorted(p for p in ROOT.rglob("*.html") if ".git" not in p.parts and "_build" not in p.parts)
titles, descs = {}, {}
parsed = {}
for f in html_files:
    src = f.read_text()
    pg = Page()
    pg.feed(src)
    parsed[f] = (src, pg)
    text = re.sub(r"\s+", " ", "".join(pg.text))
    banned_in(f.name, src)
    llc = len(re.findall(r"\bLLC\b", src))
    if llc != 1 or not re.search(r"<footer.*" + DISCLOSURE_RE, src, re.S):
        problems.append(f"{f.name}: 'LLC' should appear once, in the footer disclosure (found {llc})")
    t = re.search(r"<title>(.*?)</title>", src).group(1)
    d = re.search(r'<meta name="description" content="(.*?)">', src).group(1)
    titles.setdefault(t, []).append(f.name)
    descs.setdefault(d, []).append(f.name)
    if len(html.unescape(t)) > 70:
        problems.append(f"{f.name}: title {len(html.unescape(t))} chars")
    if len(html.unescape(d)) > 160:
        problems.append(f"{f.name}: description {len(html.unescape(d))} chars")
    # JSON-LD
    for blob in pg.ld:
        try:
            data = json.loads(blob)
        except Exception as e:
            problems.append(f"{f.name}: JSON-LD parse error {e}")
            continue
        for node in data.get("@graph", [data]):
            if node["@type"] == "Organization":
                if node["description"] not in text:
                    problems.append(f"{f.name}: Organization description not in visible text")
                if node["email"] not in text:
                    problems.append(f"{f.name}: Organization email not in visible text")
            if node["@type"] == "FAQPage":
                for q in node["mainEntity"]:
                    if q["name"] not in text or q["acceptedAnswer"]["text"] not in text:
                        problems.append(f"{f.name}: FAQ entry not in visible text: {q['name']}")
                print(f"{f.name}: {len(node['mainEntity'])} FAQ entries")
    # Links
    for href in pg.links:
        if href.startswith(("mailto:", "http://", "https://")):
            continue
        if href.startswith("#"):
            if href[1:] not in pg.ids:
                problems.append(f"{f.name}: missing anchor {href}")
            continue
        target = url_to_file(href)
        if not target.exists():
            problems.append(f"{f.name}: broken link {href}")
        elif "#" in href:
            anchor = href.split("#", 1)[1]
            tsrc, tpg = parsed.get(target) or (None, None)
            if tpg is None:
                tp = Page(); tp.feed(target.read_text()); ids = tp.ids
            else:
                ids = tpg.ids
            if anchor not in ids:
                problems.append(f"{f.name}: missing anchor {href}")

for k, v in titles.items():
    if len(v) > 1:
        problems.append(f"duplicate title in {v}")
for k, v in descs.items():
    if len(v) > 1:
        problems.append(f"duplicate description in {v}")

# Sitemap vs canonicals
sm = (ROOT / "sitemap.xml").read_text()
locs = set(re.findall(r"<loc>(.*?)</loc>", sm))
canons = set()
for f, (src, _) in parsed.items():
    m = re.search(r'<link rel="canonical" href="(.*?)">', src)
    if m:
        canons.add(m.group(1))
        if not url_to_file(m.group(1)[len(ORIGIN):]).exists():
            problems.append(f"{f.name}: canonical points nowhere")
if locs != canons:
    problems.append(f"sitemap/canonical mismatch: only sitemap {locs - canons}, only canonical {canons - locs}")

if f"Sitemap: {ORIGIN}/sitemap.xml" not in (ROOT / "robots.txt").read_text():
    problems.append("robots.txt: Sitemap line does not match ORIGIN")

for extra in ("llms.txt", "robots.txt", "sitemap.xml"):
    banned_in(extra, (ROOT / extra).read_text())

print(f"{len(html_files)} pages, {len(locs)} sitemap URLs")
print("\n".join(problems) if problems else "No problems found")
left = sorted({m for f in html_files for m in re.findall(r"\[(?:ENTITY NAME|DOMAIN|CONTACT EMAIL|FORM ENDPOINT OR INBOX)\]", f.read_text())})
if left:
    print("Placeholders left in the built pages:", ", ".join(left))
    sys.exit(1)
