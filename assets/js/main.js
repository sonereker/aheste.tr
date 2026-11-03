const ZONES = [
  { id: 0, title: "Ev, kafe, atölye", desc: "Her gün vakit geçirdiğimiz yer. Kafe, kurutma odası, sabun atölyesi ve aletlerle çalışacağımız atölye burada olsun." },
  { id: 1, title: "Mutfak bahçesi", desc: "Her gün ürün topladığımız bölüm: domates, salatalık ve aromatik otlar. Solucan kompostu da burada." },
  { id: 2, title: "Tıbbi bitkiler ve tavuklar", desc: "Biberiye, adaçayı, kekik terasları. Belki tavuk kümesi ve arı kovanları." },
  { id: 3, title: "Zeytin ve meyve", desc: "Ana ürün alanı. Zeytin loncaları, meyve ağaçları, altında baklagiller." },
  { id: 4, title: "Yarı yabani orman", desc: "Ceviz, kestane, dut. Yılda birkaç kez uğranan, kendi başına yaşayan alan." },
  { id: 5, title: "Yaban alanı", desc: "Hiç dokunulmayacak köşe. Gözlem ve öğrenme için." }
];

function initZoneMap() {
  const rings = document.getElementById("zoneRings");
  const list = document.getElementById("zoneList");
  if (!rings || !list) return;
  const ns = "http://www.w3.org/2000/svg";

  // Largest ring first so the smaller rings stay clickable on top.
  [...ZONES].reverse().forEach(zone => {
    const r = 30 + zone.id * 32;
    const circle = document.createElementNS(ns, "circle");
    circle.setAttribute("cx", 200);
    circle.setAttribute("cy", 200);
    circle.setAttribute("r", r);
    circle.setAttribute("class", "zone-ring");
    if (zone.id === 5) circle.setAttribute("stroke-dasharray", "4 5");
    circle.dataset.zone = zone.id;
    circle.addEventListener("click", () => setZone(zone.id));
    rings.appendChild(circle);

    const text = document.createElementNS(ns, "text");
    text.setAttribute("x", 200);
    text.setAttribute("y", 200 - r + 16);
    text.setAttribute("text-anchor", "middle");
    text.setAttribute("class", "zone-label");
    text.textContent = zone.id === 0 ? "0" : `ZON ${zone.id}`;
    rings.appendChild(text);
  });

  ZONES.forEach(zone => {
    const li = document.createElement("li");
    li.dataset.zone = zone.id;
    li.innerHTML = `<button type="button"><span class="z">${zone.id}</span><span><strong>${zone.title}</strong><span class="d">${zone.desc}</span></span></button>`;
    li.querySelector("button").addEventListener("click", () => setZone(zone.id));
    list.appendChild(li);
  });

  function setZone(id) {
    document.querySelectorAll("[data-zone]").forEach(el => el.classList.toggle("is-active", Number(el.dataset.zone) === id));
  }
  setZone(0);
}

function markCurrentPage() {
  const page = location.pathname.split("/").pop() || "index.html";
  document.querySelectorAll(".site-nav a").forEach(a => {
    if (a.getAttribute("href") === page) a.setAttribute("aria-current", "page");
  });
}

initZoneMap();
markCurrentPage();
