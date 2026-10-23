"""Static checks for the built site. Usage: python3 -I check.py <repo_dir>"""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(sys.argv[1])
ORIGIN = "https://[DOMAIN]"  # keep in step with ORIGIN in build.py
problems = []


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
    t = re.search(r"<title>(.*?)</title>", src).group(1)
    d = re.search(r'<meta name="description" content="(.*?)">', src).group(1)
    titles.setdefault(t, []).append(f.name)
    descs.setdefault(d, []).append(f.name)
    if len(d) > 165:
        problems.append(f"{f.name}: description {len(d)} chars")
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
            if node["@type"] == "Article":
                if node["headline"] not in text:
                    problems.append(f"{f.name}: headline not visible")
                canon = re.search(r'<link rel="canonical" href="(.*?)">', src).group(1)
                if node["url"] != canon:
                    problems.append(f"{f.name}: Article url {node['url']} != canonical {canon}")
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

print(f"{len(html_files)} pages, {len(locs)} sitemap URLs")
print("\n".join(problems) if problems else "No problems found")
