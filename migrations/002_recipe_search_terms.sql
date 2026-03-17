CREATE TABLE IF NOT EXISTS recipe_search_terms (
    recipe_id TEXT NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    term TEXT NOT NULL,
    term_weight INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (recipe_id, term)
);

CREATE INDEX IF NOT EXISTS recipe_search_terms_term_idx
    ON recipe_search_terms(term);

CREATE INDEX IF NOT EXISTS recipe_search_terms_term_recipe_idx
    ON recipe_search_terms(term, recipe_id);

CREATE INDEX IF NOT EXISTS recipe_search_terms_recipe_idx
    ON recipe_search_terms(recipe_id);
