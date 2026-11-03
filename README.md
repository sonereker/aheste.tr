# aheste.tr

Static website for Âheste, a permaculture garden in Bursa. Served with GitHub Pages at https://aheste.tr.

## Structure

- `index.html`, `permaculture.html`, `market.html`, `cafe.html`, `visit.html`: pages
- `data/products.json`: product catalog and stock (single source of truth)
- `assets/css/style.css`: styles
- `assets/js/`: `main.js` (shared, WhatsApp config), `cart.js`, `market.js`
- `assets/images/`: generated imagery (webp)

## Updating stock

Edit `data/products.json`. Set `stock` to one of `in_stock`, `low`, `sold_out`, `upcoming` and `quantity` to the available count. Products with `in_stock`/`low` and `quantity > 0` can be added to the cart.

## WhatsApp orders

Set `WHATSAPP_NUMBER` in `assets/js/main.js` (international format without `+`, e.g. `905xxxxxxxxx`).

## Local preview

```sh
python3 -m http.server
```

Open http://localhost:8000. Opening files directly does not work because products are loaded with `fetch`.
