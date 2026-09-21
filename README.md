# US Migration

Python data science project for exploring migration in the United States.

## Research website

The responsive [research website](website/README.md) presents the introduction,
interactive county maps, data preparation, and ten exploratory charts. Run
`.\us-migration\Scripts\python.exe -m http.server 8000 --bind 127.0.0.1 --directory website`
and open http://127.0.0.1:8000. See its README for independent data-export commands.

## Project scope

- Research question: Which county characteristics are associated with US migration patterns?
- Coverage: 2009 onward, through each source's latest published release; native county geographies.
- Sources: IRS migration, ACS county characteristics and migration flows, FEMA declarations, NOAA county climate.
- Deliverables: immutable raw snapshots, separate cleaned tables, a descriptive county-year panel, and executed EDA notebooks.

## Local setup

The existing local environment is in `us-migration/` and uses Python 3.13.9.
Activate it from the repository root in PowerShell:

```powershell
.\us-migration\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

For a fresh checkout, create an environment first:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

Add dependencies as they become necessary for the analysis.

## API keys

Request a [Census API key](https://api.census.gov/data/key_signup.html) and follow
the emailed activation instructions. If using NOAA Climate Data Online (CDO),
request a [NOAA token](https://www.ncei.noaa.gov/cdo-web/token).
IRS public files, OpenFEMA, and NOAA public bulk downloads do not need these keys.

From the repository root, create your local configuration without overwriting
an existing file:

```powershell
if (-not (Test-Path -LiteralPath .env)) { Copy-Item .env.example .env }
notepad .env
```

Fill in the values in `.env` only:

```dotenv
CENSUS_API_KEY=your_census_key
NOAA_CDO_TOKEN=your_noaa_token
```

Leave the NOAA value blank if using only bulk climate files. `.env` is ignored
by Git; `.env.example` is the shareable template and must contain no secrets.

After installing the requirements, load keys in Python. For a script or notebook
running with the repository root as its working directory:

```python
import os
from dotenv import load_dotenv

load_dotenv(".env")
census_key = os.getenv("CENSUS_API_KEY")
noaa_token = os.getenv("NOAA_CDO_TOKEN")
```

For notebooks running from `notebooks/`, use `load_dotenv("../.env")` instead.
Existing environment variables take precedence. A `.env` file is not loaded
automatically by Python; download scripts must call the loader. Census requests
use the `key` query parameter; CDO requests use a `token` HTTP header.
Avoid printing credentials or logging request URLs containing keys.

Verify Git excludes the local file with `git check-ignore .env` (it should print
`.env`). The downloader loads this file and reports API retrieval errors without printing keys.

## Repository layout

| Path | Purpose |
| --- | --- |
| `data/raw/` | Original source data; ignored by Git |
| `data/interim/` | Intermediate transformations; ignored by Git |
| `data/processed/` | Analysis-ready data; ignored by Git |
| `notebooks/` | Exploratory notebooks |
| `src/us_migration/` | Reusable Python analysis code |
| `scripts/` | Data download, preparation, and execution scripts |
| `tests/` | Tests for reusable code |
| `docs/` | Data sources, methodology, and decisions |
| `reports/` | Written findings and deliverables |
| `reports/figures/` | Generated figures; ignored by Git |
| `models/` | Generated model artifacts; ignored by Git |

## Workflow

```powershell
python scripts/download_data.py --start 2009 --end 2026
python scripts/download_cleaning_support.py
python -m pytest -q
python scripts/run_notebooks.py
python scripts/audit_data.py
```

See [the complete workflow](docs/workflow.md),
[coverage manifest](docs/coverage-manifest.json),
[observed coverage](docs/coverage-observed.csv),
[methodology](docs/methodology.md), and [EDA findings](reports/eda_summary.md).
The [quality/distribution notebook](notebooks/01_data_cleaning.ipynb)
and [correlation notebook](notebooks/02_eda_findings.ipynb) contain saved outputs.
They now demonstrate raw-data cleaning, export an audited missing-free analysis
cohort, and produce ten captioned findings charts. See the
[notebook cleaning guide](docs/notebook-cleaning.md) and
[chart gallery](reports/eda_visualizations.md).
Downloads resume from verified cached snapshots. Use `--refresh` to check for upstream revisions.

Keep credentials in a local `.env` file if needed; document variable names in
`.env.example`. Never commit credentials or sensitive data. Review notebook
outputs before committing them.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

This project's original code and documentation are licensed under the
[MIT License](LICENSE).

Third-party datasets and other third-party materials remain subject to their
respective licenses. Document source-data licenses in `docs/data-sources.md`.

See [the cleaned-data glossary](docs/data-glossary.md) for variable definitions, units, provenance flags, and event-count semantics.
