from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class FridgeParsedItem(BaseModel):
    name: str
    normalized_name: str
    quantity: Optional[float] = None
    unit: Optional[str] = None
    expiry_date: Optional[date] = None


class FridgeParseResponse(BaseModel):
    items: List[FridgeParsedItem]


class RecipeSearchSelection(BaseModel):
    selected_ingredients: List[str]
    query_text: str
    reason: str


class RecipeSearchAgentResponse(BaseModel):
    plan_steps: List[RecipeSearchSelection]


class ShoppingItemAgentModel(BaseModel):
    name: str
    required_quantity: Optional[float] = None
    current_quantity: Optional[float] = None
    unit: Optional[str] = None
    reason: str = Field(pattern="^(missing|insufficient|half_or_less)$")
    must_buy: bool


class ShoppingListAgentResponse(BaseModel):
    items: List[ShoppingItemAgentModel]


class FridgeItemRecord(BaseModel):
    id: str
    name: str
    normalized_name: str
    quantity: Optional[float] = None
    unit: Optional[str] = None
    expiry_date: Optional[date] = None
    days_left: Optional[int] = None
    source_text_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class RecipeRecord(BaseModel):
    id: str
    title: str
    cuisine: str
    summary: str
    servings: int
    primary_ingredients: List[str]
    required_ingredients: List[dict]
    optional_ingredients: List[dict]
    search_keywords: List[str]
    workflow_file: str


class SearchPlanRecord(BaseModel):
    id: str
    attempt_no: int
    selected_ingredients: List[str]
    query_text: str
    reason: str
    result_count: int
    next_step: Optional[str] = None


class WorkflowStep(BaseModel):
    recipe_id: str
    step_number: int
    title: str
    description: str
    ingredients: List[str]
    tool: str
    estimated_minutes: int


class RecommendResponse(BaseModel):
    plan_steps: List[SearchPlanRecord]
    recipes: List[RecipeRecord]


class ShoppingListResponse(BaseModel):
    recipe_id: str
    shopping_items: List[ShoppingItemAgentModel]


class WorkflowResponse(BaseModel):
    recipe: RecipeRecord
    steps: List[WorkflowStep]
