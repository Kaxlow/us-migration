# Do County Characteristics Explain Migration Flows?

This project studies how US counties' economic, demographic, housing, and environmental characteristics accompany domestic migration. Net migration, inflows, and outflows receive equal emphasis as rates per 1,000 ACS residents; counts describe movement volumes.

The evidence includes longitudinal exploration, 2023 county clustering and PCA, and retrospective classification. The [migration atlas and research website](https://kaxlow.github.io/us-migration/landing.html) presents published work. This checkout includes local revisions that will appear there after publication.

## Read the project

Start with the website's Overview and Findings chapters, then follow the linked analyses and supporting detail. The [notebook index](notebooks/README.md) explains the reading order and execution dependencies. [Methodology](docs/methodology.md) defines the analytical design, and the [glossary](docs/data-glossary.md) defines variables and units.

## Local setup and preview

Use the existing `us-migration/` Python environment, or create `.venv/` for a fresh checkout:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m http.server 8000 --bind 127.0.0.1 --directory website
```

Open [the local website](http://127.0.0.1:8000). Its committed static exports support preview independently of the raw downloads.

## Repository responsibilities

| Location | Responsibility |
| --- | --- |
| `data/raw/`, `data/interim/`, `data/processed/` | Immutable snapshots, temporary work, and validated analysis inputs |
| `src/us_migration/` | Reusable transformations, cohort contracts, validation, and export utilities |
| `notebooks/` | Questions, analysis choices, estimator fitting, evidence, and interpretation |
| `reports/analyses/` | Owned numerical result bundles and generated figures, grouped by topic |
| `reports/tables/` | Source and cleaning diagnostics |
| `website/` | Static presentation and packaged publication copies |
| `scripts/` | Acquisition, audits, and website packaging commands |
| `tests/` | Numerical, dependency, export, and browser checks |
| `docs/` | Workflow, methodology, data definitions, and contribution guidance |

## Reproduce or extend

Follow the [workflow](docs/workflow.md) for credentials, downloads, notebook execution, audits, and incremental export. Read [Adding an analysis](docs/adding-an-analysis.md) before extending the research. The three-outcome contract, declared cohorts, and provenance connect results across surfaces.

Run `python -m pytest -q` for Python checks. Browser checks and local preview are documented in the [website guide](website/README.md).

Keep credentials in a local `.env` using [.env.example](.env.example). Source snapshots and processed data remain Git-ignored. Review saved notebook outputs before sharing.

See [CONTRIBUTING.md](CONTRIBUTING.md). Original code and documentation use the [MIT License](LICENSE); source data retain their [documented licenses](docs/data-sources.md).
