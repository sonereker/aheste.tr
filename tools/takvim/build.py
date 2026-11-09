# /// script
# requires-python = ">=3.10"
# dependencies = ["ephem>=4.1", "jinja2>=3.1"]
# ///
"""aheste.tr/ay-takvimi bölümünü üretir.

Kullanım: uv run tools/takvim/build.py [--bugun YYYY-AA-GG]
"""

import argparse
import calendar
import datetime as dt
import hashlib
import json
import math
import pathlib
import re

import ephem
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "ay-takvimi"
DATA_OUT = ROOT / "assets" / "data"
SITE = "https://aheste.tr"
TZ = dt.timedelta(hours=3)

AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
AY_KISA = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]
AY_SLUG = ["ocak", "subat", "mart", "nisan", "mayis", "haziran", "temmuz", "agustos", "eylul", "ekim", "kasim", "aralik"]
GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]

# Tropikal burç sırası Koç'tan başlar: ateş = meyve, toprak = kök, hava = çiçek, su = yaprak.
ELEMENT_SIRASI = ["meyve", "kok", "cicek", "yaprak"] * 3
ELEMENT_AD = {"kok": "Kök", "yaprak": "Yaprak", "cicek": "Çiçek", "meyve": "Meyve"}
EVRE_AD = {"yeni": "Yeniay", "ilk": "İlk dördün", "dolun": "Dolunay", "son": "Son dördün"}
TUR_AD = {"viyol": "Viyolde tohum", "acik": "Açığa tohum", "dikim": "Dikim", "hasat": "Hasat", "bakim": "Bakım"}
EKIM_TURLERI = ("viyol", "acik", "dikim")

# Bilinen 2026–2030 tutulmalarının hepsi |enlem| < 1.43°, tutulma olmayan yeniay/dolunaylar > 1.65°.
TUTULMA_ENLEM = 1.5

TAVSIYE = {
    "meyve-b": "Meyve günü, büyüyen ay: domates, biber, fasulye gibi meyvesi yenen bitkilerin ekimi ve dikimi için en uygun gün.",
    "meyve-k": "Meyve günü, küçülen ay: meyve hasadı ve saklanacak ürünü toplamak için iyi; ekim için büyüyen ayı bekleyin.",
    "kok-b": "Kök günü: kök sebzeler ekilebilir, ama ağaç taşıma ve budama için küçülen ayı bekleyin.",
    "kok-k": "Kök günü, küçülen ay: havuç, patates, soğan, sarımsak ekimi; ağaç dikimi, taşıma ve budama için en uygun gün.",
    "yaprak-b": "Yaprak günü, büyüyen ay: marul, ıspanak, lahana ve otların ekimi ve dikimi için en uygun gün.",
    "yaprak-k": "Yaprak günü, küçülen ay: yapraklı sebzeler ekilebilir; ot temizliği, gübreleme ve sulama için iyi.",
    "cicek-b": "Çiçek günü, büyüyen ay: brokoli, karnabahar, çiçek ve şifalı bitki ekimi için en uygun gün.",
    "cicek-k": "Çiçek günü, küçülen ay: çiçek ve şifalı bitki hasadı, kurutma için iyi.",
    "engel": "Yeniay, dolunay ya da tutulma günü: ekim ve dikim yapılmaz. Toprak hazırlığı, kompost ve dinlenme günü.",
}


# ---------------------------------------------------------------- ay hesabı

def yerel(d) -> dt.datetime:
    return ephem.Date(d).datetime() + TZ


def evreler(yil):
    olaylar = []
    for ad, fn in [("yeni", ephem.next_new_moon), ("ilk", ephem.next_first_quarter_moon),
                   ("dolun", ephem.next_full_moon), ("son", ephem.next_last_quarter_moon)]:
        d = ephem.Date(f"{yil - 1}/12/01")
        while True:
            d = fn(d)
            t = yerel(d)
            if t.year > yil:
                break
            tutulma = None
            if ad in ("yeni", "dolun"):
                enlem = math.degrees(ephem.Ecliptic(ephem.Moon(d), epoch=d).lat)
                if abs(enlem) < TUTULMA_ENLEM:
                    tutulma = "Güneş tutulması" if ad == "yeni" else "Ay tutulması"
            olaylar.append({"zaman": t, "evre": ad, "tutulma": tutulma})
            d = ephem.Date(d + 1)
    olaylar.sort(key=lambda o: o["zaman"])
    return olaylar


def mevsimler(yil):
    out = []
    for ad, fn in [("İlkbahar ekinoksu", ephem.next_vernal_equinox), ("Yaz gündönümü", ephem.next_summer_solstice),
                   ("Sonbahar ekinoksu", ephem.next_autumnal_equinox), ("Kış gündönümü", ephem.next_winter_solstice)]:
        out.append((ad, yerel(fn(f"{yil}/1/1"))))
    return out


