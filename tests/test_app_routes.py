import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient

import app.main as main_module


class FakeFridgeService:
    def __init__(self):
        self.items = [
            {
                "id": "item-1",
                "name": "Spinach",
                "normalized_name": "spinach",
                "quantity": 1.0,
                "unit": "bag",
                "expiry_date": None,
                "days_left": 1,
            },
            {"id": "item-2", "name": "Shrimp", "normalized_name": "shrimp", "quantity": 200.0, "unit": "g", "expiry_date": None, "days_left": 0},
            {"id": "item-3", "name": "Butter", "normalized_name": "butter", "quantity": 1.0, "unit": "block", "expiry_date": None, "days_left": 4},
            {"id": "item-4", "name": "Garlic", "normalized_name": "garlic", "quantity": 3.0, "unit": "cloves", "expiry_date": None, "days_left": 6},
            {"id": "item-5", "name": "Onion", "normalized_name": "onion", "quantity": 1.0, "unit": "", "expiry_date": None, "days_left": 3},
        ]
        self.logged_texts = []

    def parse_and_store(self, raw_text):
        self.logged_texts.append(raw_text)
        created = {
            "id": "item-6",
            "name": "Mushroom",
            "normalized_name": "mushroom",
            "quantity": 1.0,
            "unit": "pack",
            "expiry_date": None,
            "days_left": 0,
        }
        self.items.append(created)
        return type("ParseResult", (), {"source_text_id": "log-1", "items": [created]})()

    def list_items(self):
        return list(self.items)

    def update_item(self, item_id, payload):
        for item in self.items:
            if item["id"] == item_id:
                item.update(payload)
                return
        raise ValueError(f"Item not found: {item_id}")

    def delete_item(self, item_id):
        self.items = [item for item in self.items if item["id"] != item_id]


class FakeRecipeService:
    def __init__(self):
        self.plan_steps = [
            {
                "id": "plan-1",
                "attempt_no": 1,
                "selected_ingredients": ["Spinach", "Shrimp", "Butter"],
                "query_text": "Spinach Shrimp Butter",
                "reason": "fallback selection",
                "result_count": 1,
                "next_step": None,
            }
        ]
        self.recipes = [
            {
                "id": "recipe-1",
                "title": "Garlic Shrimp Pasta",
                "cuisine": "Western",
                "summary": "Shrimp pasta",
                "servings": 2,
                "primary_ingredients": ["Shrimp", "Garlic"],
                "required_ingredients": [],
                "optional_ingredients": [],
                "search_keywords": ["shrimp", "garlic"],
            }
        ]

    def list_random_recipes(self, limit=8):
        return self.recipes[:limit]

    def recommend_from_selected_items(self, fridge_items, limit=8):
        return self.plan_steps, self.recipes[:limit]

    def recommend(self, fridge_items, limit=5, force_fallback=False, minimum_overlap=None, persist_plan=True):
        return self.plan_steps, self.recipes


class FakeShoppingService:
    def build_for_recipe(self, recipe_id, fridge_items, persist=True, force_fallback=False):
        if recipe_id != "recipe-1":
            raise ValueError(f"Recipe not found: {recipe_id}")
        return {
            "id": "shopping-1",
            "recipe_id": recipe_id,
            "shopping_items": [
                {
                    "name": "Garlic",
                    "required_quantity": 2,
                    "current_quantity": 0,
                    "unit": "cloves",
                    "reason": "missing",
                    "must_buy": True,
                }
            ],
        }


class FakeWorkflowService:
    def get_workflow(self, recipe_id):
        if recipe_id != "recipe-1":
            raise ValueError(f"Recipe not found: {recipe_id}")
        return {
            "recipe": {
                "id": recipe_id,
                "title": "Garlic Shrimp Pasta",
                "cuisine": "Western",
                "summary": "Shrimp pasta",
                "servings": 2,
                "primary_ingredients": ["Shrimp", "Garlic"],
                "required_ingredients": [],
                "optional_ingredients": [],
                "search_keywords": ["shrimp", "garlic"],
            },
            "steps": [
                {
                    "recipe_id": recipe_id,
                    "step_number": 1,
                    "title": "Boil",
                    "description": "Boil the pasta.",
                    "ingredients": ["Pasta"],
                    "tool": "pot",
                    "estimated_seconds": 8,
                },
                {
                    "recipe_id": recipe_id,
                    "step_number": 2,
                    "title": "Saute",
                    "description": "Cook the shrimp with garlic.",
                    "ingredients": ["Shrimp", "Garlic"],
                    "tool": "pan",
                    "estimated_seconds": 5,
                },
            ],
        }


