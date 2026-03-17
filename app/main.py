from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.schemas import RecommendResponse, ShoppingListResponse, WorkflowResponse
from app.services.fridge_service import FridgeService
from app.services.recipe_service import RecipeService
from app.services.shopping_service import ShoppingService
from app.services.workflow_service import WorkflowService

app = FastAPI(title="Frigo MVP")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

fridge_service = FridgeService()
recipe_service = RecipeService()
shopping_service = ShoppingService()
workflow_service = WorkflowService()


def _render_dashboard(
    request: Request,
    *,
    raw_text: str = "",
    plan_steps: Optional[List[Dict[str, Any]]] = None,
    recipes: Optional[List[Dict[str, Any]]] = None,
    shopping: Optional[Dict[str, Any]] = None,
):
    fridge_items = fridge_service.list_items()
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "raw_text": raw_text,
            "fridge_items": fridge_items,
            "plan_steps": plan_steps or [],
            "recipes": recipes or [],
            "shopping": shopping,
        },
    )


def _raise_not_found(message: str) -> None:
    raise HTTPException(status_code=404, detail=message)


@app.get("/")
def home(request: Request):
    return _render_dashboard(request)


@app.post("/fridge/parse")
def parse_fridge(payload: Dict[str, str]):
    raw_text = payload.get("raw_text", "")
    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="raw_text is required")
    result = fridge_service.parse_and_store(raw_text)
    return {"source_text_id": result.source_text_id, "items": result.items}


@app.get("/fridge/items")
def get_fridge_items():
    return fridge_service.list_items()


@app.patch("/fridge/items/{item_id}")
def patch_fridge_item(item_id: str, payload: Dict[str, Any]):
    fridge_service.update_item(item_id, payload)
    return {"id": item_id, **payload}


@app.delete("/fridge/items/{item_id}")
def delete_fridge_item(item_id: str):
    fridge_service.delete_item(item_id)
    return {"success": True}


@app.post("/recipes/recommend")
def recommend_recipes():
    fridge_items = fridge_service.list_items()
    plan_steps, recipes = recipe_service.recommend(fridge_items)
    return RecommendResponse(plan_steps=plan_steps, recipes=recipes)


@app.post("/shopping-list")
def create_shopping_list(payload: Dict[str, str]):
    recipe_id = payload.get("recipe_id")
    if not recipe_id:
        raise HTTPException(status_code=400, detail="recipe_id is required")
    try:
        shopping = shopping_service.build_for_recipe(recipe_id, fridge_service.list_items())
    except ValueError as exc:
        _raise_not_found(str(exc))
    return ShoppingListResponse(recipe_id=shopping["recipe_id"], shopping_items=shopping["shopping_items"])


@app.get("/recipes/{recipe_id}/workflow")
def get_workflow(recipe_id: str):
    try:
        workflow = workflow_service.get_workflow(recipe_id)
    except ValueError as exc:
        _raise_not_found(str(exc))
    return WorkflowResponse(recipe=workflow["recipe"], steps=workflow["steps"])


@app.post("/ui/fridge/parse")
def ui_parse_fridge(request: Request, raw_text: str = Form(...)):
    fridge_service.parse_and_store(raw_text)
    return RedirectResponse("/", status_code=303)


@app.post("/ui/fridge/items/{item_id}/update")
def ui_update_item(
    item_id: str,
    name: str = Form(...),
    quantity: str = Form(""),
    unit: str = Form(""),
    expiry_date: str = Form(""),
):
    fridge_service.update_item(
        item_id,
        {
            "name": name,
            "quantity": float(quantity) if quantity else None,
            "unit": unit or None,
            "expiry_date": date.fromisoformat(expiry_date) if expiry_date else None,
        },
    )
    return RedirectResponse("/", status_code=303)


@app.post("/ui/fridge/items/{item_id}/delete")
def ui_delete_item(item_id: str):
    fridge_service.delete_item(item_id)
    return RedirectResponse("/", status_code=303)


@app.post("/ui/recommend")
def ui_recommend(request: Request):
    plan_steps, recipes = recipe_service.recommend(fridge_service.list_items())
    return _render_dashboard(request, plan_steps=plan_steps, recipes=recipes)


@app.post("/ui/shopping")
def ui_shopping(request: Request, recipe_id: str = Form(...)):
    plan_steps, recipes = recipe_service.recommend(fridge_service.list_items())
    try:
        shopping = shopping_service.build_for_recipe(recipe_id, fridge_service.list_items())
    except ValueError as exc:
        _raise_not_found(str(exc))
    return _render_dashboard(request, plan_steps=plan_steps, recipes=recipes, shopping=shopping)


@app.get("/ui/workflow/{recipe_id}")
def ui_workflow(request: Request, recipe_id: str, step: int = 1):
    try:
        workflow = workflow_service.get_workflow(recipe_id)
    except ValueError as exc:
        _raise_not_found(str(exc))
    steps = workflow["steps"]
    current_index = max(0, min(step - 1, len(steps) - 1))
    current_step = steps[current_index]
    return templates.TemplateResponse(
        request,
        "workflow.html",
        {
            "recipe": workflow["recipe"],
            "current_step": current_step,
            "total_steps": len(steps),
            "total_minutes": sum(item["estimated_minutes"] for item in steps),
            "prev_step": current_index if current_index > 0 else None,
            "next_step": current_index + 2 if current_index < len(steps) - 1 else None,
        },
    )
