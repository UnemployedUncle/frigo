# Frigo

## Stitch Screenshots

<p align="center">
  <img src="./Stitch/Screenshot/1.png" alt="Frigo Stitch Screenshot 1" width="49%" />
  <img src="./Stitch/Screenshot/2.png" alt="Frigo Stitch Screenshot 2" width="49%" />
</p>
<p align="center">
  <img src="./Stitch/Screenshot/3.png" alt="Frigo Stitch Screenshot 3" width="49%" />
  <img src="./Stitch/Screenshot/4.png" alt="Frigo Stitch Screenshot 4" width="49%" />
</p>

Frigo is a text-first cooking tracker built around a simple flow: parse fridge items from natural language, recommend recipes from the current fridge state, show a per-recipe shopping list, and guide cooking with an auto-advancing timer.

Current product and implementation references:

- [prd3.md](./prd3.md): current product direction
- [current-development-summary.md](./current-development-summary.md): code-based implementation summary
- [prd3.5.md](./prd3.5.md): next cleanup and speed-focused refactoring plan

## Current Scope

Implemented now:

- Home screen with `Saved Recipes`, `Completed Recipes`, cooking grass, and 8 random recipes
- Separate Fridge screen with natural-language input, parsed preview, text fridge layout, editable table, and recommendation item selection
- Separate fridge-based recommendation screen using selected fridge items
- Recipe detail screen with ingredients, shopping list, and full workflow
- Save / unsave on recipe cards and recipe detail
- Cook mode with browser-managed `estimated_seconds` countdown, auto-next-step, pause, resume, stop, and complete
- Completion logging in `cooking_sessions`
- Saved recipe logging in `saved_recipes`
- PostgreSQL-backed recipe, workflow, fridge, and feedback storage
- Local JSONL seed loading into Postgres

Explicitly out of scope now:

- Photo-based input or recommendation
- Weekly meal planning
- Advanced personalization
- Partial cook-session resume

## Product Flow

Main UI flow:

1. Open `/` to review feedback counts, recent cooking grass, and 8 random recipes.
2. Open `/fridge` to add fridge items, review parsed results, edit stored values, and choose ingredients for fridge-based recommendation.
3. Open `/recommendations/fridge` to review recipes based on selected fridge items.
4. Open `/recipes/{recipe_id}` to review ingredients, shopping list, and workflow.
5. Open `/cook/{recipe_id}` to run the timer-driven workflow.
6. Save or complete recipes; Home reflects both counts.

## Runtime Architecture

Core services:

- `FridgeService`: parses natural language and manages fridge items
- `RecipeService`: serves random home recipes and fridge-based recommendation results
- `ShoppingService`: computes missing ingredients from the current fridge
- `WorkflowService`: loads workflow steps from PostgreSQL
- `CookingService`: records completed cooking sessions and builds cooking grass
- `SavedRecipeService`: tracks saved recipes and save state

Runtime principles:

- PostgreSQL is the runtime source of truth
- `workflow_steps` is the workflow source of truth at runtime
- OpenRouter is optional
- UI paths are fallback-first and should still work when OpenRouter is disabled or fails

Runtime tables used by the current app:

- `recipes`
- `workflow_steps`
- `recipe_search_terms`
- `fridge_items`
- `fridge_input_logs`
- `cooking_sessions`
- `saved_recipes`
- `shopping_list_runs`
- `recipe_search_plans`

## Main Routes

UI routes:

- `GET /`: Home
- `GET /fridge`: Fridge page
- `POST /ui/fridge/parse`: fridge natural-language submit
- `POST /ui/fridge/items/{item_id}/update`: fridge item update
- `POST /ui/fridge/items/{item_id}/delete`: fridge item delete
- `POST /recommendations/fridge`: fridge recommendation submit
- `GET /recommendations/fridge`: selected-item recommendation screen
- `GET /recipes/{recipe_id}`: recipe detail
- `POST /recipes/{recipe_id}/save`: save toggle
- `GET /cook/{recipe_id}`: cook mode
- `POST /cook/{recipe_id}/complete`: completion submit