class FakeCookingService:
    def __init__(self):
        self.completed = []

    def completion_grass(self, days=14):
        base = [
            {"date": "2026-03-10", "count": 0, "label": "Mon", "iso_date": "2026-03-10"},
            {"date": "2026-03-11", "count": 1, "label": "Tue", "iso_date": "2026-03-11"},
            {"date": "2026-03-12", "count": 0, "label": "Wed", "iso_date": "2026-03-12"},
            {"date": "2026-03-13", "count": 2, "label": "Thu", "iso_date": "2026-03-13"},
            {"date": "2026-03-14", "count": 0, "label": "Fri", "iso_date": "2026-03-14"},
            {"date": "2026-03-15", "count": 1, "label": "Sat", "iso_date": "2026-03-15"},
            {"date": "2026-03-16", "count": 0, "label": "Sun", "iso_date": "2026-03-16"},
        ]
        return base

    def recent_completed(self, limit=4):
        return [
            {
                "id": "session-1",
                "recipe_id": "recipe-1",
                "title": "Garlic Shrimp Pasta",
                "summary": "Shrimp pasta",
                "primary_ingredients": ["Shrimp", "Garlic"],
                "completed_at": datetime(2026, 3, 15, 19, 0, tzinfo=timezone.utc),
                "actual_seconds": 13,
            }
        ]

    def home_summary_counts(self):
        return {"completed_count": 7}

    def complete_recipe(self, recipe_id, actual_seconds):
        self.completed.append((recipe_id, actual_seconds))


class FakeSavedRecipeService:
    def __init__(self):
        self.saved = set()

    def count_saved(self):
        return len(self.saved)

    def is_saved(self, recipe_id):
        return recipe_id in self.saved

    def saved_map(self, recipe_ids):
        return {recipe_id: recipe_id in self.saved for recipe_id in recipe_ids}

    def toggle(self, recipe_id):
        if recipe_id in self.saved:
            self.saved.remove(recipe_id)
            return False
        self.saved.add(recipe_id)
        return True


