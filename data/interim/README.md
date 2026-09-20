# Interim data

This directory holds local runtime files and temporary intermediate artifacts.
Its contents are ignored by Git, except for this README.

`scripts/run_notebooks.py` creates `jupyter/` for the local kernel registration,
Jupyter runtime files, IPython history, and Matplotlib cache. The cleaning-only
entry point, `scripts/clean_data.py`, uses the same notebook runner.
These runtime files are recreated as needed; they are not analysis datasets.

Final source tables and analysis exports belong in
[data/processed](../processed/README.md). One-time notebook-refactoring scripts
and baseline backups are not required by the current workflow.

See [the workflow](../../docs/workflow.md) for notebook execution instructions.
