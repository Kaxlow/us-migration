# US Migration research website

A static, responsive research site. No build step, Node installation, or API keys
are required. Fira Sans loads from Google Fonts, with a sans-serif fallback when
offline; chart libraries and data are served locally. Serve this directory over HTTP:

```powershell
.\us-migration\Scripts\python.exe -m http.server 8000 --bind 127.0.0.1 --directory website
```

Open http://127.0.0.1:8000. The complete `website/` directory can also be hosted
on any static host (including GitHub Pages). Hash navigation supports direct
links such as `/#data-prep-eda`. Opening `index.html` as a file will not work
because browsers restrict local JSON fetches.

## Content and data

- Introduction and Data Prep + EDA are populated. Seven model chapters contain
  only Overview, Data, Code, Results headings. Conclusion has no findings yet.
- `data/introduction.json` contains the supplied introduction, with the domestic
  IRS definition aligned to the measured EDA outcome. Planned features are
  distinguished from current features in `app.js`.
- `scripts/build_population_map.py` independently downloads Vintage 2025 county
  estimates, CBSA membership, and 2025 Census cartographic boundaries. It does
  not import or change the existing cleaning/EDA pipeline. Requires the project's
  pandas/requests dependencies plus `pyshp==3.1.6`.
- County change = `100 * (POPESTIMATE2025 / POPESTIMATE2024 - 1)`, using the same
  vintage for both years. Area growth uses summed populations. CBSA membership
  classifies metropolitan/micropolitan counties; unmatched counties are outside
  these areas. Coverage is the 50 states and DC, excluding Puerto Rico.
- Download cache and source sidecars: `data/raw/website/` (Git ignored).
  Published source URLs, retrieval timestamps, and SHA-256 hashes are retained in
  `website/data/population-provenance.json`. Delete only the relevant cached
  source and sidecar if deliberately refreshing an upstream release.
- `scripts/export_website_data.py` exports the existing validated analysis
  dataset, saved correlation/trend results, captions, and real cleaning images.
  It never runs cleaning. The analysis JSON records the input Parquet checksum.
- EDA uses 2009–2023, including state units for Alaska/Connecticut. The ten charts
  exclude state units. Scatter plots replace the notebook's two hexbin plots;
  all observations are retained. Correlations and captions use saved EDA outputs.
- Maps share projection, diverging colors, gray missingness, zoom, search, and
  pointer/touch inspection. Searching also provides keyboard access to details.
  EDA boundaries are a fixed 2025 display, not a historical boundary crosswalk.
  Rates outside the legend bounds saturate in color; exact values remain visible.
- Raw project snapshots are not in Git. Source cards link to official endpoints
  and the repository's acquisition guide, without pretending raw files are hosted.

Rebuild the two exports from the repository root:

```powershell
.\us-migration\Scripts\python.exe -m pip install pyshp==3.1.6
.\us-migration\Scripts\python.exe scripts/build_population_map.py
.\us-migration\Scripts\python.exe scripts/export_website_data.py
.\us-migration\Scripts\python.exe scripts/export_cleaning_evidence.py
.\us-migration\Scripts\python.exe -m pytest tests/test_website_data.py -q
```

## Third-party assets

Vendored, version-pinned D3 7.9.0 (ISC) and Plotly.js 2.35.2 (MIT) retain their
license notices in the minified files. Sources: https://d3js.org and
https://github.com/plotly/plotly.js. Census geography and population data are
credited beside the maps and in provenance. Existing notebook images are copied
into this directory so the published site does not depend on ignored local files.

## Validation

Browser checks cover desktop/mobile layout, all ten chart traces, year changes,
state-level map records, county search, empty chapter headings, and console errors.
Data tests check county coverage, growth arithmetic, geography grouping totals,
analysis uniqueness, net-count arithmetic, and chart cohort size.

The Data Cleaning section follows notebook sections 2–9 in order. Its comparison
images come from the notebook; expandable tables preserve saved cell outputs.
Additional joined and paired imputation snapshots come from the notebook's saved
Parquet exports, labeled separately from cell outputs. `cleaning-evidence.json`
records the notebook and export checksums. Regenerate it after rerunning notebook 01.
Populated chapters have section links using `#chapter/section-id`; section navigation
preserves chart and map state. Conclusion has no section navigation until content is added.
