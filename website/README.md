# Research website

A static research site using native JavaScript modules and vendored D3 and Plotly. Serve the committed `website/` directory:

```powershell
python -m http.server 8000 --bind 127.0.0.1 --directory website
```

Open [the local preview](http://127.0.0.1:8000). The Overview introduces the question and current findings. Findings and limitations connects the evidence across analyses. Method chapters lead with the question and answer, then expose figures, interpretation, and expandable technical detail. Future work retains links for planned methods.

## Content and data ownership

The chapter registry declares title, stable URL slug, navigation group, completion status, dataset dependencies, `render(data)`, and `init(data)`. Each section declares an explicit ID. The router caches successful datasets and mounted views, preserves history and reading position, and contains failures within the requested chapter. Existing method routes remain available.

`data/introduction.json` owns the question wording, stable IDs, statuses, evidence links, and remaining gaps. Measured findings come from topic result bundles; `data/findings.json` is a compact generated synthesis for Overview and Findings. Numeric text uses these exports.

`data/<topic>/` and `assets/<topic>/` are publication copies with ownership manifests. The exporter validates canonical checksums, preserves unowned files, and removes only obsolete owned files. Classification validates complete input/split/target context and shared county profiles before combining its independent notebooks. Identical sample images are shared only when full sample values, columns, and row keys agree.

See the [workflow](../docs/workflow.md#incremental-website-export) for refresh commands and [Adding an analysis](../docs/adding-an-analysis.md) for extension instructions.

## Map context and measurement

The introduction's population-change map uses Vintage 2025 Census estimates and same-vintage 2024–2025 growth. CBSA membership defines metropolitan, micropolitan, and other areas; area growth uses summed populations. Its separate builder records source URLs, retrieval times, and hashes in `data/population-provenance.json`.

EDA covers 2009–2023 with Alaska/Connecticut state substitutes on the map. County-only charts exclude those substitutes. Fixed 2025 display boundaries provide a visual reference; native historical geographies remain in the analysis. Outcome scales use pooled-year 95th percentiles and retain exact tooltip values. Interactive scatter points replace two notebook density charts while retaining all observations.

## Browser verification

Python checks validate exported arithmetic and provenance. Install Playwright in a local development environment and make it available through `NODE_PATH`; `CHROMIUM_EXECUTABLE` can point to an existing Chromium browser. Run:

```powershell
node tests/website_interactions.cjs
node tests/website_supervised.cjs
node tests/website_structure.cjs
```

The suites cover desktop/tablet/phone layouts, plots, selectors, search, keyboard access, downloads, navigation and history, lazy dataset loading, chapter failure/retry, stable links, and research-question status. Screenshots are written under ignored interim storage.

The [vendored libraries](vendor/README.md) retain their licenses. Noto Sans uses a local sans-serif fallback when Google Fonts is unavailable. Publication is separate from local implementation and verification.