API-like routes still present:

- `POST /fridge/parse`
- `GET /fridge/items`
- `PATCH /fridge/items/{item_id}`
- `DELETE /fridge/items/{item_id}`
- `POST /recipes/recommend`
- `POST /shopping-list`
- `GET /recipes/{recipe_id}/workflow`

Internal or cleanup-candidate routes:

- `POST /ui/recommend`: currently redundant and a cleanup candidate tracked in `prd3.5.md`
- `GET /ui/recipes/{recipe_id}` and `GET /ui/workflow/{recipe_id}`: redirect compatibility helpers

## Environment

This repo currently does not include `.env.example`. Create `.env` manually for local runs.

Current variables:

```env
OPENROUTER_API_KEY=
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=gpt-oss-120b
OPENROUTER_FALLBACK_MODEL=qwen3.5-122b-a10b
DATABASE_URL=postgresql://frigo:frigo@localhost:5432/frigo
APP_ENV=development
```

Model aliases are normalized in `app/config.py`.

Notes:

- Docker Compose overrides `DATABASE_URL` inside the app container to `postgresql://frigo:frigo@db:5432/frigo`
- OpenRouter is optional; fallback parsing and recommendation paths remain available

## Local Run

Start Postgres and the app:

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

Current startup expectations:

1. `.env` is present
2. local seed files exist under `data/`
3. Postgres starts through Docker Compose
4. the app connects to Postgres at container runtime

## Migrations and Seed

Apply SQL migrations:

```bash
python scripts/migrate.py
```

Load local seed files into Postgres:

```bash
python scripts/seed_recipes.py
```

Validate workflow seed shape:

```bash
python scripts/validate_workflows.py
```

What the seed script currently does:

- clears runtime tables
- loads `data/recipes.jsonl`
- loads `data/workflow_steps.jsonl`
- rebuilds `recipe_search_terms`
- inserts demo fridge items
- inserts demo completion records

## Local Data Files

This repository is intended to work without committing raw or seed data to GitHub.

Current local-only seed inputs:

- `data/recipes.jsonl`
- `data/workflow_steps.jsonl`

Useful local metadata if present:

- `data/raw_seed_report.json`
- `data/raw_seed_review.jsonl`
- `data/README.md`

If local seed files are missing, seed and workflow validation scripts fail with a local-data message.

## Natural Language Input

Examples that work well now:

```text
chicken 1 pack today, broccoli 1 bag tomorrow, onion 1, egg 2
```

```text
si geum chi han bong ji i beon ju mal, saeu 200g naeil, beoteo 1gae
```

```text
egg 2 today, chicken broth 1 can, green onion 1, cornstarch 1
```

The parser is most stable when ingredients are separated by commas.

## Recommendation Strategy

Current recommendation behavior:

1. Home uses a random-8 repository path
2. Fridge recommendation uses selected fridge items from the UI
3. selected ingredient names are normalized
4. `recipe_search_terms` is queried for candidate recipe IDs
5. a small candidate set is hydrated from `recipes`
6. results are re-ranked with overlap count and fridge urgency

This is the current path intended to support large recipe data without full-table Python scans.

## Legacy and Deprecated

These still exist for compatibility or cleanup tracking, but they are not primary runtime concepts:

- `workflow_file`: deprecated compatibility field on recipes
- `estimated_minutes`: deprecated compatibility field on workflow rows
- `recipe_search_plans`: persisted plan history exists, but it is not part of the main UI experience
- `data/workflows/`: no longer used at runtime

Archive and legacy references remain under `Archive/`.

## Next Cleanup

The next cleanup and speed-focused refactoring plan is tracked in [prd3.5.md](./prd3.5.md).
