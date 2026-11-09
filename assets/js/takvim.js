const BOLGE_ANAHTAR = "aheste-bolge";
const AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"];
const AY_SLUG = ["ocak", "subat", "mart", "nisan", "mayis", "haziran", "temmuz", "agustos", "eylul", "ekim", "kasim", "aralik"];
const GUNLER = ["Pazar", "Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi"];
const ELEMENT = { k: ["kok", "Kök"], y: ["yaprak", "Yaprak"], c: ["cicek", "Çiçek"], m: ["meyve", "Meyve"] };
const EVRE = { Y: ["yeni", "Yeniay"], I: ["ilk", "İlk dördün"], D: ["dolun", "Dolunay"], S: ["son", "Son dördün"] };

const bugun = new Date();
const iki = n => String(n).padStart(2, "0");
const isoTarih = d => `${d.getFullYear()}-${iki(d.getMonth() + 1)}-${iki(d.getDate())}`;
const mobil = () => window.matchMedia("(max-width: 767px)").matches;

function okuBolge() {
  try { return localStorage.getItem(BOLGE_ANAHTAR); } catch { return null; }
}
function yazBolge(slug) {
  try { localStorage.setItem(BOLGE_ANAHTAR, slug); } catch { /* özel pencerede depolama kapalı olabilir */ }
}

const onbellek = {};
function veri(url) {
  onbellek[url] ??= fetch(url).then(r => (r.ok ? r.json() : null)).catch(() => null);
  return onbellek[url];
}

function gunKodu(ayVerisi, tarih) {
  const kod = ayVerisi?.gun?.[`${iki(tarih.getMonth() + 1)}-${iki(tarih.getDate())}`];
  if (!kod) return null;
  const evre = EVRE[kod[2]] || null;
  const engel = kod[2] === "Y" || kod[2] === "D";
  const element = ELEMENT[kod[0]];
  return {
    element,
    buyuyen: kod[1] === "b",
    evre,
    tutulma: kod[3] === "t",
    engel,
    tavsiye: engel ? ayVerisi.tavsiye.engel : ayVerisi.tavsiye[`${element[0]}-${kod[1]}`],
  };
}

// Ay'ın yaşına göre aydınlık kısmı çizer; yalnızca simge için, ±yarım gün yeterli.
function aySimgesi(tarih) {
  const yas = ((tarih - Date.UTC(2000, 0, 6, 18, 14)) / 864e5 / 29.530588853) % 1;
  const t = yas < 0 ? yas + 1 : yas;
  const r = 20, k = Math.cos(2 * Math.PI * t), rx = Math.abs(k) * r;
  const buyuyen = t < 0.5;
  const yay = buyuyen ? 1 : 0;
  const terminator = buyuyen ? (k > 0 ? 0 : 1) : (k > 0 ? 1 : 0);
  const yol = `M22 2 A${r} ${r} 0 0 ${yay} 22 42 A${rx.toFixed(2)} ${r} 0 0 ${terminator} 22 2Z`;
  return `<svg class="bugun-ay" viewBox="0 0 44 44" aria-hidden="true"><circle cx="22" cy="22" r="20" fill="#2b3550"/><path d="${yol}" fill="#f3de9f"/><circle cx="22" cy="22" r="20" fill="none" stroke="#1f2a44" stroke-width="1.5"/></svg>`;
}

// ---------------------------------------------------------------- bölge seçimi

function bolgeUygula(slug) {
  document.querySelectorAll("[data-bolge-sekme] [data-bolge]").forEach(b => b.setAttribute("aria-selected", String(b.dataset.bolge === slug)));
  document.querySelectorAll("[data-bolge-icerik]").forEach(el => { el.hidden = el.dataset.bolgeIcerik !== slug; });
  document.querySelectorAll("[data-bu-ay='']").forEach(el => buAyCiz(el, slug));
}

function bolgeBaslat() {
  const sayfaBolgesi = document.body.dataset.bolge;
  if (sayfaBolgesi) yazBolge(sayfaBolgesi);
  const secili = sayfaBolgesi || okuBolge() || "marmara";
  bolgeUygula(secili);
  document.addEventListener("click", e => {
    const btn = e.target.closest("[data-bolge-sekme] [data-bolge]");
    if (!btn) return;
    yazBolge(btn.dataset.bolge);
    bolgeUygula(btn.dataset.bolge);
  });
}

