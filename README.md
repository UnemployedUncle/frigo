# Frigo

Frigo is a text-first cooking tracker. The service takes fridge items from natural language, recommends recipes from the current fridge state, shows a per-recipe shopping list, and runs step-by-step cooking with an auto-advancing timer.

The current product direction is documented in [prd2.md](/Users/yongsupyi/Desktop/frigo/prd2.md). This README is focused on the codebase as it exists now.

## Current Scope

Implemented now:

- Text-first Home screen with cooking grass and 8 recipe recommendations
- Separate Fridge screen with natural-language input, text fridge layout, and editable table
- Recipe detail screen with ingredients, shopping list, and full workflow
- Cook mode with `estimated_seconds` countdown, auto-next-step, pause/resume/stop
- Completion logging in `cooking_sessions`
- PostgreSQL-backed workflow storage
- Large local seed loading from JSONL into Postgres

Explicitly out of scope now:

- Photo-based UI
- Weekly meal planning
- Advanced personalization
- Partial cook-session resume

## Product Flow

The main user flow is:

1. Open `/` to see cooking grass and recommended recipes.
2. Open `/fridge` to add or edit fridge items.
3. Open `/recipes/{recipe_id}` to review ingredients, shopping list, and workflow.
4. Open `/cook/{recipe_id}` to run the timer-driven workflow.
5. Complete the recipe and save a `cooking_sessions` record.

## Runtime Architecture

Core services:

- `FridgeService`: parses natural language and manages fridge items
- `RecipeService`: recommends recipes using indexed ingredient overlap
- `ShoppingService`: computes missing ingredients from the current fridge
- `WorkflowService`: reads workflow steps from the database
- `CookingService`: records completed cooking sessions

Storage:

- PostgreSQL is the runtime database
- `recipes` stores recipe metadata
- `workflow_steps` stores all workflow rows
- `recipe_search_terms` is the search index for fast recommendation lookup
- `fridge_items` stores current fridge inventory
- `cooking_sessions` stores completed cooking runs

Important change:

- Workflow execution no longer depends on `data/workflows/*.jsonl`
- Runtime now reads from the `workflow_steps` table
- If `data/workflows` still exists locally, it is legacy data and can be deleted

## Main Routes

UI routes:

- `GET /`: Home
- `GET /fridge`: Fridge page
- `POST /ui/fridge/parse`: fridge natural-language form submit
- `POST /ui/fridge/items/{item_id}/update`: fridge item update
- `POST /ui/fridge/items/{item_id}/delete`: fridge item delete
- `GET /recipes/{recipe_id}`: recipe detail
- `GET /cook/{recipe_id}`: cook mode
- `POST /cook/{recipe_id}/complete`: save completion record

API-like routes still present:

- `POST /fridge/parse`
- `GET /fridge/items`
- `PATCH /fridge/items/{item_id}`
- `DELETE /fridge/items/{item_id}`
- `POST /recipes/recommend`
- `POST /shopping-list`
- `GET /recipes/{recipe_id}/workflow`

## Environment

Copy `.env.example`:

```bash
cp .env.example .env
```

Current variables:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=gpt-oss-120b
OPENROUTER_FALLBACK_MODEL=Qwen3.5-122B-A10B
DATABASE_URL=postgresql://frigo:frigo@localhost:5432/frigo
```

Model aliases are normalized in [config.py](/Users/yongsupyi/Desktop/frigo/app/config.py):

- `gpt-oss-120b` -> `openai/gpt-oss-120b:free`
- `Qwen3.5-122B-A10B` -> `qwen/qwen3.5-122b-a10b`

OpenRouter is optional. If the API call fails or is disabled, the app falls back to deterministic local parsing/recommendation logic.

## Local Run

Start the app and Postgres:

```bash
docker compose up --build
```

Background mode:

```bash
docker compose up --build -d
```

Stop:

```bash
docker compose down
```

After startup, the app is available at:

- `http://localhost:8000`

On container start, the app runs:

1. DB migrations
2. recipe/workflow seed load
3. workflow validation
4. FastAPI via Uvicorn

## Seed and Data Files

This repository uses local-only seed files under `data/`.

Current seed inputs:

- [recipes.jsonl](/Users/yongsupyi/Desktop/frigo/data/recipes.jsonl)
- [workflow_steps.jsonl](/Users/yongsupyi/Desktop/frigo/data/workflow_steps.jsonl)

