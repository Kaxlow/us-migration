# Notebooks

Notebook names identify topics. Reading order follows the research story; execution follows input dependencies.

| Notebook | Question and input | Result owner |
| --- | --- | --- |
| [Data cleaning](data_cleaning.ipynb) | Combine verified source snapshots and supplements while retaining uncertainty | Processed analysis dataset and cleaning diagnostics |
| [Exploration](exploration.ipynb) | Describe movement and characteristic associations in the validated panel | `exploration` |
| [Clustering](clustering.ipynb) | Compare independent characteristic and migration groupings in 2023 | `clustering` |
| [PCA](pca.ipynb) | Summarize characteristic variation and subsequent migration associations | `pca` |
| [Naive Bayes](naive_bayes.ipynb) | Classify inflow intensity in the shared retrospective 2023 split | `classification/naive-bayes` |
| [Decision trees](decision_trees.ipynb) | Classify outflow intensity and net direction in that split | `classification/decision-trees` |

Read in the order shown. After cleaning creates `data/processed/analysis_county_year.parquet`, all five analytical notebooks run independently. Naive Bayes and decision trees each export their own cohort, split, and target evidence; website packaging validates and combines them.

Reusable implementations live in the Python modules. Notebooks keep the reasoning, parameter choices, estimator fitting, intermediate examples, checks, and measured conclusions visible. Follow the [manual Jupyter workflow](../docs/workflow.md#3-execute-and-inspect-the-notebooks), then [package the affected topic](../docs/workflow.md#incremental-website-export).

Results are staged under ignored interim storage and finalized under `reports/analyses/<topic>/` only after the notebook reaches its export cell. Inspect and save the executed notebook. Numerical evidence is tracked; generated figures remain local and are copied into the website for publication.