def gun_verisi(yil, olaylar):
    by_date = {o["zaman"].date(): o for o in olaylar if o["zaman"].year == yil}
    ana = [o for o in olaylar if o["evre"] in ("yeni", "dolun")]
    gunler = {}
    d = dt.date(yil, 1, 1)
    while d.year == yil:
        oglen = dt.datetime(d.year, d.month, d.day, 12)
        oglen_utc = oglen - TZ
        boylam = math.degrees(ephem.Ecliptic(ephem.Moon(oglen_utc), epoch=oglen_utc).lon)
        onceki = [o for o in ana if o["zaman"] <= oglen]
        olay = by_date.get(d)
        evre = olay["evre"] if olay else None
        tutulma = olay["tutulma"] if olay else None
        engel = evre in ("yeni", "dolun")
        g = {
            "tarih": d,
            "element": ELEMENT_SIRASI[int(boylam // 30) % 12],
            "buyuyen": onceki[-1]["evre"] == "yeni",
            "evre": evre,
            "tutulma": tutulma,
            "engel": engel,
        }
        g["tavsiye"] = TAVSIYE["engel"] if engel else TAVSIYE[f"{g['element']}-{'b' if g['buyuyen'] else 'k'}"]
        gunler[d] = g
        d += dt.timedelta(days=1)
    return gunler


# ---------------------------------------------------------------- ekim pencereleri

def ayg(s):
    m, d = map(int, s.split("-"))
    return m, d


def kayma(ifade, bolge, yil):
    m, d = ayg(bolge["son_don"] if ifade[0] == "s" else bolge["ilk_don"])
    return dt.date(yil, m, d) + dt.timedelta(weeks=int(ifade[1:]))


def yila_yansit(da, db, yil):
    """[da, db] aralığını yılın takvimine sarar; yıl sınırını aşan kısım yılın öbür ucuna düşer."""
    bas = dt.date(yil, 1, 1)
    L = 366 if calendar.isleap(yil) else 365
    oa, ob = (da - bas).days, (db - bas).days
    if ob - oa >= L - 1:
        return [(bas, dt.date(yil, 12, 31))]
    k = oa // L
    oa, ob = oa - k * L, ob - k * L
    if ob < L:
        parcalar = [(oa, ob)]
    else:
        parcalar = [(oa, L - 1), (0, ob - L)]
    return [(bas + dt.timedelta(days=a), bas + dt.timedelta(days=b)) for a, b in parcalar]


def pencereler(kalemler, bolge, yil):
    out = []
    for p in kalemler:
        tur, a, b = p[:3]
        opt = p[3] if len(p) > 3 else {}
        if bolge["slug"] in opt.get("yok", []):
            continue
        if "sadece" in opt and bolge["slug"] not in opt["sadece"]:
            continue
        da = kayma(a, bolge, yil)
        db = kayma(b, bolge, yil + 1 if (a[0] == "i" and b[0] == "s") else yil)
        # 10 günden kısa hasat penceresi, bitkinin o bölgede açık alanda yetişmediği anlamına gelir.
        if (db - da).days < (10 if tur == "hasat" else 4):
            continue
        out.append({"tur": tur, "parcalar": yila_yansit(da, db, yil)})
    return birlestir(out, yil)


def birlestir(ws, yil):
    """Aynı türdeki pencereleri yılın günleri üzerinde birleştirir; Aralık'tan Ocak'a taşan aralık tek pencere sayılır."""
    bas = dt.date(yil, 1, 1)
    L = 366 if calendar.isleap(yil) else 365
    out = []
    for tur in TUR_AD:
        gunler = [False] * L
        for w in ws:
            if w["tur"] != tur:
                continue
            for a, b in w["parcalar"]:
                for i in range((a - bas).days, (b - bas).days + 1):
                    gunler[i] = True
        if not any(gunler):
            continue
        if all(gunler):
            out.append({"tur": tur, "bas": bas, "bit": dt.date(yil, 12, 31), "parcalar": [(bas, dt.date(yil, 12, 31))]})
            continue
        kosular, i = [], 0
        while i < L:
            if gunler[i]:
                j = i
                while j + 1 < L and gunler[j + 1]:
                    j += 1
                kosular.append([i, j])
                i = j + 1
            else:
                i += 1
        sarili = None
        if len(kosular) > 1 and kosular[0][0] == 0 and kosular[-1][1] == L - 1:
            sarili = (kosular.pop(), kosular.pop(0))
        for a, b in kosular:
            da, db = bas + dt.timedelta(days=a), bas + dt.timedelta(days=b)
            out.append({"tur": tur, "bas": da, "bit": db, "parcalar": [(da, db)]})
        if sarili:
            (a1, b1), (a2, b2) = sarili
            da, db = bas + dt.timedelta(days=a1), bas + dt.timedelta(days=b2)
            out.append({"tur": tur, "bas": da, "bit": db,
                        "parcalar": [(da, bas + dt.timedelta(days=b1)), (bas, db)]})
    out.sort(key=lambda w: (list(TUR_AD).index(w["tur"]), w["bas"]))
    return out


def tarih_kisa(d):
    return f"{d.day} {AY_KISA[d.month - 1]}"


def aralik_metni(w):
    return f"{tarih_kisa(w['bas'])} – {tarih_kisa(w['bit'])}"


def uygun_gunler(w, gunler, kural):
    """kural: ('element', 'meyve', 'buyuyen') ya da ('evre', None, 'kuculen')."""
    _, element, evre = kural
    aday, yedek = [], []
    for a, b in w["parcalar"]:
        d = a
        while d <= b:
            g = gunler.get(d)
            if g and not g["engel"]:
                evre_ok = g["buyuyen"] == (evre == "buyuyen")
                element_ok = element is None or g["element"] == element
                if element_ok and evre_ok:
                    aday.append(d)
                elif element is not None and element_ok:
                    yedek.append(d)
            d += dt.timedelta(days=1)
    return sorted(aday), sorted(yedek)


def gun_listesi(tarihler):
    gruplar = {}
    for d in tarihler:
        gruplar.setdefault(d.month, []).append(d.day)
    return [{"ay": AYLAR[m - 1], "gunler": ", ".join(map(str, g))} for m, g in sorted(gruplar.items())]


def bitki_kurali(b):
    return ("element", b["element"], "kuculen" if b["element"] == "kok" else "buyuyen")


# ---------------------------------------------------------------- sunum yardımcıları

def gantt_cubuklari(ws, yil):
    L = 366 if calendar.isleap(yil) else 365
    iki_serit = any(w["tur"] in ("viyol", "acik") for w in ws) and any(w["tur"] not in ("viyol", "acik") for w in ws)
    out = []
    for w in ws:
        serit = ("ust" if w["tur"] in ("viyol", "acik") else "alt") if iki_serit else "tek"
        for a, b in w["parcalar"]:
            sol = (a.timetuple().tm_yday - 1) / L * 100
            gen = ((b - a).days + 1) / L * 100
            out.append({"tur": w["tur"], "serit": serit, "sol": f"{sol:.2f}", "gen": f"{gen:.2f}",
                        "etiket": f"{TUR_AD[w['tur']]}: {aralik_metni(w)}"})
    return out


def ay_basliklari(yil):
    L = 366 if calendar.isleap(yil) else 365
    out = []
    for m in range(1, 13):
        a = dt.date(yil, m, 1).timetuple().tm_yday - 1
        n = calendar.monthrange(yil, m)[1]
        out.append({"ad": AYLAR[m - 1], "kisa": AY_KISA[m - 1], "sol": f"{a / L * 100:.2f}", "gen": f"{n / L * 100:.2f}"})
    return out


def isaret(yil, ay_gun, metin):
    L = 366 if calendar.isleap(yil) else 365
    m, d = ayg(ay_gun)
    return {"sol": f"{(dt.date(yil, m, d).timetuple().tm_yday - 1) / L * 100:.2f}", "metin": metin}


def ay_karti(yil, ay, gunler):
    ilk_gun, n = calendar.monthrange(yil, ay)
    hucreler = []
    for gun in range(1, n + 1):
        g = gunler[dt.date(yil, ay, gun)]
        d = g["tarih"]
        siniflar = ["g", f"e-{g['element']}", "b" if g["buyuyen"] else "k"]
        if g["engel"]:
            siniflar.append("yok")
        if g["tutulma"]:
            siniflar.append("tut")
        parcalar = [f"{gun} {AYLAR[ay - 1]} {GUNLER[d.weekday()]}"]
        if g["evre"]:
            parcalar.append(EVRE_AD[g["evre"]])
        if g["tutulma"]:
            parcalar.append(g["tutulma"])
        parcalar.append(f"{ELEMENT_AD[g['element']].lower()} günü")
        parcalar.append("büyüyen ay" if g["buyuyen"] else "küçülen ay")
        hucreler.append({"gun": gun, "iso": d.isoformat(), "sinif": " ".join(siniflar), "evre": g["evre"],
                         "aria": ", ".join(parcalar)})
    return {"yil": yil, "ay": ay, "ad": AYLAR[ay - 1], "slug": AY_SLUG[ay - 1], "bos": ilk_gun, "hucreler": hucreler,
            "url": f"/ay-takvimi/{yil}/{AY_SLUG[ay - 1]}/"}


def slugla(s):
    tablo = str.maketrans("çğıöşüâîûÇĞİÖŞÜ", "cgiosuaiucgiosu")
    return re.sub(r"[^a-z0-9]+", "-", s.translate(tablo).lower()).strip("-")


# ---------------------------------------------------------------- üretim

class Uretici:
    def __init__(self, bugun):
        self.bugun = bugun
        self.aktif = bugun.year + 1 if bugun.month >= 11 else bugun.year
        self.yillar = [bugun.year, bugun.year + 1]
        veri = json.loads((HERE / "data" / "bitkiler.json").read_text())
        self.gruplar = veri["gruplar"]
        self.bitkiler = veri["bitkiler"]
        self.agac = veri["agac"]
        self.bolgeler = json.loads((HERE / "data" / "bolgeler.json").read_text())
        self.halk = json.loads((HERE / "data" / "halk_takvimi.json").read_text())
        self.bilgiler = json.loads((HERE / "data" / "bilgiler.json").read_text())
        for b in self.bolgeler:
            b["son_don_metin"] = "~" + tarih_kisa(dt.date(2027, *ayg(b["son_don"])))
            b["ilk_don_metin"] = b.get("ilk_don_etiket") or "~" + tarih_kisa(dt.date(2027, *ayg(b["ilk_don"])))
        self.ay = {}
        for y in sorted(set(self.yillar + [self.aktif])):
            olaylar = evreler(y)
            self.ay[y] = {"olaylar": olaylar, "gunler": gun_verisi(y, olaylar), "mevsimler": mevsimler(y)}
        self.env = Environment(loader=FileSystemLoader(HERE / "templates"), autoescape=select_autoescape(["html"]),
                               trim_blocks=True, lstrip_blocks=True)
        self.sayfalar = []

    # ------------------------------------------------ ortak bağlam
    def ortak(self):
        surum = hashlib.sha1(b"".join((ROOT / "assets" / p).read_bytes() for p in ("css/takvim.css", "js/takvim.js"))).hexdigest()[:8]
        return {"site": SITE, "surum": surum, "aktif": self.aktif, "bolgeler": self.bolgeler, "bitkiler": self.bitkiler,
                "gruplar": self.gruplar, "agac": self.agac, "AYLAR": AYLAR, "AY_SLUG": AY_SLUG, "TUR_AD": TUR_AD,
                "ELEMENT_AD": ELEMENT_AD, "EVRE_AD": EVRE_AD, "guncelleme": self.bugun}

    def yaz(self, url, sablon, baslik, aciklama, kirinti, ld_ek=(), **ctx):
        yol = ROOT / url.strip("/") / "index.html"
        yol.parent.mkdir(parents=True, exist_ok=True)
        ld = [{"@context": "https://schema.org", "@type": "BreadcrumbList",
               "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": ad, "item": SITE + u}
                                   for i, (ad, u) in enumerate(kirinti)]}, *ld_ek]
        ld_metin = json.dumps(ld if len(ld) > 1 else ld[0], ensure_ascii=False).replace("</", "<\\/")
        html = self.env.get_template(sablon).render(
            **self.ortak(), url=url, baslik=baslik, aciklama=aciklama, kirinti=kirinti, ld=ld_metin, **ctx)
        yol.write_text(html)
        self.sayfalar.append(url)

    # ------------------------------------------------ bölge × bitki hesapları
    def bitki_pencereleri(self, bitki, bolge, yil):
        return pencereler(bitki["pencere"], bolge, yil)

    def gantt(self, bolge, yil):
        satirlar = []
        for grup in self.gruplar:
            rows = []
            for b in [b for b in self.bitkiler if b["grup"] == grup["slug"]]:
                ws = self.bitki_pencereleri(b, bolge, yil)
                rows.append({"ad": b["ad"], "url": f"/ay-takvimi/{b['slug']}/", "cubuklar": gantt_cubuklari(ws, yil),
                             "eksik": not any(w["tur"] == "hasat" for w in ws)})
            satirlar.append({"ad": grup["ad"], "satirlar": rows})
        rows = []
        for a in self.agac:
            ws = pencereler(a["pencere"], bolge, yil)
            rows.append({"ad": a["ad"], "url": f"/ay-takvimi/agac-dikimi/#{a['slug']}", "cubuklar": gantt_cubuklari(ws, yil),
                         "eksik": False})
        satirlar.append({"ad": "Ağaç ve fidan", "satirlar": rows})
        return {"aylar": ay_basliklari(yil), "gruplar": satirlar,
                "isaretler": [isaret(yil, bolge["son_don"], f"son don {bolge['son_don_metin']}"),
                              isaret(yil, "05-06", "Hıdırellez"),
                              *([] if bolge.get("ilk_don_etiket") else [isaret(yil, bolge["ilk_don"], f"ilk don {bolge['ilk_don_metin']}")])]}

    def ay_isleri(self, bolge, yil, ay):
        """Belirli bir ayda bölgede yapılacak işler: {tur: [{ad, url}]}."""
        a = dt.date(yil, ay, 1)
        b = dt.date(yil, ay, calendar.monthrange(yil, ay)[1])
        isler = {t: [] for t in TUR_AD if t != "bakim"}
        for bitki in self.bitkiler:
            for w in self.bitki_pencereleri(bitki, bolge, yil):
                if any(p0 <= b and p1 >= a for p0, p1 in w["parcalar"]):
                    kayit = {"ad": bitki["ad"], "url": f"/ay-takvimi/{bitki['slug']}/"}
                    if kayit not in isler[w["tur"]]:
                        isler[w["tur"]].append(kayit)
        agac = []
        for t in self.agac:
            for w in pencereler(t["pencere"], bolge, yil):
                if any(p0 <= b and p1 >= a for p0, p1 in w["parcalar"]):
                    agac.append({"ad": t["ad"], "url": f"/ay-takvimi/agac-dikimi/#{t['slug']}"})
                    break
        return {"isler": [(TUR_AD[t], v) for t, v in isler.items() if v], "agac": agac}

    def halk_olaylari(self, yil):
        out = []
        for h in self.halk:
            if "etiket" in h:
                out.append({"sira": dt.date(yil, *ayg(h["sira"])), "tarih": h["etiket"], "ad": h["ad"], "aciklama": h["aciklama"], "tur": "halk"})
                continue
            bas = dt.date(yil, *ayg(h["bas"]))
            if "bit" in h:
                bit = dt.date(yil, *ayg(h["bit"]))
                if bit < bas:
                    out.append({"sira": dt.date(yil, 1, 1), "tarih": f"{tarih_kisa(dt.date(yil - 1, *ayg(h['bas'])))} {yil - 1} – {tarih_kisa(bit)}",
                                "ad": h["ad"], "aciklama": h["aciklama"], "tur": "halk"})
                    out.append({"sira": bas, "tarih": tarih_kisa(bas), "ad": f"{h['ad']} başlar", "aciklama": h["aciklama"], "tur": "halk"})
                else:
                    out.append({"sira": bas, "tarih": f"{tarih_kisa(bas)} – {tarih_kisa(bit)}", "ad": h["ad"], "aciklama": h["aciklama"], "tur": "halk"})
            else:
                out.append({"sira": bas, "tarih": tarih_kisa(bas), "ad": h["ad"], "aciklama": h["aciklama"], "tur": "halk"})
        aciklamalar = {
            "İlkbahar ekinoksu": "Gece ile gündüz eşitlenir; astronomik ilkbahar başlar.",
            "Yaz gündönümü": "Yılın en uzun günü; astronomik yaz başlar.",
            "Sonbahar ekinoksu": "Gece ile gündüz yeniden eşitlenir; kışlık ekimlerin zamanı gelir.",
            "Kış gündönümü": "Yılın en uzun gecesi; Erbain başlar.",
        }
        for ad, t in self.ay[yil]["mevsimler"]:
            out.append({"sira": t.date(), "tarih": f"{tarih_kisa(t)} · {t:%H:%M}", "ad": ad, "aciklama": aciklamalar[ad], "tur": "gok"})
        for o in self.ay[yil]["olaylar"]:
            if o["tutulma"] and o["zaman"].year == yil:
                out.append({"sira": o["zaman"].date(), "tarih": f"{tarih_kisa(o['zaman'])} · {o['zaman']:%H:%M}", "ad": o["tutulma"],
                            "aciklama": "Ay takvimine göre tutulma günü ekim ve dikim yapılmaz. Türkiye'den görünüp görünmemesi tutulmanın yoluna bağlıdır.",
                            "tur": "tutulma"})
        out.sort(key=lambda x: x["sira"])
        return out

    # ------------------------------------------------ sayfalar
    def sayfa_hub(self):
        y = self.aktif
        aylar = [ay_karti(y, m, self.ay[y]["gunler"]) for m in range(1, 13)]
        yillar = sorted({int(p.name) for p in OUT.glob("[0-9][0-9][0-9][0-9]") if p.is_dir()} | set(self.yillar))
        self.yaz("/ay-takvimi/", "hub.html",
                 f"Ay Takvimi {y}: Ekim Dikim Takvimi ve Bugünün Ay Günü · Âheste",
                 f"{y} ekim dikim ay takvimi: bugün ay hangi evrede, hangi gün ne ekilir, ne dikilir? 7 bölgeye göre sebze ekim çizelgesi, ağaç dikimi ve önemli tarım günleri.",
                 [("Ay Takvimi", "/ay-takvimi/")],
                 yil=y, aylar=aylar, yillar=yillar)

    def sayfa_yil(self, y):
        aylar = [ay_karti(y, m, self.ay[y]["gunler"]) for m in range(1, 13)]
        ana = [o for o in self.ay[y]["olaylar"] if o["evre"] in ("yeni", "dolun") and o["zaman"].year == y]
        self.yaz(f"/ay-takvimi/{y}/", "yil.html",
                 f"{y} Ay Takvimi: Ekim, Dikim ve Budama Günleri · Âheste",
                 f"{y} ay takvimi: her gün için ay evresi, kök, yaprak, çiçek ve meyve günleri. Hangi gün ekim yapılır, hangi gün yapılmaz; {y} yeniay ve dolunay tarihleri.",
                 [("Ay Takvimi", "/ay-takvimi/"), (f"{y}", f"/ay-takvimi/{y}/")],
                 yil=y, aylar=aylar, ana=ana)

    def sayfa_ay(self, y, m):
        gunler = self.ay[y]["gunler"]
        kart = ay_karti(y, m, gunler)
        liste = []
        for d in sorted(k for k in gunler if k.month == m):
            g = gunler[d]
            liste.append({"tarih": d, "gun": d.day, "hafta": GUNLER[d.weekday()], "element": g["element"],
                          "element_ad": ELEMENT_AD[g["element"]], "buyuyen": g["buyuyen"], "evre": g["evre"],
                          "tutulma": g["tutulma"], "engel": g["engel"], "tavsiye": g["tavsiye"]})
        olaylar = [o for o in self.ay[y]["olaylar"] if o["zaman"].year == y and o["zaman"].month == m]
        onemli = [h for h in self.halk_olaylari(y) if h["sira"].month == m and h["sira"].year == y]
        onceki = (y, m - 1) if m > 1 else (y - 1, 12)
        sonraki = (y, m + 1) if m < 12 else (y + 1, 1)
        var = lambda t: t[0] in self.yillar or (OUT / str(t[0])).is_dir()
        ad = AYLAR[m - 1]
        self.yaz(f"/ay-takvimi/{y}/{AY_SLUG[m - 1]}/", "ay.html",
                 f"{ad} {y} Ay Takvimi: {ad} Ayında Ne Ekilir, Ne Dikilir? · Âheste",
                 f"{ad} {y} ay takvimi gün gün: ay evresi, kök, yaprak, çiçek ve meyve günleri. {ad} ayında bölgelere göre hangi sebzeler ekilir, dikilir ve hasat edilir?",
                 [("Ay Takvimi", "/ay-takvimi/"), (f"{y}", f"/ay-takvimi/{y}/"), (ad, f"/ay-takvimi/{y}/{AY_SLUG[m - 1]}/")],
                 yil=y, ay=m, ay_ad=ad, kart=kart, liste=liste, olaylar=olaylar, onemli=onemli,
                 isler={b["slug"]: self.ay_isleri(b, y, m) for b in self.bolgeler},
                 onceki={"url": f"/ay-takvimi/{onceki[0]}/{AY_SLUG[onceki[1] - 1]}/", "ad": f"{AYLAR[onceki[1] - 1]} {onceki[0]}"} if var(onceki) else None,
                 sonraki={"url": f"/ay-takvimi/{sonraki[0]}/{AY_SLUG[sonraki[1] - 1]}/", "ad": f"{AYLAR[sonraki[1] - 1]} {sonraki[0]}"} if var(sonraki) else None)

    def sayfa_onemli(self, y):
        ana = [o for o in self.ay[y]["olaylar"] if o["evre"] in ("yeni", "dolun") and o["zaman"].year == y]
        self.yaz(f"/ay-takvimi/{y}/onemli-gunler/", "onemli.html",
                 f"{y} Cemre, Hıdırellez ve Önemli Tarım Günleri · Âheste",
                 f"Cemre {y}'de ne zaman düşer? Hıdırellez, Kasım günü, Erbain, Hamsin, ekinoks ve gündönümü tarihleri, {y} tutulmaları, yeniay ve dolunay tarihleri.",
                 [("Ay Takvimi", "/ay-takvimi/"), (f"{y}", f"/ay-takvimi/{y}/"), ("Önemli günler", f"/ay-takvimi/{y}/onemli-gunler/")],
                 yil=y, olaylar=self.halk_olaylari(y), ana=ana)

    def sayfa_bolge(self, bolge):
        y = self.aktif
        self.yaz(f"/ay-takvimi/{bolge['slug']}/", "bolge.html",
                 f"{bolge['ad']} Bölgesi Ekim Dikim Takvimi: Ne Zaman Ne Ekilir? · Âheste",
                 f"{bolge['ad']} bölgesinde sebze tohumu, fide ve fidan ne zaman ekilir, dikilir, hasat edilir? Ay ay ekim çizelgesi, son ve ilk don tarihleri ve {y} ay takvimi.",
                 [("Ay Takvimi", "/ay-takvimi/"), (f"{bolge['ad']} Bölgesi", f"/ay-takvimi/{bolge['slug']}/")],
                 yil=y, bolge=bolge, gantt=self.gantt(bolge, y), govde_bolge=bolge["slug"],
                 aylik=[{"ad": AYLAR[m - 1], "slug": AY_SLUG[m - 1], **self.ay_isleri(bolge, y, m)} for m in range(1, 13)])

    def sayfa_bitki(self, bitki):
        y = self.aktif
        gunler = self.ay[y]["gunler"]
        kural = bitki_kurali(bitki)
        bolge_veri = []
        for bolge in self.bolgeler:
            ws = self.bitki_pencereleri(bitki, bolge, y)
            uygun = []
            for w in ws:
                if w["tur"] not in EKIM_TURLERI:
                    continue
                aday, yedek = uygun_gunler(w, gunler, kural)
                uygun.append({"tur": TUR_AD[w["tur"]], "aralik": aralik_metni(w),
                              "gunler": gun_listesi(aday or yedek), "yedek": not aday and bool(yedek)})
            bolge_veri.append({"bolge": bolge, "pencereler": [{"tur": TUR_AD[w["tur"]], "aralik": aralik_metni(w)} for w in ws],
                               "cubuklar": gantt_cubuklari(ws, y), "uygun": uygun,
                               "eksik": not any(w["tur"] == "hasat" for w in ws)})
        marmara = next(v for v in bolge_veri if v["bolge"]["slug"] == "marmara")
        ozet = "; ".join(f"{p['tur'].lower()} {p['aralik']}" for p in marmara["pencereler"] if p["tur"] != "Hasat")
        sss = [
            {"s": f"{bitki['ad']} ne zaman ekilir?",
             "c": f"Marmara'da {ozet}. Diğer bölgelerde tarihler son ve ilk don tarihlerine göre kayar; bu sayfada 7 bölgenin tarihleri ve uygun ay günleri var."},
            {"s": f"{bitki['ad']} hangi ay gününde ekilir?",
             "c": f"Ay takvimine göre {bitki['ad'].lower()} bir {ELEMENT_AD[bitki['element']].lower()} bitkisidir; {ELEMENT_AD[bitki['element']].lower()} günlerinde ve "
                  f"{'küçülen' if kural[2] == 'kuculen' else 'büyüyen'} ayda ekilmesi önerilir. Yeniay, dolunay ve tutulma günlerinde ekim yapılmaz."},
        ]
        bilgi = self.bilgiler[bitki["slug"]]
        sss.append({"s": f"{bitki['ad']} kaç cm derine ekilir, aralığı ne olmalı?",
                    "c": f"Ekim derinliği: {bilgi['derinlik']}. Sıra arası ve sıra üzeri: {bilgi['aralik']}. "
                         f"Çimlenme: {bilgi['cimlenme']}. Hasat: {bilgi['hasat']}."})
        benzer = [b for b in self.bitkiler if b["grup"] == bitki["grup"] and b["slug"] != bitki["slug"]]
        self.yaz(f"/ay-takvimi/{bitki['slug']}/", "bitki.html",
                 f"{bitki['ad']} Ne Zaman Ekilir? Bölgelere Göre Ekim, Dikim ve Hasat · Âheste",
                 f"{bitki['ad']} ne zaman ekilir, fidesi ne zaman dikilir? Marmara, Ege, Akdeniz, İç Anadolu, Karadeniz, Doğu ve Güneydoğu Anadolu için ekim tarihleri ve {y} ay takvimine göre uygun günler.",
                 [("Ay Takvimi", "/ay-takvimi/"), (bitki["ad"], f"/ay-takvimi/{bitki['slug']}/")],
                 ld_ek=[{"@context": "https://schema.org", "@type": "FAQPage",
                         "mainEntity": [{"@type": "Question", "name": q["s"],
                                         "acceptedAnswer": {"@type": "Answer", "text": q["c"]}} for q in sss]}],
                 yil=y, bitki=bitki, bilgi=bilgi, bolge_veri=bolge_veri, aylar_baslik=ay_basliklari(y), sss=sss, benzer=benzer,
                 kural_metni=f"{ELEMENT_AD[bitki['element']]} günü · {'küçülen' if kural[2] == 'kuculen' else 'büyüyen'} ay")

    def sayfa_agac(self):
        y = self.aktif
        gunler = self.ay[y]["gunler"]
        isler = []
        for a in self.agac:
            satirlar = []
            for bolge in self.bolgeler:
                ws = pencereler(a["pencere"], bolge, y)
                tarihler = []
                for w in ws:
                    aday, _ = uygun_gunler(w, gunler, ("evre", None, a["evre"]))
                    tarihler += aday
                satirlar.append({"bolge": bolge, "araliklar": [aralik_metni(w) for w in ws],
                                 "cubuklar": gantt_cubuklari(ws, y), "gunler": gun_listesi(sorted(set(tarihler)))})
            isler.append({**a, "satirlar": satirlar, "evre_ad": "küçülen" if a["evre"] == "kuculen" else "büyüyen"})
        self.yaz("/ay-takvimi/agac-dikimi/", "agac.html",
                 "Fidan Ne Zaman Dikilir? Ağaç Taşıma, Budama ve Aşı Zamanı · Âheste",
                 f"Meyve fidanı ne zaman dikilir, ağaç ne zaman taşınır ve budanır, aşı ne zaman yapılır? 7 bölgeye göre tarihler ve {y} ay takvimine göre uygun günler.",
                 [("Ay Takvimi", "/ay-takvimi/"), ("Ağaç ve fidan", "/ay-takvimi/agac-dikimi/")],
                 yil=y, isler=isler, aylar_baslik=ay_basliklari(y))

    # ------------------------------------------------ JS verisi, site haritası
    def json_yaz(self):
        DATA_OUT.mkdir(parents=True, exist_ok=True)
        for y in self.yillar:
            gun = {}
            for d, g in self.ay[y]["gunler"].items():
                kod = g["element"][0] + ("b" if g["buyuyen"] else "k") + ({"yeni": "Y", "ilk": "I", "dolun": "D", "son": "S"}.get(g["evre"], "-")) + ("t" if g["tutulma"] else "-")
                gun[f"{d:%m-%d}"] = kod
            (DATA_OUT / f"ay-{y}.json").write_text(json.dumps({"yil": y, "gun": gun, "tavsiye": TAVSIYE}, ensure_ascii=False, separators=(",", ":")))
        y = self.aktif
        isler = {}
        for bolge in self.bolgeler:
            isler[bolge["slug"]] = {}
            for b in self.bitkiler:
                isler[bolge["slug"]][b["slug"]] = [[w["tur"], f"{p0:%m-%d}", f"{p1:%m-%d}"]
                                                   for w in self.bitki_pencereleri(b, bolge, y) for p0, p1 in w["parcalar"]]
        ekim = {"yil": y, "turler": TUR_AD,
                "bolgeler": [{"slug": b["slug"], "ad": b["ad"]} for b in self.bolgeler],
                "bitkiler": {b["slug"]: {"ad": b["ad"], "element": b["element"]} for b in self.bitkiler},
                "isler": isler}
        (DATA_OUT / "ekim.json").write_text(json.dumps(ekim, ensure_ascii=False, separators=(",", ":")))

    def site_haritasi(self):
        sabit = ["/", "/location.html", "/garden.html", "/trees.html", "/cafe.html", "/shop.html"]
        var_olan = sorted({"/" + str(p.parent.relative_to(ROOT)) + "/" for p in OUT.rglob("index.html")})
        urls = sabit + var_olan
        satirlar = "\n".join(f"  <url><loc>{SITE}{u}</loc></url>" for u in urls)
        (ROOT / "sitemap.xml").write_text(
            f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{satirlar}\n</urlset>\n')
        (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")

    def calistir(self):
        self.sayfa_hub()
        for y in self.yillar:
            self.sayfa_yil(y)
            self.sayfa_onemli(y)
            for m in range(1, 13):
                self.sayfa_ay(y, m)
        for b in self.bolgeler:
            self.sayfa_bolge(b)
        for b in self.bitkiler:
            self.sayfa_bitki(b)
        self.sayfa_agac()
        self.json_yaz()
        self.site_haritasi()
        print(f"{len(self.sayfalar)} sayfa üretildi · yıllar {self.yillar} · aktif yıl {self.aktif}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bugun", help="Tarih yerine geçer (YYYY-AA-GG), test için")
    args = ap.parse_args()
    bugun = dt.date.fromisoformat(args.bugun) if args.bugun else (dt.datetime.now(dt.timezone.utc) + TZ).date()
    Uretici(bugun).calistir()


if __name__ == "__main__":
    main()
