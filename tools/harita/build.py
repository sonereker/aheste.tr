# /// script
# requires-python = ">=3.10"
# ///
"""location.html içindeki aday bölgeler haritasını üretir.

İl sınırları: alpers/Turkey-Maps-GeoJSON (Apache-2.0). Komşu ülkeler veride yok,
bu yüzden deniz ve komşular boyanmaz; yalnızca adlarıyla yazılır.
"""
import json
import math
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "location.html"
SOURCE = "https://raw.githubusercontent.com/alpers/Turkey-Maps-GeoJSON/8bbe6554c83c45dbe3605b470d0948f499478dbc/tr-cities.json"

LON_MIN, LON_MAX, LAT_MIN, LAT_MAX = 25.55, 31.0, 38.95, 41.75
SCALE = 200
KX = math.cos(math.radians((LAT_MIN + LAT_MAX) / 2))
WIDTH = round((LON_MAX - LON_MIN) * KX * SCALE)
HEIGHT = round((LAT_MAX - LAT_MIN) * SCALE)

CANDIDATE_PROVINCES = {"Bursa", "Çanakkale", "Yalova", "Bilecik", "Balıkesir"}

# (slug, label, province note, lon, lat, label side)
CANDIDATES = [
    ("bursa", "Bursa", None, 29.30, 40.42, "right"),
    ("canakkale", "Çanakkale", None, 26.47, 39.80, "right"),
    ("cinarcik", "Çınarcık", "Yalova", 29.12, 40.64, "left"),
    ("bilecik", "Bilecik", None, 30.01, 40.36, "right"),
    ("ayvalik", "Ayvalık", "Balıkesir", 26.69, 39.32, "right"),
]
REFERENCE = ("İstanbul", 28.98, 41.01)
SEAS = [("Karadeniz", 29.55, 41.5), ("Marmara Denizi", 27.85, 40.82), ("Ege Denizi", 25.62, 39.2)]
COUNTRIES = [("Yunanistan", 25.85, 41.05)]


def project(lon, lat):
    return (lon - LON_MIN) * KX * SCALE, (LAT_MAX - lat) * SCALE


def ring_path(ring):
    pts, last = [], None
    for lon, lat in ring:
        x, y = project(lon, lat)
        if last and math.hypot(x - last[0], y - last[1]) < 0.8:
            continue
        pts.append((x, y))
        last = (x, y)
    if len(pts) < 3:
        return ""
    return "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z"


def in_view(polygons):
    lons = [p[0] for poly in polygons for ring in poly for p in ring]
    lats = [p[1] for poly in polygons for ring in poly for p in ring]
    return min(lons) < LON_MAX and max(lons) > LON_MIN and min(lats) < LAT_MAX and max(lats) > LAT_MIN


def provinces():
    with urllib.request.urlopen(SOURCE, timeout=30) as r:
        data = json.load(r)
    out = []
    for f in sorted(data["features"], key=lambda f: f["properties"]["name"]):
        geom = f["geometry"]
        polygons = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        if not in_view(polygons):
            continue
        d = "".join(ring_path(ring) for poly in polygons for ring in poly)
        name = f["properties"]["name"]
        cls = "il aday-il" if name in CANDIDATE_PROVINCES else "il"
        out.append(f'<path class="{cls}" d="{d}"><title>{name}</title></path>')
    return out


def marker(slug, label, note, lon, lat, side):
    x, y = project(lon, lat)
    dx, anchor = (12, "start") if side == "right" else (-12, "end")
    sub = f'<text class="il-adi" x="{x + dx:.0f}" y="{y + 17:.0f}" text-anchor="{anchor}">{note}</text>' if note else ""
    return (f'<a class="aday" href="#aday-{slug}"><circle cx="{x:.1f}" cy="{y:.1f}" r="7"/>'
            f'<text x="{x + dx:.0f}" y="{y + 1:.0f}" text-anchor="{anchor}">{label}</text>{sub}</a>')


def svg():
    parts = [f'<svg class="harita" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="harita-baslik harita-aciklama">',
             '<title id="harita-baslik">Aday bölgeler haritası</title>',
             '<desc id="harita-aciklama">Kuzeybatı Türkiye. Beş aday: Bursa, Çanakkale, Çınarcık (Yalova), Bilecik ve Ayvalık (Balıkesir). Adayların illeri boyalı, İstanbul referans olarak işaretli.</desc>',
             '<g class="iller">', *provinces(), '</g>']
    parts += [f'<text class="deniz" x="{x:.0f}" y="{y:.0f}">{n}</text>' for n, x, y in ((n, *project(lo, la)) for n, lo, la in SEAS)]
    parts += [f'<text class="ulke" x="{x:.0f}" y="{y:.0f}">{n}</text>' for n, x, y in ((n, *project(lo, la)) for n, lo, la in COUNTRIES)]
    rn, rlon, rlat = REFERENCE
    rx, ry = project(rlon, rlat)
    parts.append(f'<g class="referans"><circle cx="{rx:.1f}" cy="{ry:.1f}" r="4"/><text x="{rx + 9:.0f}" y="{ry - 7:.0f}">{rn}</text></g>')
    parts += [marker(*c) for c in CANDIDATES]
    parts.append("</svg>")
    return "\n".join(parts)


def main():
    html = PAGE.read_text()
    pattern = re.compile(r"(<!-- harita:başla -->\n).*?(<!-- harita:bitir -->)", re.S)
    if not pattern.search(html):
        raise SystemExit("location.html içinde harita işaretleri yok")
    PAGE.write_text(pattern.sub(lambda m: m.group(1) + svg() + "\n" + m.group(2), html))
    print(f"harita yazıldı: {WIDTH}×{HEIGHT}")


if __name__ == "__main__":
    main()
