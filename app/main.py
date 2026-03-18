import json
from datetime import date
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from fastapi import FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.schemas import RecommendResponse, ShoppingListResponse, WorkflowResponse
from app.services.cooking_service import CookingService
from app.services.fridge_service import FridgeService
from app.services.recipe_service import RecipeService
from app.services.saved_recipe_service import SavedRecipeService
from app.services.shopping_service import ShoppingService
from app.services.workflow_service import WorkflowService

app = FastAPI(title="Frigo MVP")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

fridge_service = FridgeService()
recipe_service = RecipeService()
shopping_service = ShoppingService()
workflow_service = WorkflowService()
cooking_service = CookingService()
saved_recipe_service = SavedRecipeService()


def _chunked(values: List[Dict[str, Any]], size: int) -> List[List[Dict[str, Any]]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


def _format_item_label(item: Dict[str, Any]) -> str:
    days_left = item.get("days_left")
    if days_left is None:
        expiry = "OPEN"
    elif days_left <= 1:
        expiry = f"D-{days_left}"
    else:
        expiry = f"D-{days_left}"
    quantity_parts = []
    if item.get("quantity") is not None:
        quantity_value = item["quantity"]
        quantity_parts.append(str(int(quantity_value) if quantity_value == int(quantity_value) else quantity_value))
    if item.get("unit"):
        quantity_parts.append(item["unit"])
    quantity_text = f" ({' '.join(quantity_parts)})" if quantity_parts else ""
    return f"{item['name']}{quantity_text} {expiry}".strip()


def _fridge_status_icon(days_left: Optional[int]) -> str:
    if days_left is None:
        return "·"
    if days_left <= 1:
        return "!"
    if days_left <= 3:
        return "*"
    return "+"


def _build_fridge_layout(fridge_items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, str]]]:
    layout = {"DOOR": [], "FRIDGE": [], "FRIDGE2": [], "DOOR2": [], "FREEZER": []}
    freezer_keywords = {"shrimp", "ice", "dumpling", "frozen"}
    top_bins = ["DOOR", "FRIDGE", "FRIDGE2", "DOOR2"]
    top_index = 0
    for item in fridge_items:
        normalized_name = item.get("normalized_name", "")
        target = "FREEZER" if any(keyword in normalized_name for keyword in freezer_keywords) else top_bins[top_index % len(top_bins)]
        if target != "FREEZER":
            top_index += 1
        layout[target].append(
            {
                "name": item["name"],
                "label": _format_item_label(item),
                "status": _fridge_status_icon(item.get("days_left")),
            }
        )
    return layout


def _render_home(
    request: Request,
):
    grass = cooking_service.completion_grass()
    summary = cooking_service.home_summary_counts()
    saved_count = saved_recipe_service.count_saved()
    recipes = recipe_service.list_random_recipes(limit=8)
    saved_map = saved_recipe_service.saved_map(recipe["id"] for recipe in recipes)
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "grass_rows": _chunked(grass, 7),
            "saved_count": saved_count,
            "completed_count": summary.get("completed_count", 0),
            "recipes": recipes or [],
            "saved_map": saved_map,
        },
    )


def _render_fridge(
    request: Request,
    *,
    raw_text: str = "",
    parsed_preview_items: Optional[List[Dict[str, Any]]] = None,
    selection_error: Optional[str] = None,
):
    fridge_items = fridge_service.list_items()
    return templates.TemplateResponse(
        request,
        "fridge.html",
        {
            "raw_text": raw_text,
            "parsed_preview_items": parsed_preview_items or [],
            "fridge_items": fridge_items,
            "fridge_layout": _build_fridge_layout(fridge_items),
            "selection_error": selection_error,
        },
    )


def _load_selected_fridge_items(item_ids: List[str]) -> List[Dict[str, Any]]:
    fridge_items = fridge_service.list_items()
    if not fridge_items:
        raise ValueError("냉장고에 저장된 재료가 없습니다.")

    if len(fridge_items) < 5:
        return fridge_items

    unique_ids = list(dict.fromkeys(item_ids))
    if len(unique_ids) != 5:
        raise ValueError("재료를 정확히 5개 선택해주세요.")

    by_id = {item["id"]: item for item in fridge_items}
    selected_items = [by_id[item_id] for item_id in unique_ids if item_id in by_id]
    if len(selected_items) != 5:
        raise ValueError("선택한 재료를 다시 확인해주세요.")
    return selected_items


def _render_selected_recommendations(
    request: Request,
    selected_items: List[Dict[str, Any]],
):
    _, recipes = recipe_service.recommend_from_selected_items(selected_items, limit=8)
    saved_map = saved_recipe_service.saved_map(recipe["id"] for recipe in recipes)
    return templates.TemplateResponse(
        request,
        "recommendations.html",
        {
            "selected_items": selected_items,
            "recipes": recipes,
            "saved_map": saved_map,
        },
    )


