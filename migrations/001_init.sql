CREATE TABLE IF NOT EXISTS fridge_input_logs (
    id UUID PRIMARY KEY,
    raw_text TEXT NOT NULL,
    parsed_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS fridge_items (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    quantity DOUBLE PRECISION NULL,
    unit TEXT NULL,
    expiry_date DATE NULL,
    days_left INTEGER NULL,
    source_text_id UUID NULL REFERENCES fridge_input_logs(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS recipes (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    cuisine TEXT NOT NULL,
    summary TEXT NOT NULL,
    servings INTEGER NOT NULL,
    primary_ingredients JSONB NOT NULL,
    required_ingredients JSONB NOT NULL,
    optional_ingredients JSONB NOT NULL,
    search_keywords JSONB NOT NULL,
    workflow_file TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS recipe_search_plans (
    id UUID PRIMARY KEY,
    attempt_no INTEGER NOT NULL,
    selected_ingredients JSONB NOT NULL,
    query_text TEXT NOT NULL,
    reason TEXT NOT NULL,
    result_count INTEGER NOT NULL,
    next_step TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS shopping_list_runs (
    id UUID PRIMARY KEY,
    recipe_id TEXT NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    shopping_items JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
