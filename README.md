# US Migration

Python data science project for exploring migration in the United States.

## Project scope

- Research questions: TODO
- Geographic coverage and time period: TODO
- Data sources and usage terms: TODO
- Planned analyses and deliverables: TODO

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

Dependency files currently contain placeholders. Add packages as they become
necessary and record versions for reproducible analysis.

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

TODO: Document data acquisition, processing, analysis, and test commands once
implemented. No runnable pipeline or test suite exists yet.

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
