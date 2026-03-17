CREATE TABLE IF NOT EXISTS cooking_sessions (
    id UUID PRIMARY KEY,
    recipe_id TEXT NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    completed_at TIMESTAMPTZ NOT NULL,
    actual_seconds INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS cooking_sessions_completed_at_idx
    ON cooking_sessions (completed_at DESC);

CREATE INDEX IF NOT EXISTS cooking_sessions_recipe_id_idx
    ON cooking_sessions (recipe_id);