// ---------------------------------------------------------------- bu ay ne ekilir

async function buAyCiz(el, slug) {
  const d = await veri("/assets/data/ekim.json");
  if (!d) return;
  const bolge = el.dataset.buAy || slug;
  const ay = bugun.getMonth() + 1;
  const bas = `${iki(ay)}-01`;
  const son = `${iki(ay)}-${iki(new Date(bugun.getFullYear(), ay, 0).getDate())}`;
  const gruplar = {};
  for (const [bitki, isler] of Object.entries(d.isler[bolge] || {})) {
    for (const [tur, a, b] of isler) {
      if (a <= son && b >= bas) (gruplar[tur] ??= new Set()).add(bitki);
    }
  }
  const bolgeAd = d.bolgeler.find(b => b.slug === bolge)?.ad ?? "";
  const satirlar = Object.keys(d.turler).filter(t => gruplar[t]).map(t => {
    const linkler = [...gruplar[t]].map(s => `<a href="/ay-takvimi/${s}/">${d.bitkiler[s].ad}</a>`).join(", ");
    return `<div><dt>${d.turler[t]}</dt><dd>${linkler}</dd></div>`;
  }).join("");
  el.innerHTML = `
    <div class="bu-ay-bas"><h3>${AYLAR[ay - 1]} · ${bolgeAd}</h3><a class="ok-link" href="/ay-takvimi/${bugun.getFullYear()}/${AY_SLUG[ay - 1]}/">Gün gün</a></div>
    ${satirlar ? `<dl class="isler">${satirlar}</dl>` : `<p class="soluk">Bu ay ekim ya da dikim işi yok; toprak dinlenir.</p>`}`;
}

// ---------------------------------------------------------------- bugün kutusu

async function bugunCiz() {
  const kutu = document.querySelector("[data-bugun]");
  if (!kutu) return;
  const v = await veri(`/assets/data/ay-${bugun.getFullYear()}.json`);
  const g = gunKodu(v, bugun);
  if (!g) return;
  const durum = [g.evre ? g.evre[1] : (g.buyuyen ? "Büyüyen ay" : "Küçülen ay"), `${g.element[1]} günü`];
  if (g.tutulma) durum.push("Tutulma");
  kutu.querySelector("[data-bugun-icerik]").innerHTML = `
    <div class="bugun-ust">${aySimgesi(bugun)}<div><strong>${bugun.getDate()} ${AYLAR[bugun.getMonth()]} ${GUNLER[bugun.getDay()]}</strong><span class="soluk kucuk">${durum.join(" · ")}</span></div></div>
    <p>${g.tavsiye}</p>
    <a class="ok-link" href="/ay-takvimi/${bugun.getFullYear()}/${AY_SLUG[bugun.getMonth()]}/">${AYLAR[bugun.getMonth()]} takvimi</a>`;
  kutu.hidden = false;
}

// ---------------------------------------------------------------- ay kartları

function bugunuIsaretle() {
  document.querySelectorAll(`[data-d="${isoTarih(bugun)}"]`).forEach(el => el.classList.add("bugun"));
}

function kaydirmaBaslat() {
  document.querySelectorAll("[data-kaydir]").forEach(kap => {
    const sc = kap.querySelector(".aylar");
    const kart = sc.querySelector(`.ay-kart[data-yil="${bugun.getFullYear()}"][data-ay="${bugun.getMonth() + 1}"]`);
    if (kart && sc.scrollWidth > sc.clientWidth) {
      sc.scrollLeft += kart.getBoundingClientRect().left - sc.getBoundingClientRect().left - (sc.clientWidth - kart.clientWidth) / 2;
    }
    kap.querySelectorAll("[data-kaydir-yon]").forEach(btn => btn.addEventListener("click", () => {
      const genislik = sc.querySelector(".ay-kart").getBoundingClientRect().width + 12;
      sc.scrollBy({ left: Number(btn.dataset.kaydirYon) * genislik, behavior: "smooth" });
    }));
  });
}

