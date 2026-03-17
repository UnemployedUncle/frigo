import unittest
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
            }
        ]
        self.logged_texts = []

    def parse_and_store(self, raw_text):
        self.logged_texts.append(raw_text)
        created = {
            "id": "item-2",
            "name": "Shrimp",
            "normalized_name": "shrimp",
            "quantity": 200.0,
            "unit": "g",
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
                "workflow_file": "data/workflows/garlic_shrimp_pasta.jsonl",
            }
        ]

    def recommend(self, fridge_items):
        return self.plan_steps, self.recipes


class FakeShoppingService:
    def build_for_recipe(self, recipe_id, fridge_items):
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
                "workflow_file": "data/workflows/garlic_shrimp_pasta.jsonl",
            },
            "steps": [
                {
                    "recipe_id": recipe_id,
                    "step_number": 1,
                    "title": "Boil",
                    "description": "Boil the pasta.",
                    "ingredients": ["Pasta"],
                    "tool": "pot",
                    "estimated_minutes": 10,
                },
                {
                    "recipe_id": recipe_id,
                    "step_number": 2,
                    "title": "Saute",
                    "description": "Cook the shrimp with garlic.",
                    "ingredients": ["Shrimp", "Garlic"],
                    "tool": "pan",
                    "estimated_minutes": 5,
                },
            ],
        }


class AppRoutesTest(unittest.TestCase):
    def setUp(self):
        self.fridge_service = FakeFridgeService()
        self.recipe_service = FakeRecipeService()
        self.shopping_service = FakeShoppingService()
        self.workflow_service = FakeWorkflowService()
        self.patchers = [
            patch.object(main_module, "fridge_service", self.fridge_service),
            patch.object(main_module, "recipe_service", self.recipe_service),
            patch.object(main_module, "shopping_service", self.shopping_service),
            patch.object(main_module, "workflow_service", self.workflow_service),
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
        self.assertEqual(len(self.fridge_service.items), 2)

        response = self.client.patch(
            "/fridge/items/item-1",
            json={"name": "Baby Spinach", "quantity": 2, "unit": "bag", "expiry_date": None},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.fridge_service.items[0]["name"], "Baby Spinach")

        response = self.client.delete("/fridge/items/item-1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(self.fridge_service.items), 1)

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
        response = self.client.get("/ui/workflow/recipe-1?step=2")
        self.assertEqual(response.status_code, 200)
        self.assertIn("2단계. Saute", response.text)

        shopping_not_found = self.client.post("/shopping-list", json={"recipe_id": "missing"})
        self.assertEqual(shopping_not_found.status_code, 404)

        workflow_not_found = self.client.get("/recipes/missing/workflow")
        self.assertEqual(workflow_not_found.status_code, 404)


if __name__ == "__main__":
    unittest.main()
