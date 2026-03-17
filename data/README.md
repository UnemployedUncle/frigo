# Local Data Layout

This repository is intended to be pushed to GitHub without raw or seed data.

Keep the following files only on your local machine:

- `Raw/full_dataset.csv`
- `data/recipes.jsonl`
- `data/workflows/*.jsonl`

Required local paths for the current app:

- `data/recipes.jsonl`: seed data for `scripts/seed_recipes.py`
- `data/workflows/*.jsonl`: workflow files for `scripts/validate_workflows.py`

Optional local paths:

- `Raw/full_dataset.csv`: source dataset for raw cleanup scripts
- `Archive/scripts/build_raw_staging_seed.py`: archived one-off staging builder for raw seed cleanup

If these files are missing, seed and workflow validation scripts will fail with a local-data message.
