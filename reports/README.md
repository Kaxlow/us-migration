# Research evidence

`analyses/<topic>/` contains canonical numerical results in `data/`, generated images in `figures/`, and a file ownership/checksum manifest. Classification has separate `naive-bayes` and `decision-trees` owners. The website contains intentional publication copies of these bundles.

`tables/` contains source and cleaning diagnostics. [The EDA summary](eda_summary.md) combines acquisition integrity, coverage, and descriptive associations. [The chart gallery](eda_visualizations.md) links the ten exploratory findings charts.

An analytical notebook finalizes its bundle after successful computation. Website packaging refreshes selected topics and their dependent synthesis, validating manifests before changing publication files. Cleanup removes only previously recorded files within an owner's directories; unrelated files remain intact.

Numerical evidence and manifests are tracked. Generated canonical figures are ignored and recreated by notebook execution. A fresh checkout can preview the committed website; regenerating its artifacts requires the documented inputs and notebook runs.

See [workflow](../docs/workflow.md), [methodology](../docs/methodology.md), and [variable definitions](../docs/data-glossary.md).
