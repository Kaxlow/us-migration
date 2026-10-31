# Verification

Run `python -m pytest -q`. The configured test root is `tests/`, keeping ignored interim work outside collection. If Windows restricts temporary directories, pass a fresh repository-local `--basetemp=data/interim/<unique-name>` and `-p no:cacheprovider`.

Offline fixtures check acquisition integrity, parsing, geographic handling, imputation, and cohort validation. Unsupervised and classification tests independently recompute exported summaries and verify selection rules, row membership, PCA geometry, prediction metrics, and tree structure. Workflow checks establish that Python imports are independent of notebook files. Export tests cover topic isolation, incompatible provenance, checksum failures, and ownership-bound cleanup.

Saved notebooks retain executed evidence. Raw/processed inputs remain optional for export-only checks; tests requiring those inputs identify their dependency.

See [browser verification](../website/README.md#browser-verification) for the interactive suites and viewport coverage.
