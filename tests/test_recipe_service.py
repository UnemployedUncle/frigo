import unittest

from app.services.recipe_service import RecipeService


class FakeAgent:
    def __init__(self, selections):
        self.selections = selections

    def build_selection(self, fridge_items, desired_count):
        return self.selections[desired_count]


class FakeRecipeRepo:
    def __init__(self, recipes):
        self.recipes = recipes

    def search_candidate_recipe_ids(self, terms, min_overlap, limit):
        normalized_terms = set(terms)
        matches = []
        for recipe in self.recipes:
            overlap_count = len(normalized_terms.intersection(set(recipe["search_keywords"])))
            if overlap_count >= min_overlap:
                matches.append({"id": recipe["id"], "overlap_count": overlap_count})
        matches.sort(key=lambda item: (-item["overlap_count"], item["id"]))
        return matches[:limit]

    def get_recipes_by_ids(self, recipe_ids):
        recipes_by_id = {recipe["id"]: recipe for recipe in self.recipes}
        return [recipes_by_id[recipe_id] for recipe_id in recipe_ids if recipe_id in recipes_by_id]


class FakePlanRepo:
    def __init__(self):
        self.steps = []

    def insert_plan_step(self, payload):
        self.steps.append(payload)


class RecipeServiceTest(unittest.TestCase):
    def make_service(self, recipes, selections):
        service = RecipeService()
        service.recipe_repo = FakeRecipeRepo(recipes)
        service.agent = FakeAgent(selections)
        service.plan_repo = FakePlanRepo()
        return service

    def test_recommend_uses_overlap_threshold_and_expiry_bonus(self):
        recipes = [
            {
                "id": "chicken_divan",
                "title": "치킨 디반 브로콜리 베이크",
                "search_keywords": ["닭고기", "브로콜리", "양파"],
            },
            {
                "id": "sesame_ginger_chicken",
                "title": "참깨 생강 치킨",
                "search_keywords": ["닭고기", "간장", "생강"],
            },
            {
                "id": "tuna_macaroni_casserole",
                "title": "참치 마카로니 캐서롤",
                "search_keywords": ["참치", "마카로니", "양파"],
            },
        ]
        selections = {
            4: type(
                "Selection",
                (),
                {
                    "selected_ingredients": ["닭고기", "브로콜리", "양파", "간장"],
                    "query_text": "닭고기 브로콜리 양파 간장",
                    "reason": "fallback selection",
                },
            )()
        }
        fridge_items = [
            {"name": "닭고기", "normalized_name": "닭고기", "days_left": 1},
            {"name": "브로콜리", "normalized_name": "브로콜리", "days_left": 5},
            {"name": "양파", "normalized_name": "양파", "days_left": None},
            {"name": "간장", "normalized_name": "간장", "days_left": None},
        ]

        service = self.make_service(recipes, selections)
        plan_steps, recommended = service.recommend(fridge_items)

        self.assertEqual(len(plan_steps), 1)
        self.assertEqual(plan_steps[0]["result_count"], 2)
        self.assertEqual([recipe["id"] for recipe in recommended], ["chicken_divan", "sesame_ginger_chicken"])

    def test_recommend_falls_back_until_overlap_matches(self):
        recipes = [
            {
                "id": "vegetable_beef_soup",
                "title": "비프 채소 수프",
                "search_keywords": ["소고기", "토마토", "채소믹스"],
            }
        ]
        selections = {
            5: type(
                "Selection",
                (),
                {
                    "selected_ingredients": ["감자", "양배추", "우유", "치즈", "버터"],
                    "query_text": "감자 양배추 우유 치즈 버터",
                    "reason": "5-step",
                },
            )(),
            4: type(
                "Selection",
                (),
                {
                    "selected_ingredients": ["감자", "양배추", "우유", "치즈"],
                    "query_text": "감자 양배추 우유 치즈",
                    "reason": "4-step",
                },
            )(),
            3: type(
                "Selection",
                (),
                {
                    "selected_ingredients": ["소고기", "토마토", "채소믹스"],
                    "query_text": "소고기 토마토 채소믹스",
                    "reason": "3-step",
                },
            )(),
        }
        fridge_items = [
            {"name": "감자", "normalized_name": "감자", "days_left": None},
            {"name": "양배추", "normalized_name": "양배추", "days_left": None},
            {"name": "우유", "normalized_name": "우유", "days_left": None},
            {"name": "치즈", "normalized_name": "치즈", "days_left": None},
            {"name": "소고기", "normalized_name": "소고기", "days_left": 2},
        ]

        service = self.make_service(recipes, selections)
        plan_steps, recommended = service.recommend(fridge_items)

        self.assertEqual([step["result_count"] for step in plan_steps], [0, 0, 1])
        self.assertEqual(plan_steps[0]["next_step"], "결과가 없어 4개 조합으로 fallback")
        self.assertEqual(plan_steps[1]["next_step"], "결과가 없어 3개 조합으로 fallback")
        self.assertEqual([recipe["id"] for recipe in recommended], ["vegetable_beef_soup"])

    def test_recommend_allows_single_overlap_for_single_fridge_item(self):
        recipes = [
            {
                "id": "egg_drop_soup",
                "title": "계란 드롭 수프",
                "search_keywords": ["달걀", "치킨브로스", "대파"],
            }
        ]
        selections = {
            1: type(
                "Selection",
                (),
                {
                    "selected_ingredients": ["달걀"],
                    "query_text": "달걀",
                    "reason": "1-step",
                },
            )()
        }
        fridge_items = [{"name": "달걀", "normalized_name": "달걀", "days_left": 1}]

        service = self.make_service(recipes, selections)
        plan_steps, recommended = service.recommend(fridge_items)

        self.assertEqual(len(plan_steps), 1)
        self.assertEqual(plan_steps[0]["result_count"], 1)
        self.assertEqual([recipe["id"] for recipe in recommended], ["egg_drop_soup"])


if __name__ == "__main__":
    unittest.main()
