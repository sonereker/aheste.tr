import { formatPrice, showToast, whatsappLink } from "./main.js";
import { addToCart, isOrderable, setCatalog } from "./cart.js";

const STOCK_LABELS = {
  in_stock: p => `bol, ${p.quantity} adet`,
  low: p => `son ${p.quantity}!`,
  sold_out: () => "tükendi",
  upcoming: () => "mevsimi bekleniyor"
};

const grid = document.getElementById("products");
const filters = document.getElementById("filters");
const banner = document.getElementById("stockBanner");
const limit = Number(grid?.dataset.limit) || Infinity;

function productCard(p) {
  const orderable = isOrderable(p);
  return `
    <article class="product${orderable ? "" : " is-out"}">
      <img src="assets/images/${p.image}.webp" alt="${p.name}" loading="lazy" width="600" height="600">
      <span class="code">${p.code} · ${p.unit}</span>
      <h3>${p.name}</h3>
      <span class="latin">${p.latin}</span>
      <p class="desc">${p.description}</p>
      <div class="row"><span class="price">${formatPrice(p.price)}</span><span class="stock ${p.stock}">${STOCK_LABELS[p.stock](p)}</span></div>
      <button class="btn${orderable ? "" : " ghost"}" type="button" data-id="${p.id}" data-action="${orderable ? "add" : "notify"}">
        ${orderable ? "Sepete ekle" : "Gelince haber ver"}
      </button>
    </article>`;
}

function render(products, category) {
  const shown = products.filter(p => category === "all" || p.category === category).slice(0, limit);
  grid.innerHTML = shown.map(productCard).join("") || `<p class="muted">Bu kategoride ürün yok.</p>`;
}

async function init() {
  if (!grid) return;
  let data;
  try {
    const res = await fetch("data/products.json", { cache: "no-store" });
    data = await res.json();
  } catch {
    grid.innerHTML = `<p class="muted">Ürünler yüklenemedi. Sayfayı yenilemeyi deneyin.</p>`;
    return;
  }
  const { products, categories } = data;
  setCatalog(products);

  if (banner) banner.hidden = products.some(isOrderable);

  let current = "all";
  if (filters) {
    const all = [{ id: "all", name: "Tümü" }, ...categories];
    filters.innerHTML = all.map(c => `<button class="filter" type="button" data-category="${c.id}" aria-pressed="${c.id === current}">${c.name}</button>`).join("");
    filters.addEventListener("click", e => {
      const btn = e.target.closest("[data-category]");
      if (!btn) return;
      current = btn.dataset.category;
      filters.querySelectorAll("[data-category]").forEach(b => b.setAttribute("aria-pressed", String(b === btn)));
      render(products, current);
    });
  }
  render(products, current);

  grid.addEventListener("click", e => {
    const btn = e.target.closest("[data-action]");
    if (!btn) return;
    const product = products.find(p => p.id === btn.dataset.id);
    if (btn.dataset.action === "add") {
      addToCart(product.id);
    } else {
      window.open(whatsappLink(`Merhaba, "${product.name}" yeniden geldiğinde bana haber verebilir misiniz?`), "_blank", "noopener");
      showToast(`${product.name} gelince haber vereceğiz`);
    }
  });
}

init();
