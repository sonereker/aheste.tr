// Rough planning figures from general horticulture sources; to be checked with local nurseries.
const TREES = [
  { name: "Zeytin · Gemlik", latin: "Olea europaea", layer: "canopy", years: "4–5", water: "low", frost: -7, fit: { bursa: "good", canakkale: "good", yalova: "ok" }, note: "Bölgenin yerli çeşidi, hem yağlık hem sofralık. Ana ürünümüz olabilir." },
  { name: "Zeytin · Ayvalık", latin: "Olea europaea", layer: "canopy", years: "5–6", water: "low", frost: -6, fit: { bursa: "ok", canakkale: "good", yalova: "ok" }, note: "Yağ verimi yüksek, Kuzey Ege'de çok iyi. Marmara'da soğuk kışlarda zorlanabilir." },
  { name: "Zeytin · Domat", latin: "Olea europaea", layer: "canopy", years: "5–6", water: "low", frost: -7, fit: { bursa: "ok", canakkale: "good", yalova: "ok" }, note: "İri sofralık çeşit, kırma ve çizik zeytin için." },
  { name: "Ceviz", latin: "Juglans regia", layer: "canopy", years: "6–8", water: "high", frost: -25, fit: { bursa: "good", canakkale: "ok", yalova: "good" }, note: "Kökleri juglon salgılar, altına domates ve elma dikilmez. Bahçenin daha uzak bölümlerine." },
  { name: "Kestane", latin: "Castanea sativa", layer: "canopy", years: "5–7", water: "medium", frost: -20, fit: { bursa: "good", canakkale: "ok", yalova: "good" }, note: "Asidik toprak ister. Uludağ ve Kaz Dağları eteklerinde doğal olarak var." },
  { name: "Dut", latin: "Morus alba / nigra", layer: "canopy", years: "3–5", water: "medium", frost: -20, fit: { bursa: "good", canakkale: "good", yalova: "good" }, note: "Hızlı büyür, gölge ve tavuk yemi verir. Pekmez ve kurutma için." },
  { name: "İncir", latin: "Ficus carica", layer: "low", years: "2–3", water: "low", frost: -10, fit: { bursa: "good", canakkale: "good", yalova: "ok" }, note: "Kuru incir ve reçel için. Genç fidanlar sert ayazda donabilir." },
  { name: "Nar", latin: "Punica granatum", layer: "low", years: "3", water: "low", frost: -12, fit: { bursa: "ok", canakkale: "good", yalova: "ok" }, note: "Sıcak, kuru yaz sever. Nar ekşisi dükkân için güçlü bir ürün." },
  { name: "Badem", latin: "Prunus dulcis", layer: "low", years: "3–4", water: "low", frost: -15, fit: { bursa: "ok", canakkale: "good", yalova: "poor" }, note: "Erken çiçek açar, geç don çiçeği yakar. Nemli iklimde hastalanır." },
  { name: "Ayva", latin: "Cydonia oblonga", layer: "low", years: "3–4", water: "medium", frost: -20, fit: { bursa: "good", canakkale: "ok", yalova: "good" }, note: "Kafe tatlıları ve reçel için. Ateş yanıklığına dikkat." },
  { name: "Keçiboynuzu", latin: "Ceratonia siliqua", layer: "low", years: "6–8", water: "low", frost: -5, fit: { bursa: "poor", canakkale: "ok", yalova: "poor" }, note: "Soğuğa hassas. Ancak denize yakın, korunaklı bir yamaçta denenebilir." },
  { name: "İğde", latin: "Elaeagnus angustifolia", layer: "low", years: "3–4", water: "low", frost: -30, fit: { bursa: "good", canakkale: "good", yalova: "good" }, note: "Azot bağlar, rüzgâr kırıcı olur, arılar sever. Zeytin loncasının yardımcısı." },
  { name: "Yalancı akasya", latin: "Robinia pseudoacacia", layer: "canopy", years: "—", water: "low", frost: -30, fit: { bursa: "good", canakkale: "good", yalova: "good" }, note: "Azot bağlar, çok iyi bal ağacı. Ama hızlı yayılır, kontrol gerekir." },
  { name: "Gümüş akasya", latin: "Acacia dealbata", layer: "low", years: "—", water: "low", frost: -8, fit: { bursa: "ok", canakkale: "good", yalova: "good" }, note: "Azot bağlar, kış sonu çiçek açar. İstilacı olabilir, sınırlı dikilmeli." }
];

const LAYER_NAMES = { canopy: "Tepe", low: "Kısa boylu ağaçlar" };
const WATER_NAMES = { low: "Az", medium: "Orta", high: "Çok" };
const FIT_NAMES = { good: "İyi", ok: "Olur", poor: "Zor" };
const REGION_NAMES = { bursa: "Bursa", canakkale: "Çanakkale", yalova: "Yalova" };

const body = document.getElementById("treeRows");
const count = document.getElementById("treeCount");
const filters = { region: "all", layer: "all", water: "all" };

function matches(tree) {
  if (filters.region !== "all" && tree.fit[filters.region] === "poor") return false;
  if (filters.layer !== "all" && tree.layer !== filters.layer) return false;
  if (filters.water !== "all" && tree.water !== filters.water) return false;
  return true;
}

function render() {
  const rows = TREES.filter(matches);
  body.innerHTML = rows.map(t => `
    <tr>
      <th scope="row">${t.name}<div class="muted small" style="font-family: var(--font-body); font-weight: 400; font-style: italic">${t.latin}</div></th>
      <td>${LAYER_NAMES[t.layer]}</td>
      <td class="num">${t.years} yıl</td>
      <td>${WATER_NAMES[t.water]}</td>
      <td class="num">${t.frost}°C</td>
      ${Object.keys(REGION_NAMES).map(r => `<td><span class="fit ${t.fit[r]}">${FIT_NAMES[t.fit[r]]}</span></td>`).join("")}
      <td class="small">${t.note}</td>
    </tr>`).join("") || `<tr><td colspan="9" class="muted">Bu filtrelere uyan ağaç yok.</td></tr>`;
  count.textContent = `${rows.length} / ${TREES.length} ağaç`;
}

function buildGroup(key, label, options) {
  const group = document.createElement("div");
  group.className = "filters";
  group.setAttribute("role", "group");
  group.setAttribute("aria-label", label);
  group.innerHTML = `<span class="label">${label}</span>` + Object.entries({ all: "Tümü", ...options })
    .map(([value, name]) => `<button class="filter" type="button" data-key="${key}" data-value="${value}" aria-pressed="${value === "all"}">${name}</button>`).join("");
  group.addEventListener("click", e => {
    const btn = e.target.closest("[data-value]");
    if (!btn) return;
    filters[key] = btn.dataset.value;
    group.querySelectorAll("[data-value]").forEach(b => b.setAttribute("aria-pressed", String(b === btn)));
    render();
  });
  return group;
}

const filterHost = document.getElementById("treeFilters");
if (body && filterHost) {
  filterHost.append(
    buildGroup("region", "Bölgeye uygun", REGION_NAMES),
    buildGroup("layer", "Katman", LAYER_NAMES),
    buildGroup("water", "Su ihtiyacı", WATER_NAMES)
  );
  render();
}