Current local artifacts:

- [raw_seed_report.json](/Users/yongsupyi/Desktop/frigo/data/raw_seed_report.json)
- [raw_seed_review.jsonl](/Users/yongsupyi/Desktop/frigo/data/raw_seed_review.jsonl)

Current local generated full seed, based on `Raw/full_dataset.csv`:

- raw rows scanned: `2,231,142`
- accepted recipes: `2,231,111`
- excluded rows: `31`
- workflow steps: `14,631,812`

DB load status currently verified:

- `recipes`: `2,231,111`
- `workflow_steps`: `14,631,812`
- `recipe_search_terms`: `24,558,436`
- `fridge_items`: `9`
- `cooking_sessions`: `4`

## Large Seed Workflow

The one-off full-seed builder is:

- [raw_full_seed_builder.ipynb](/Users/yongsupyi/Desktop/frigo/notebooks/raw_full_seed_builder.ipynb)

It reads `Raw/full_dataset.csv` in streaming mode and generates:

- `data/recipes.jsonl`
- `data/workflow_steps.jsonl`
- `data/raw_seed_review.jsonl`
- `data/raw_seed_report.json`

It also backs up the previous local seed under:

- `Archive/seed_backup_*`

This replaced the old “one workflow file per recipe” idea. For large data, workflows are stored as rows in `workflow_steps`, not as millions of files.

## Loading Seed into Postgres

Load local seed files into Postgres:

```bash
docker compose run --rm -T -v "$PWD:/app" app python scripts/seed_recipes.py
```

What the seed script does:

- clears runtime tables
- loads `recipes.jsonl`
- loads `workflow_steps.jsonl`
- rebuilds `recipe_search_terms`
- inserts demo fridge items
- inserts demo completion records

Workflow validation:

```bash
python scripts/validate_workflows.py
```

This validates `data/workflow_steps.jsonl` by default. Directory-based validation remains only for explicit legacy use.

## Natural Language Input

Examples that work well now:

```text
chicken 1 pack today, broccoli 1 bag tomorrow, onion 1, egg 2
```

```text
시금치 한 봉지 이번 주말, 새우 200g 내일, 버터 1개
```

```text
egg 2 today, chicken broth 1 can, green onion 1, cornstarch 1
```

The parser is most stable when ingredients are separated by commas.

## Recommendation Strategy

Recommendation no longer scans all recipes in Python.

Current strategy:

1. Normalize fridge terms
2. Query `recipe_search_terms`
3. Get candidate recipe IDs by overlap count
4. Hydrate a small candidate set from `recipes`
5. Re-rank with fridge urgency and return top results

This is the current path that supports million-scale recipe data.

## Legacy Files

These remain in the repo or local workspace as legacy/reference material:

- `Archive/`: exploration docs, references, seed backups, old examples
- `workflow_file`: deprecated recipe compatibility field
- `estimated_minutes`: deprecated workflow compatibility field

They are not part of the current main data flow unless explicitly used for reference.

## GitHub Policy

This repository is intentionally configured so large local data does not get pushed.

Ignored local-only assets include:

- `Raw/`
- `data/*` except lightweight placeholders/docs
- `notebooks/`
- `Archive/seed_backup_*`

That means generated seed outputs such as:

- `data/recipes.jsonl`
- `data/workflow_steps.jsonl`
- `data/raw_seed_report.json`
- `data/raw_seed_review.jsonl`

stay local and are not uploaded to GitHub.

## Tests and Verification

Useful commands:

```bash
python scripts/validate_workflows.py
```

```bash
docker compose run --rm -T -v "$PWD:/app" app python -m unittest discover -s tests -p 'test_*.py'
```

```bash
docker exec frigo-db-1 psql -U frigo -d frigo -c "select count(*) from recipes;"
```

## References

- Product spec: [prd2.md](/Users/yongsupyi/Desktop/frigo/prd2.md)
- Earlier MVP spec: [prd.md](/Users/yongsupyi/Desktop/frigo/prd.md)
- Text UI reference: [260317_textRepresentation.md](/Users/yongsupyi/Desktop/frigo/Archive/260317_textRepresentation.md)
- Archived notes: [Archive](/Users/yongsupyi/Desktop/frigo/Archive)
