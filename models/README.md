# Models

Optional location for generated model artifacts; artifacts are ignored by Git.

Phase 2 uses descriptive clustering and PCA rather than deployed predictors.
The executed estimator code is in notebooks 03 and 04. Their assignments,
PCA coefficients/scores, diagnostics and input provenance are published under
`website/data/phase2/` and its chapter JSON files. See
[Phase 2 methodology](../docs/methodology.md#clustering-and-pca) for cohort, parameters,
evaluation and reproduction instructions. No fitted estimator pickle is needed
by the static website.

## Planned prediction outcomes

Evaluate net migration, inflow, and outflow rates separately using a shared
publication-date-aware temporal/geographic evaluation design. Report per-outcome
baselines and errors on identical evaluation rows. Net-gain/net-loss classification
remains a specifically net-migration question. All contemporaneous migration
counts, rates, derived balances, and migration-cluster labels stay outside the
predictor matrix. The explored 2023 cohort requires fresh evaluation data before
claims of untouched test performance. Estimator implementation and tuning belong
to the later supervised-learning phase.
