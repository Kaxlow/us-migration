# Project commands

Run scripts from the repository root with the project Python environment.

| Command | Purpose |
| --- | --- |
| `download_data.py --start 2009 --end 2026` | Acquire verified immutable snapshots; supports `--sources` and `--refresh` |
| `download_cleaning_support.py` | Acquire historical ACS, state supplements, CPI-U, and geographic references |
| `audit_data.py` | Audit source integrity and coverage and refresh the descriptive report |
| `build_population_map.py` | Refresh the separate contextual population-change map |
| `export_cleaning_evidence.py` | Capture saved cleaning evidence into its canonical result bundle |
| `export_website_data.py` | Package all available completed result bundles |
| `export_website_data.py --topics pca` | Refresh one topic and dependent findings |

Supported topics are `cleaning`, `exploration`, `clustering`, `pca`, and `classification`. Classification packages the independently executed Naive Bayes and tree analyses after checking provenance. These commands package results; notebook execution remains in Jupyter.

See the [workflow](../docs/workflow.md) for prerequisites and the [extension guide](../docs/adding-an-analysis.md) for adding a topic.
