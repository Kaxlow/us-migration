# Research website

A static research site using native JavaScript modules and vendored D3 and Plotly. Serve the committed `website/` directory:

```powershell
python -m http.server 8000 --bind 127.0.0.1 --directory website
```

Open [the local preview](http://127.0.0.1:8000). The site root opens `landing.html`, the county migration flow atlas. County and state search lists every matching county in a scrollable menu on all maps. Its analysis button opens `index.html`; existing root hash links still open their analysis chapters. Navigation runs Overview, Data & Methods, Analyses, then Findings. Analysis sections run Overview, Data Prep, Code, Results, then Conclusion, with method explanations and preparation evidence visible in the page. Future work retains links for planned methods.

## Content and data ownership

The landing page versions its CSS, entry module, and search-module URLs to keep cached assets aligned with its HTML. Bump the `atlas-3` asset version in `landing.html` and `landing.js` when changing that interface. During local development, Ctrl+Shift+R refreshes an already-open page and its cached assets.

The chapter registry declares title, stable URL slug, navigation group, completion status, dataset dependencies, `render(data)`, and `init(data)`. Each section declares an explicit ID. The router caches successful datasets and mounted views, preserves history and reading position, and contains failures within the requested chapter. Existing method routes remain available.

`data/introduction.json` owns the question wording, stable IDs, statuses, evidence links, and remaining gaps. Measured findings come from topic result bundles; `data/findings.json` is a compact generated synthesis for Overview and Findings. Numeric text uses these exports.

`data/<topic>/` and `assets/<topic>/` are publication copies with ownership manifests. The exporter validates canonical checksums, preserves unowned files, and removes only obsolete owned files. Classification validates complete input/split/target context and shared county profiles before combining its independent notebooks. Identical sample images are shared only when full sample values, columns, and row keys agree.

See the [workflow](../docs/workflow.md#incremental-website-export) for refresh commands and [Adding an analysis](../docs/adding-an-analysis.md) for extension instructions.

## Map context and measurement

The landing atlas uses all published domestic county-pair records in the cleaned IRS inflow view, with explicit origin and destination. Rebuild its 2009–2023 year files and source-hash metadata with `python scripts/build_flow_map.py`. Each selection draws every geographically matched, reported connection. Canvas projects a three-dimensional scene with raised curved arrows, a fixed perspective, drag and keyboard panning, zoom, and county picking. Moving arrowheads follow each flow from origin to destination; reduced-motion preferences start with static arrows. The Animate flows / Pause flows button explicitly controls arrow movement independently of Play years. Arrow width scales linearly with the count within the current selection. Time playback advances through the available filing-year intervals.

Net arrows require reported counts in both directions and follow the sign of inflow minus outflow. Missing or suppressed directions remain unknown. Balanced pairs have no arrow. The packaged flow data retain reported connections with historical county identifiers that lack matching display geometry. The atlas draws connections with matching display geometry, and tooltips give their exact values. Alaska and Hawaii use insets. These pair sums differ from published county totals when suppression or source coverage removes individual connections.

The four analysis notebooks author their conclusions in Markdown. The repository module `src/us_migration/analysis_exports.py` reads that prose using `notebook_conclusions`, and the website renders the same paragraphs and task subsections. One collapsed helper call before Conclusions keeps notebook reruns connected to those exports. After changing data or model choices, review the prose against the new results before packaging the topic bundles.

The introduction's population-change map uses Vintage 2025 Census estimates and same-vintage 2024–2025 growth. CBSA membership defines metropolitan, micropolitan, and other areas; area growth uses summed populations. Its separate builder records source URLs, retrieval times, and hashes in `data/population-provenance.json`.

EDA covers 2009–2023 with Alaska/Connecticut state substitutes on the map. County-only charts exclude those substitutes. Fixed 2025 display boundaries provide a visual reference; native historical geographies remain in the analysis. Outcome scales use pooled-year 95th percentiles and retain exact tooltip values. Interactive scatter points replace two notebook density charts while retaining all observations.

## Browser verification

Python checks validate exported arithmetic and provenance. Install Playwright in a local development environment and make it available through `NODE_PATH`; `CHROMIUM_EXECUTABLE` can point to an existing Chromium browser. Run:

```powershell
node tests/website_interactions.cjs
node tests/website_supervised.cjs
node tests/website_structure.cjs
node tests/website_landing.cjs
node tests/website_maps.cjs
```

The suites cover desktop/tablet/phone layouts, plots, selectors, search, keyboard access, downloads, navigation and history, lazy dataset loading, chapter failure/retry, stable links, and research-question status. Screenshots are written under ignored interim storage.

The [vendored libraries](vendor/README.md) retain their licenses. Noto Sans uses a local sans-serif fallback when Google Fonts is unavailable. Publication is separate from local implementation and verification.
