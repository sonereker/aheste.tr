// Set to the farm's number in international format without "+" (e.g. "905xxxxxxxxx").
// Left empty, WhatsApp opens with the message and lets the visitor pick a contact.
export const WHATSAPP_NUMBER = "";

export function whatsappLink(message) {
  return `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(message)}`;
}

export function formatPrice(value) {
  return `₺${value.toLocaleString("tr-TR")}`;
}

let toastTimer;
export function showToast(message) {
  let toast = document.getElementById("toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "toast";
    toast.className = "toast";
    toast.setAttribute("role", "status");
    toast.setAttribute("aria-live", "polite");
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 2600);
}

const ZONES = [
  { id: 0, title: "Ev ve kafe", desc: "Gölge Kafe, kurutma odası, sabun atölyesi. Her gün buradayız." },
  { id: 1, title: "Mutfak bahçesi", desc: "Anahtar delik yataklar, domates, fesleğen, solucan kompostu." },
  { id: 2, title: "Tıbbi bitkiler", desc: "Biberiye, adaçayı, kekik terasları. Arı kovanları da burada." },
  { id: 3, title: "Zeytin loncası", desc: "140 zeytin ağacı, altında baklagiller ve yer örtücüler." },
  { id: 4, title: "Yarı yabani orman", desc: "Ceviz, kestane, yabani armut. Yılda birkaç kez hasat." },
  { id: 5, title: "Yaban alanı", desc: "Hiç dokunmuyoruz. Gözlem ve öğrenme alanı." }
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
  setZone(2);
}

function markCurrentPage() {
  const page = location.pathname.split("/").pop() || "index.html";
  document.querySelectorAll(".site-nav a").forEach(a => {
    if (a.getAttribute("href") === page) a.setAttribute("aria-current", "page");
  });
}

function initWhatsappForms() {
  document.querySelectorAll("form[data-whatsapp]").forEach(form => {
    form.addEventListener("submit", event => {
      event.preventDefault();
      if (!form.reportValidity()) return;
      const data = new FormData(form);
      const lines = [form.dataset.whatsapp];
      form.querySelectorAll("[name]").forEach(field => {
        const value = data.get(field.name);
        if (value) lines.push(`${field.dataset.label || field.name}: ${value}`);
      });
      window.open(whatsappLink(lines.join("\n")), "_blank", "noopener");
      const status = form.querySelector(".form-status");
      if (status) status.textContent = "WhatsApp'ta mesajınız hazır, göndermeyi unutmayın.";
    });
  });
}

initZoneMap();
markCurrentPage();
initWhatsappForms();
