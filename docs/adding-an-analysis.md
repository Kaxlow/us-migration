# Adding an analysis

Choose a stable topic name that describes its research purpose. Add a notebook with that name and declare its research question, inputs, cohort, output owner, and interpretation limits at the start. List reading order and actual prerequisites in the notebook index.

Reuse the cohort and outcome contracts. Put reusable transformations or evaluation routines in the Python package; keep estimator choices, fitting, and interpretation visible in the notebook. Add tests for scientific contracts and observable behavior.

For an owned result bundle, register the topic in `begin_analysis` and the exporter, start a fresh staging directory, and write numerical evidence to its `data/` and figures to `figures/`. End with `finish_analysis`. Include input checksum, cohort identifiers, feature definitions, and relevant split/target specification in the results. Preserve numeric precision and FIPS strings. A failed run leaves the preceding canonical bundle intact.

Add the topic to the exporter CLI and availability list. Define any cross-analysis synthesis explicitly and verify compatible inputs before combining results. Publication cleanup follows ownership manifests; avoid deleting files outside those manifests. Document expected inputs, outputs, and refresh commands.

Create a website chapter exporting `render(data)` and `init(data)`, which may return a cleanup function or a promise for one. Register its group, status, slug, and datasets. Give every top-level section an explicit stable ID. Link it to a stable research-question ID and explain whether the evidence fully or partially addresses that question. Preserve aliases when changing existing section IDs.

Lead with the question and principal measured result. Follow with supporting charts and interpretation, retaining technical detail in expandable sections. Reuse shared components and chart utilities. Refresh the compact findings export when this topic contributes to synthesis.

Run numerical/export tests, execute and save the affected notebook, package its topic, and verify browser behavior at 1440, 768, and 390 pixels. Check downloads, keyboard use, loading errors, deep links, and reading-position restoration. Publication follows the project's separate release decision.
