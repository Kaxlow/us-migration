# Raw data

Store original, unmodified source files here. Data files are ignored by Git.

Run from the repository root to acquire the source data and cleaning supplements:

```powershell
python scripts/download_data.py --start 2009 --end 2026
python scripts/download_cleaning_support.py
```

Snapshots are stored under source/request directories with SHA-256 filenames
and metadata sidecars. `catalog.json` selects the active snapshots; `runs/`
records acquisition attempts, and `latest_run.json` describes the latest invocation.
Downloads reuse verified snapshots; `--refresh` checks for upstream revisions.
Keep raw snapshots unchanged so processed outputs remain traceable to their inputs.

See [data sources](../../docs/data-sources.md) for source details and
[the workflow](../../docs/workflow.md) for acquisition, provenance, and retry instructions.
