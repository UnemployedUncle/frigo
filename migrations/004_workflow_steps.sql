CREATE TABLE IF NOT EXISTS workflow_steps (
    recipe_id TEXT NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    ingredients JSONB NOT NULL,
    tool TEXT NOT NULL,
    estimated_seconds INTEGER NOT NULL,
    estimated_minutes INTEGER NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (recipe_id, step_number)
);

CREATE INDEX IF NOT EXISTS workflow_steps_recipe_id_idx
    ON workflow_steps (recipe_id);