const panel = document.getElementById("gun-panel");
let seciliHucre = null;

function paneliKapat() {
  panel.hidden = true;
  seciliHucre?.classList.remove("secili");
  seciliHucre?.focus();
  seciliHucre = null;
}

async function gunAc(hucre) {
  const tarih = new Date(`${hucre.dataset.d}T12:00:00`);
  const v = await veri(`/assets/data/ay-${tarih.getFullYear()}.json`);
  const g = gunKodu(v, tarih);
  if (!g) return;
  seciliHucre?.classList.remove("secili");
  seciliHucre = hucre;
  hucre.classList.add("secili");
  const ayUrl = `/ay-takvimi/${tarih.getFullYear()}/${AY_SLUG[tarih.getMonth()]}/`;
  const ayRozeti = g.evre
    ? `<span class="rozet" style="background:#f5f7f6"><i class="f f-${g.evre[0]}"></i>${g.evre[1]}</span>`
    : `<span class="rozet" style="background:#f5f7f6"><i class="ok ${g.buyuyen ? "b" : "k"}"></i>${g.buyuyen ? "Büyüyen ay" : "Küçülen ay"}</span>`;
  panel.innerHTML = `
    <button type="button" class="kapat" aria-label="Kapat">×</button>
    <h3>${tarih.getDate()} ${AYLAR[tarih.getMonth()]} ${tarih.getFullYear()}, ${GUNLER[tarih.getDay()]}</h3>
    <span class="rozet e-${g.element[0]}">${g.element[1]} günü</span>${ayRozeti}${g.tutulma ? `<span class="rozet" style="background:#f6e3de;color:#9a3b26">Tutulma</span>` : ""}
    <p>${g.tavsiye}</p>
    ${location.pathname === ayUrl ? "" : `<a class="ok-link" href="${ayUrl}">${AYLAR[tarih.getMonth()]} ${tarih.getFullYear()} gün gün</a>`}`;
  panel.hidden = false;
  panel.querySelector(".kapat").addEventListener("click", paneliKapat);
}

function gunPaneliBaslat() {
  if (!panel) return;
  document.addEventListener("click", e => {
    const hucre = e.target.closest(".ay-kart .g[data-d]");
    if (hucre) gunAc(hucre);
  });
  document.addEventListener("keydown", e => {
    if (e.key === "Escape" && !panel.hidden) paneliKapat();
  });
}

// ---------------------------------------------------------------- çizelge

function bugunCizgisi() {
  const yil = bugun.getFullYear();
  const uzunluk = (Date.UTC(yil + 1, 0, 1) - Date.UTC(yil, 0, 1)) / 864e5;
  const gun = (Date.UTC(yil, bugun.getMonth(), bugun.getDate()) - Date.UTC(yil, 0, 1)) / 864e5;
  document.querySelectorAll(".g-satir .g-iz").forEach(iz => {
    const c = document.createElement("span");
    c.className = "bugun-cizgi";
    c.style.left = `${(gun / uzunluk) * 100}%`;
    c.title = "Bugün";
    iz.appendChild(c);
  });
}

function gorunumBaslat() {
  const kap = document.querySelector("[data-gorunum]");
  if (!kap) return;
  const sec = ad => {
    kap.querySelectorAll("[data-gorunum-sec]").forEach(b => b.setAttribute("aria-selected", String(b.dataset.gorunumSec === ad)));
    document.querySelectorAll("[data-gorunum-icerik]").forEach(el => {
      el.hidden = el.dataset.gorunumIcerik !== ad;
      if (!el.hidden && el.dataset.buAy) buAyCiz(el);
    });
  };
  kap.addEventListener("click", e => {
    const b = e.target.closest("[data-gorunum-sec]");
    if (b) sec(b.dataset.gorunumSec);
  });
  sec(mobil() ? "ay" : "yil");
}

function ayDetayiAc() {
  document.querySelector(`[data-ay-detay="${bugun.getMonth() + 1}"]`)?.setAttribute("open", "");
}

bolgeBaslat();
bugunuIsaretle();
kaydirmaBaslat();
gunPaneliBaslat();
bugunCizgisi();
gorunumBaslat();
ayDetayiAc();
bugunCiz();