class AppRoutesTest(unittest.TestCase):
    def setUp(self):
        self.fridge_service = FakeFridgeService()
        self.recipe_service = FakeRecipeService()
        self.shopping_service = FakeShoppingService()
        self.workflow_service = FakeWorkflowService()
        self.cooking_service = FakeCookingService()
        self.saved_recipe_service = FakeSavedRecipeService()
        self.patchers = [
            patch.object(main_module, "fridge_service", self.fridge_service),
            patch.object(main_module, "recipe_service", self.recipe_service),
            patch.object(main_module, "shopping_service", self.shopping_service),
            patch.object(main_module, "workflow_service", self.workflow_service),
            patch.object(main_module, "cooking_service", self.cooking_service),
            patch.object(main_module, "saved_recipe_service", self.saved_recipe_service),
        ]
        for patcher in self.patchers:
            patcher.start()
        self.client = TestClient(main_module.app)

    def tearDown(self):
        for patcher in reversed(self.patchers):
            patcher.stop()

    def test_fridge_parse_update_and_delete_routes(self):
        response = self.client.post("/fridge/parse", json={"raw_text": "Spinach 1 bag tomorrow"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["source_text_id"], "log-1")
        self.assertEqual(len(self.fridge_service.items), 6)

        ui_response = self.client.post("/ui/fridge/parse", data={"raw_text": "Shrimp 200g today"})
        self.assertEqual(ui_response.status_code, 200)
        self.assertIn("PARSED PREVIEW", ui_response.text)

        response = self.client.patch(
            "/fridge/items/item-1",
            json={"name": "Baby Spinach", "quantity": 2, "unit": "bag", "expiry_date": None},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.fridge_service.items[0]["name"], "Baby Spinach")

        response = self.client.delete("/fridge/items/item-1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(self.fridge_service.items), 6)

    def test_recommend_shopping_and_workflow_routes(self):
        recommend_response = self.client.post("/recipes/recommend")
        self.assertEqual(recommend_response.status_code, 200)
        payload = recommend_response.json()
        self.assertEqual(len(payload["plan_steps"]), 1)
        self.assertEqual(payload["recipes"][0]["id"], "recipe-1")

        shopping_response = self.client.post("/shopping-list", json={"recipe_id": "recipe-1"})
        self.assertEqual(shopping_response.status_code, 200)
        self.assertEqual(shopping_response.json()["shopping_items"][0]["reason"], "missing")

        workflow_response = self.client.get("/recipes/recipe-1/workflow")
        self.assertEqual(workflow_response.status_code, 200)
        self.assertEqual(len(workflow_response.json()["steps"]), 2)

    def test_ui_workflow_navigation_and_not_found_handling(self):
        home_response = self.client.get("/")
        self.assertEqual(home_response.status_code, 200)
        self.assertIn("HOME SUMMARY", home_response.text)
        self.assertIn("Saved Recipes", home_response.text)
        self.assertIn("Completed Recipes", home_response.text)
        self.assertIn("COOKING GRASS", home_response.text)
        self.assertNotIn("IN YOUR FRIDGE", home_response.text)
        self.assertNotIn("NATURAL INPUT", home_response.text)

        fridge_response = self.client.get("/fridge")
        self.assertEqual(fridge_response.status_code, 200)
        self.assertIn("TEXT FRIDGE", fridge_response.text)
        self.assertIn("NATURAL INPUT", fridge_response.text)
        self.assertIn("SELECT 5 INGREDIENTS FOR RECOMMENDATION", fridge_response.text)

        bad_recommend_response = self.client.post("/recommendations/fridge", data={"item_ids": ["item-1"]})
        self.assertEqual(bad_recommend_response.status_code, 200)
        self.assertIn("정확히 5개 선택해주세요", bad_recommend_response.text)

        detail_response = self.client.get("/recipes/recipe-1")
        self.assertEqual(detail_response.status_code, 200)
        self.assertIn("RECIPE DETAIL", detail_response.text)
        self.assertIn("SHOPPING LIST", detail_response.text)
        self.assertIn("Save", detail_response.text)

        save_response = self.client.post("/recipes/recipe-1/save", data={"redirect_to": "/"}, follow_redirects=False)
        self.assertEqual(save_response.status_code, 303)
        self.assertTrue(self.saved_recipe_service.is_saved("recipe-1"))

        recommend_response = self.client.get("/recommendations/fridge?item_ids=item-1&item_ids=item-2&item_ids=item-3&item_ids=item-4&item_ids=item-5")
        self.assertEqual(recommend_response.status_code, 200)
        self.assertIn("FRIDGE RECOMMENDATIONS", recommend_response.text)
        self.assertIn("Garlic Shrimp Pasta", recommend_response.text)

        response = self.client.get("/cook/recipe-1?step=2")
        self.assertEqual(response.status_code, 200)
        self.assertIn("COOKING MODE", response.text)
        self.assertIn("Total remaining", response.text)
        self.assertIn("Pause", response.text)
        self.assertIn("Resume", response.text)
        self.assertIn("Stop", response.text)

        complete_response = self.client.post("/cook/recipe-1/complete", data={"actual_seconds": 13}, follow_redirects=False)
        self.assertEqual(complete_response.status_code, 303)
        self.assertEqual(self.cooking_service.completed, [("recipe-1", 13)])

        shopping_not_found = self.client.post("/shopping-list", json={"recipe_id": "missing"})
        self.assertEqual(shopping_not_found.status_code, 404)

        workflow_not_found = self.client.get("/recipes/missing/workflow")
        self.assertEqual(workflow_not_found.status_code, 404)


if __name__ == "__main__":
    unittest.main()