def _raise_not_found(message: str) -> None:
    raise HTTPException(status_code=404, detail=message)


@app.get("/")
def home(request: Request):
    return _render_home(request)


@app.get("/fridge")
def fridge_page(request: Request):
    return _render_fridge(request)


@app.get("/recommendations/fridge")
def fridge_recommendations_page(request: Request, item_ids: List[str] = Query(default=[])):
    if not item_ids:
        return RedirectResponse("/fridge", status_code=303)
    try:
        selected_items = _load_selected_fridge_items(item_ids)
    except ValueError:
        return RedirectResponse("/fridge", status_code=303)
    return _render_selected_recommendations(request, selected_items)


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


@app.post("/recommendations/fridge")
def fridge_recommendations_submit(request: Request, item_ids: List[str] = Form(default=[])):
    try:
        selected_items = _load_selected_fridge_items(item_ids)
    except ValueError as exc:
        return _render_fridge(request, selection_error=str(exc))
    query_string = urlencode([("item_ids", item["id"]) for item in selected_items])
    return RedirectResponse(f"/recommendations/fridge?{query_string}", status_code=303)


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


@app.get("/recipes/{recipe_id}")
def ui_recipe_detail(request: Request, recipe_id: str):
    try:
        workflow = workflow_service.get_workflow(recipe_id)
        shopping = shopping_service.build_for_recipe(
            recipe_id,
            fridge_service.list_items(),
            persist=False,
            force_fallback=True,
        )
    except ValueError as exc:
        _raise_not_found(str(exc))
    return templates.TemplateResponse(
        request,
        "recipe_detail.html",
        {
            "recipe": workflow["recipe"],
            "steps": workflow["steps"],
            "shopping_items": shopping["shopping_items"],
            "total_seconds": sum(item["estimated_seconds"] for item in workflow["steps"]),
            "is_saved": saved_recipe_service.is_saved(recipe_id),
        },
    )


@app.get("/ui/recipes/{recipe_id}")
def ui_recipe_detail_redirect(recipe_id: str):
    return RedirectResponse(f"/recipes/{recipe_id}", status_code=303)


@app.post("/ui/fridge/parse")
def ui_parse_fridge(request: Request, raw_text: str = Form(...)):
    result = fridge_service.parse_and_store(raw_text)
    return _render_fridge(request, raw_text=raw_text, parsed_preview_items=result.items)


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
    return RedirectResponse("/fridge", status_code=303)


@app.post("/ui/fridge/items/{item_id}/delete")
def ui_delete_item(item_id: str):
    fridge_service.delete_item(item_id)
    return RedirectResponse("/fridge", status_code=303)


@app.post("/ui/recommend")
def ui_recommend(request: Request):
    return _render_home(request)


@app.post("/recipes/{recipe_id}/save")
def ui_toggle_saved_recipe(recipe_id: str, redirect_to: str = Form("/")):
    try:
        saved_recipe_service.toggle(recipe_id)
    except ValueError as exc:
        _raise_not_found(str(exc))
    return RedirectResponse(redirect_to or "/", status_code=303)

@app.get("/cook/{recipe_id}")
def ui_cook(request: Request, recipe_id: str, step: int = 1):
    try:
        workflow = workflow_service.get_workflow(recipe_id)
    except ValueError as exc:
        _raise_not_found(str(exc))
    steps = workflow["steps"]
    current_index = max(0, min(step - 1, len(steps) - 1))
    total_seconds = sum(item["estimated_seconds"] for item in steps)
    return templates.TemplateResponse(
        request,
        "workflow.html",
        {
            "recipe": workflow["recipe"],
            "steps": steps,
            "total_steps": len(steps),
            "total_seconds": total_seconds,
            "initial_step_index": current_index,
            "steps_json": json.dumps(steps, ensure_ascii=False),
            "stop_url": f"/recipes/{recipe_id}",
        },
    )


@app.get("/ui/workflow/{recipe_id}")
def ui_workflow_redirect(recipe_id: str, step: int = 1):
    return RedirectResponse(f"/cook/{recipe_id}?step={step}", status_code=303)


@app.post("/cook/{recipe_id}/complete")
def ui_complete_cook(recipe_id: str, actual_seconds: int = Form(...)):
    try:
        workflow_service.get_workflow(recipe_id)
    except ValueError as exc:
        _raise_not_found(str(exc))
    cooking_service.complete_recipe(recipe_id, actual_seconds)
    return RedirectResponse("/", status_code=303)
