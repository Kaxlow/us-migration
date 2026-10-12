# Tests

Run `python -m pytest -q` in the repo environment.
Small offline fixtures check flow direction, suppression and valid negative AGI,
duplicate/conflicting IRS pairs, ACS missing codes and MOEs, NOAA state conversion,
FEMA geography/date handling, missing migration joins, immutable snapshots, cache
reuse, and credential redaction. Real-data diagnostics are in the executed notebooks.

`test_phase2.py` checks the unsupervised input contract, outcome exclusion,
cluster selection and exported summaries, PCA geometry, shared county rows and
executed notebooks. It can validate the committed result exports without raw
source downloads; if the local cleaned Parquet exists, its checksum is checked too.
