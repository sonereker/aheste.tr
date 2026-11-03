# aheste.tr

Public project notebook for Âheste, a permaculture farm we are planning. Served with GitHub Pages at https://aheste.tr.

Each page is a "note" that weighs options with pros, cons and rough scores, and ends with open questions and our current leaning.

## Pages

- `index.html`: notebook overview, decision board, table of contents, log
- `location.html`: Bursa vs Çanakkale vs Yalova, distance to the provincial centre, weighted scoring (`assets/js/location.js`)
- `garden.html`: garden elements (food forest, keyhole beds, swales, chickens, bees…) and the zone map
- `trees.html`: candidate trees with filters (`assets/js/trees.js`)
- `cafe.html`: café concepts
- `shop.html`: shop product ideas

## Editing

- Note status classes: `open`, `discussing`, `leaning`, `decided` (see `.status` in `assets/css/style.css`).
- Region scores and default weights: `CRITERIA` and `REGIONS` in `assets/js/location.js`.
- Tree data: `TREES` in `assets/js/trees.js`.
- Zone descriptions: `ZONES` in `assets/js/main.js`.

## Local preview

```sh
python3 -m http.server
```

Open http://localhost:8000.
