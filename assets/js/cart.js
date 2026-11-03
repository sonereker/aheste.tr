import { formatPrice, showToast, whatsappLink } from "./main.js";

const STORAGE_KEY = "aheste-cart";

function load() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
  } catch {
    return {};
  }
}

function save() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  } catch {
    // Storage can be unavailable (private mode); the cart still works for this visit.
  }
}

let items = load();
let catalog = new Map();

export function setCatalog(products) {
  catalog = new Map(products.map(p => [p.id, p]));
  // Drop items that are no longer orderable or exceed the current stock.
  for (const [id, qty] of Object.entries(items)) {
    const product = catalog.get(id);
    if (!product || !isOrderable(product)) delete items[id];
    else items[id] = Math.min(qty, product.quantity);
  }
  save();
  render();
}

export function isOrderable(product) {
  return (product.stock === "in_stock" || product.stock === "low") && product.quantity > 0;
}

export function addToCart(id) {
  const product = catalog.get(id);
  if (!product || !isOrderable(product)) return;
  const next = (items[id] || 0) + 1;
  if (next > product.quantity) {
    showToast(`${product.name}: stokta yalnızca ${product.quantity} adet var`);
    return;
  }
  items[id] = next;
  save();
  render();
  showToast(`${product.name} sepete eklendi`);
}

function changeQty(id, delta) {
  const product = catalog.get(id);
  const next = (items[id] || 0) + delta;
  if (next <= 0) delete items[id];
  else if (product && next <= product.quantity) items[id] = next;
  save();
  render();
}

function entries() {
  return Object.entries(items)
    .map(([id, qty]) => ({ product: catalog.get(id), qty }))
    .filter(entry => entry.product);
}

function orderMessage() {
  const lines = ["Merhaba, Âheste'den sipariş vermek istiyorum:"];
  let total = 0;
  entries().forEach(({ product, qty }) => {
    total += product.price * qty;
    lines.push(`- ${qty} × ${product.name} (${product.unit}), ${formatPrice(product.price * qty)}`);
  });
  lines.push(`Toplam: ${formatPrice(total)}`);
  return lines.join("\n");
}

const drawer = document.getElementById("cart");
const list = document.getElementById("cartItems");
const totalEl = document.getElementById("cartTotal");
const checkout = document.getElementById("cartCheckout");

function render() {
  const count = Object.values(items).reduce((sum, qty) => sum + qty, 0);
  document.querySelectorAll("[data-cart-count]").forEach(el => (el.textContent = count));
  if (!list) return;

  const rows = entries();
  if (rows.length === 0) {
    list.innerHTML = `<li class="cart-empty">Sepetiniz boş.</li>`;
  } else {
    list.innerHTML = rows.map(({ product, qty }) => `
      <li>
        <div><strong>${product.name}</strong><div class="muted">${product.unit} · ${formatPrice(product.price)}</div></div>
        <div class="qty" aria-label="${product.name} adedi">
          <button type="button" data-dec="${product.id}" aria-label="Azalt">−</button>
          <span>${qty}</span>
          <button type="button" data-inc="${product.id}" aria-label="Artır">+</button>
        </div>
      </li>`).join("");
  }
  const total = rows.reduce((sum, { product, qty }) => sum + product.price * qty, 0);
  totalEl.textContent = formatPrice(total);
  checkout.toggleAttribute("aria-disabled", rows.length === 0);
  checkout.href = rows.length ? whatsappLink(orderMessage()) : "#";
}

function openCart(open) {
  if (!drawer) return;
  drawer.classList.toggle("is-open", open);
  drawer.setAttribute("aria-hidden", String(!open));
  if (open) drawer.querySelector("[data-close-cart]").focus();
}

document.querySelectorAll("[data-open-cart]").forEach(btn => btn.addEventListener("click", () => openCart(true)));
drawer?.querySelector("[data-close-cart]").addEventListener("click", () => openCart(false));
document.addEventListener("keydown", e => { if (e.key === "Escape") openCart(false); });
list?.addEventListener("click", e => {
  const inc = e.target.closest("[data-inc]");
  const dec = e.target.closest("[data-dec]");
  if (inc) changeQty(inc.dataset.inc, 1);
  if (dec) changeQty(dec.dataset.dec, -1);
});
checkout?.addEventListener("click", e => {
  if (checkout.hasAttribute("aria-disabled")) e.preventDefault();
});

render();
