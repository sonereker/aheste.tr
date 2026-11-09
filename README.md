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

## Moon calendar (`/ay-takvimi/`)

A generated section with its own look (Merriweather, `assets/css/takvim.css`, `assets/js/takvim.js`). Do not edit `ay-takvimi/**` by hand; edit the data or templates and rebuild:

```sh
uv run tools/takvim/build.py   # writes ay-takvimi/, assets/data/*.json, sitemap.xml, robots.txt
python3 tools/takvim/kontrol.py  # checks internal links, anchors and sitemap
```

- Regions and frost dates: `tools/takvim/data/bolgeler.json`.
- Crops and tree jobs: `tools/takvim/data/bitkiler.json`. Windows are in weeks relative to the region's last spring frost (`s`) and first autumn frost (`i`), e.g. `["dikim", "s+0", "s+6"]`; a window from `i…` to `s…` runs into the next year. `yok` / `sadece` limit a window to some regions.
- Sowing depth, spacing, germination and harvest time per crop: `tools/takvim/data/bilgiler.json` (every crop in `bitkiler.json` needs an entry).
- A harvest window shorter than 10 days is dropped and the crop is marked as hard to grow outdoors in that region.
- Folk calendar days: `tools/takvim/data/halk_takvimi.json`. Moon phases, element days, equinoxes and eclipses are computed with `ephem` (Turkey time, UTC+3).
- Templates: `tools/takvim/templates/`.
- The build writes the current and next year. From November the "active" year (hub, region, crop pages) is the next year. `.github/workflows/ay-takvimi.yml` reruns it every 1 November and commits the result; older year folders are kept.

## Local preview

```sh
python3 -m http.server
```

Open http://localhost:8000.
