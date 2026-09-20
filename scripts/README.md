# Scripts

- `download_data.py --start 2009 --end 2026`: acquire official data and immutable raw snapshots; supports `--sources` and `--refresh`.
- `clean_data.py --start 2009 --end 2026`: execute the authoritative cleaning notebook, save outputs, and export source audit tables and the imputed downstream dataset.
- `run_notebooks.py`: execute both EDA notebooks offline and save their outputs.
- `audit_data.py`: verify hashes/state shards, export observed coverage, and summarize EDA findings.
- `build_notebooks.py`: regenerate only the ten-chart notebook (clears its outputs); validate and preserve the authoritative cleaning notebook.
- `notebook_chart_cells.py`: editable source for the ten chart cells used by the generator.
- `download_cleaning_support.py`: acquire state ACS/IRS/NOAA supplements and the Census tribal/county relationship file.

Run with the repo Python environment. See [workflow](../docs/workflow.md) for full commands, inputs, outputs, and limitations.
