# Contributing

Follow the [workflow](docs/workflow.md) for environment setup, data preparation,
manual Jupyter execution, and export. Use the [extension guide](docs/adding-an-analysis.md)
to add an independently owned analysis topic.

Keep reusable logic in the Python package and analysis choices, fitted estimators,
evidence, and interpretation in notebooks. Document scientific choices in the
methodology and variable definitions in the glossary. Preserve source provenance,
cohort definitions, numeric precision, and leading zeros in geographic identifiers.

Run `python -m pytest -q` for reusable code and export changes. Execute and save
affected notebooks when computation changes. Run the relevant [browser suites](website/README.md#browser-verification)
for website changes. Match the surrounding code style and keep changes focused.

Review saved notebook outputs and generated publication artifacts before committing.
Summarize the behavior changed, the evidence preserved, and the checks completed.
Keep credentials and raw/processed source data in their ignored local locations.
