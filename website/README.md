# US Migration research website

A static, responsive research site. No build step, Node installation, or API keys
are required. Noto Sans loads from Google Fonts, with a sans-serif fallback when
offline; chart libraries and data are served locally. Serve this directory over HTTP:

```powershell
.\us-migration\Scripts\python.exe -m http.server 8000 --bind 127.0.0.1 --directory website
```

Open http://127.0.0.1:8000. The complete `website/` directory can also be hosted
on any static host (including GitHub Pages). Hash navigation supports direct
links such as `/#data-prep-eda`. Opening `index.html` as a file will not work
because browsers restrict local JSON fetches.

## Content and data

- Introduction, Data Prep + EDA, Clustering and PCA are populated. Six model chapters contain
  only Overview, Data, Code, Results headings. Conclusion has no findings yet.
- `data/introduction.json` contains the supplied introduction, with the domestic
  IRS definition aligned to the measured EDA outcome. Planned features are
  distinguished from current features in `chapters/introduction.js`.
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
- Maps share projection, outcome-specific colors, gray missingness, zoom, search, and
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
preserves chart and map state. Planned chapters use the same section navigation with placeholder headings.

## Phase 2 chapters

`chapters/clustering.js` and `chapters/pca.js` render Overview, Data Prep, Code,
Results and Conclusions using shared typography, plain section headers, navigation
and chart cards. Open `/#clustering` or `/#pca`. D3 renders the analysis figures;
data snapshots retain the shared light image style. Numeric samples and result CSVs are downloadable, with row keys separate
from model inputs. GitHub links target named sections of notebooks 03 and 04 on
`main` and become available when the changes are published.

Run `python scripts/run_phase2.py` to execute both notebooks and refresh their
saved outputs, `assets/phase2/`, `data/phase2/`, `data/clustering.json` and
`data/pca.json`. No website build or external chart service is required. The JSON
exports record the cleaned-input checksum and analysis package versions.
See [Phase 2 methodology](../docs/methodology.md#clustering-and-pca).

Validation includes required content, notebook anchors, local downloads/images,
desktop/mobile overflow, chapter/section navigation and the existing maps/charts.
`python -m pytest tests/test_phase2.py tests/test_website_data.py -q` verifies
published arithmetic, selection rules, PCA geometry, sample consistency and
executed notebook outputs.

## Navigation and interactive results

Noto Sans typography and the Wanderer / Hearth / Journey palette use parchment, forest green and terracotta. The masthead, chapter title and left section navigation remain visible while scrolling. Model navigation follows Regression with AdaBoost, GradientBoosting and XGBoost.

`charts/clustering.js`, `charts/pca.js`, and `charts/phase-details.js` use vendored D3 for silhouette curves, scatterplots, profile heatmaps, truncated hierarchies, outcome boxes, PCA variance, associations, and selectable score quintiles. Pointer, touch, and keyboard inspection expose exact values. The workflow diagram uses responsive HTML generated by D3.

`charts/cluster-map.js` shares map markup with Changing Populations, including county suggestions, keyboard selection, zoom, inspection, and slate/gold colors. FIPS assignments join existing Census boundaries; gray marks excluded or unmatched geographies. `clustering-charts.json` and `pca-toy.json` are exported by the executed notebooks from fitted arrays. Standardized sample exports use dimensionless column names. The notebook's cluster interpretations include county examples verified against assignments.

History entries retain scroll positions and rendered chapter state so Back and Forward restore the prior reading position. Conclusion cards reuse the original Introduction questions and connect them to plain-language answers.

Run `node tests/website_interactions.cjs` with Playwright available on `NODE_PATH`
and optionally `CHROMIUM_EXECUTABLE` pointing to a local Chromium binary. The
browser regression test covers charts, county suggestions, keyboard inspection,
whole-number k ticks, viewport sizing and exact Back restoration at 1440, 768 and
390 pixels. Screenshots are saved under ignored `data/interim/`.

## Chapter modules

`app.js` loads the exported data and runs routing, navigation, links, and lifecycle
cleanup. `chapters/index.js` keeps each chapter title, heading, URL slug, `render`,
and `init` together. Each chapter owns its narrative and layout. To add a chapter,
create a module exporting `render(data)` and `init(data)` and add a registry entry.
`render` returns sections with direct `h2` children; their titles become the left
navigation labels and stable section anchors. `init` initializes visuals and may
return a cleanup function. The first section is selected and scrolled into view
on chapter entry; explicit section links take precedence.

Long chart implementations live in `charts/`, with shared map and chart helpers.
Native JavaScript imports make module dependencies explicit. The vendored D3 and
Plotly distributions load before the application module. No bundler is required.
Data Prep + EDA uses title case for readable section names (Data Sources, Data
Cleaning, EDA Findings).

Snapshot image generators share `src/us_migration/snapshot_style.py`: white
backgrounds, dark text, pale headers, and subtle row shading. Execute the cleaning,
clustering, and PCA notebooks to refresh their embedded figures, then run
`scripts/export_website_data.py` and `scripts/export_cleaning_evidence.py` to
refresh the published cleaning assets and notebook evidence.

## Net migration, inflows, and outflows

All three rates per 1,000 ACS residents receive equal emphasis. County downloads
retain their supporting counts. The ten EDA chart groups, cluster distributions,
PCA associations, and score quintiles compare the same observations across
outcomes. Findings and captions are regenerated from executed analyses.

Detailed outcome charts have selectors; summary tables and the PCA association
matrix show the outcomes together. Map limits use pooled-year 95th percentiles.
The shared Python outcome contract is exported to `data/outcomes.json`.
Snapshot cards place contextual notes below images. Interactive marks use compact
pointer/focus tooltips. The population-change introduction remains contextual.
