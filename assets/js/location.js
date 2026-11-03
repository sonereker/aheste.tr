// Scores are our rough 1–5 estimates per criterion (5 = best for us), not measured data.
const CRITERIA = [
  { id: "olive", name: "Zeytin ve iklim uyumu", weight: 4 },
  { id: "water", name: "Su bulma kolaylığı", weight: 4 },
  { id: "land", name: "Arsa ucuzluğu", weight: 3 },
  { id: "visitors", name: "Ziyaretçi potansiyeli", weight: 3 },
  { id: "distance", name: "İl merkezine yakınlık", weight: 3 },
  { id: "frost", name: "Don riskinin azlığı", weight: 2 },
  { id: "market", name: "Satış kanalı (pazar, restoran)", weight: 2 }
];

const REGIONS = [
  { id: "bursa", name: "Bursa", scores: { olive: 4, water: 4, land: 2, visitors: 5, distance: 4, frost: 3, market: 5 } },
  { id: "canakkale", name: "Çanakkale", scores: { olive: 5, water: 2, land: 4, visitors: 3, distance: 3, frost: 4, market: 3 } },
  { id: "yalova", name: "Yalova", scores: { olive: 3, water: 5, land: 1, visitors: 4, distance: 5, frost: 3, market: 4 } }
];

const weightsEl = document.getElementById("weights");
const rankingEl = document.getElementById("ranking");

function score(region, weights) {
  const total = CRITERIA.reduce((sum, c) => sum + weights[c.id], 0);
  if (total === 0) return 0;
  const weighted = CRITERIA.reduce((sum, c) => sum + weights[c.id] * region.scores[c.id], 0);
  return Math.round((weighted / total / 5) * 100);
}

function currentWeights() {
  return Object.fromEntries(CRITERIA.map(c => [c.id, Number(document.getElementById(`w-${c.id}`).value)]));
}

function renderRanking() {
  const weights = currentWeights();
  const ranked = REGIONS.map(r => ({ ...r, score: score(r, weights) })).sort((a, b) => b.score - a.score);
  rankingEl.innerHTML = ranked.map((r, i) => `
    <li>
      <span class="pos">${i + 1}</span>
      <div><strong>${r.name}</strong><div class="bar"><i style="width:${r.score}%"></i></div></div>
      <span class="score">${r.score}/100</span>
    </li>`).join("");
}

function init() {
  if (!weightsEl || !rankingEl) return;
  weightsEl.innerHTML = CRITERIA.map(c => `
    <label for="w-${c.id}">
      <span>${c.name}</span>
      <output id="o-${c.id}" for="w-${c.id}">${c.weight}</output>
      <input type="range" id="w-${c.id}" min="0" max="5" step="1" value="${c.weight}">
    </label>`).join("") + `<button class="reset" type="button" id="resetWeights">Varsayılana dön</button>`;

  weightsEl.addEventListener("input", e => {
    if (e.target.type !== "range") return;
    document.getElementById(e.target.id.replace("w-", "o-")).textContent = e.target.value;
    renderRanking();
  });
  document.getElementById("resetWeights").addEventListener("click", () => {
    CRITERIA.forEach(c => {
      document.getElementById(`w-${c.id}`).value = c.weight;
      document.getElementById(`o-${c.id}`).textContent = c.weight;
    });
    renderRanking();
  });
  renderRanking();
}

init();
