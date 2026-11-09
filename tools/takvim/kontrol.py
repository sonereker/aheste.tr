"""Üretilen sayfalardaki iç bağlantıları, görselleri ve site haritasını denetler.

Kullanım: python3 tools/takvim/kontrol.py
"""

import pathlib
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urldefrag, urlparse

ROOT = pathlib.Path(__file__).resolve().parents[2]


class Baglantilar(HTMLParser):
    def __init__(self):
        super().__init__()
        self.adresler, self.idler = [], set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.idler.add(a["id"])
        for anahtar in ("href", "src"):
            if anahtar in a:
                self.adresler.append(a[anahtar])


def dosya(sayfa: pathlib.Path, adres: str):
    yol = urlparse(adres).path
    hedef = ROOT / yol.lstrip("/") if yol.startswith("/") else sayfa.parent / yol
    if yol.endswith("/") or hedef.is_dir():
        hedef = hedef / "index.html"
    return hedef


def main():
    sayfalar = list((ROOT / "ay-takvimi").rglob("index.html")) + list(ROOT.glob("*.html"))
    ayrisan = {}
    for s in sayfalar:
        p = Baglantilar()
        p.feed(s.read_text())
        ayrisan[s] = p
    hatalar = []
    for s, p in ayrisan.items():
        for adres in p.adresler:
            if re.match(r"^(https?:|mailto:|#$)", adres):
                continue
            yol, parca = urldefrag(adres)
            hedef = s if not yol else dosya(s, yol)
            if not hedef.exists():
                hatalar.append(f"{s.relative_to(ROOT)} → {adres} (dosya yok)")
            elif parca and hedef.suffix == ".html" and hedef in ayrisan and parca not in ayrisan[hedef].idler:
                hatalar.append(f"{s.relative_to(ROOT)} → {adres} (#{parca} yok)")
    harita = (ROOT / "sitemap.xml").read_text()
    for loc in re.findall(r"<loc>https://aheste\.tr(.*?)</loc>", harita):
        if not dosya(ROOT / "index.html", loc).exists():
            hatalar.append(f"sitemap.xml → {loc} (dosya yok)")
    for h in sorted(set(hatalar)):
        print(h)
    print(f"{len(sayfalar)} sayfa denetlendi, {len(set(hatalar))} sorun")
    sys.exit(1 if hatalar else 0)


if __name__ == "__main__":
    main()
