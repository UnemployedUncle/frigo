import argparse
import ast
import csv
import json
import re
import shutil
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


DISPLAY_INGREDIENT_LIMIT = 3
SEARCH_KEYWORD_LIMIT = 15
DEFAULT_SERVINGS = 4
DEFAULT_STEP_MINUTES = 5
COOKING_VERBS = {
    "add",
    "arrange",
    "bake",
    "beat",
    "blend",
    "boil",
    "broil",
    "brown",
    "combine",
    "cook",
    "cover",
    "drain",
    "drop",
    "fold",
    "fry",
    "heat",
    "knead",
    "let",
    "marinate",
    "mix",
    "place",
    "pour",
    "preheat",
    "roast",
    "saute",
    "serve",
    "simmer",
    "stir",
    "top",
    "whisk",
}
UNITS = {
    "c",
    "cup",
    "cups",
    "t",
    "tbsp",
    "tbsp.",
    "tablespoon",
    "tablespoons",
    "teaspoon",
    "teaspoons",
    "tsp",
    "tsp.",
    "oz",
    "oz.",
    "ounce",
    "ounces",
    "lb",
    "lb.",
    "lbs",
    "lbs.",
    "pound",
    "pounds",
    "pkg",
    "pkg.",
    "package",
    "packages",
    "can",
    "cans",
    "jar",
    "jars",
    "carton",
    "cartons",
    "bottle",
    "bottles",
    "box",
    "boxes",
    "bag",
    "bags",
    "envelope",
    "envelopes",
    "clove",
    "cloves",
    "slice",
    "slices",
    "stick",
    "sticks",
    "dash",
    "dashes",
    "pinch",
    "pinches",
    "qt",
    "qt.",
    "quart",
    "quarts",
    "pt",
    "pt.",
    "pint",
    "pints",
    "gal",
    "gal.",
    "gallon",
    "gallons",
}
TOOL_KEYWORDS = [
    ("slow cooker", "slow cooker"),
    ("bake", "oven"),
    ("broil", "oven"),
    ("roast", "oven"),
    ("oven", "oven"),
    ("skillet", "pan"),
    ("fry", "pan"),
    ("pan", "pan"),
    ("saucepan", "pot"),
    ("pot", "pot"),
    ("boil", "pot"),
    ("simmer", "pot"),
    ("bowl", "bowl"),
    ("mix", "bowl"),
    ("combine", "bowl"),
]
PREP_PATTERNS = [
    r",?\s*cut up$",
    r",?\s*cubed$",
    r",?\s*softened$",
    r",?\s*melted$",
    r",?\s*drained$",
    r",?\s*chopped$",
    r",?\s*sliced$",
    r",?\s*diced$",
    r",?\s*beaten$",
    r",?\s*divided$",
    r",?\s*cooked$",
    r",?\s*uncooked$",
    r",?\s*thawed$",
    r",?\s*firmly packed$",
    r",?\s*packed$",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build staging recipe/workflow seed from Raw/full_dataset.csv")
    parser.add_argument("--limit", type=int, default=100, help="Number of rows to inspect from the raw CSV")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("Raw/full_dataset.csv"),
        help="Path to raw CSV file",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/staging/raw_first_100"),
        help="Directory for staging outputs",
    )
    return parser.parse_args()


def safe_parse_list(value: str) -> Tuple[List[Any], Optional[str]]:
    if value is None:
        return [], "empty value"
    text = str(value).strip()
    if not text:
        return [], "empty string"
    for parser in (ast.literal_eval, json.loads):
        try:
            parsed = parser(text)
            if isinstance(parsed, list):
                return parsed, None
        except Exception:
            continue
    return [], "failed to parse list"


def slugify(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"['’]", "", lowered)
    lowered = re.sub(r"[^a-z0-9]+", "_", lowered)
    return lowered.strip("_") or "recipe"


def normalize_term(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def dedupe_preserve(values: Sequence[str], *, max_items: Optional[int] = None) -> List[str]:
    seen = set()
    result: List[str] = []
    for value in values:
        text = str(value).strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(text)
        if max_items is not None and len(result) >= max_items:
            break
    return result


def parse_fraction(token: str) -> Optional[float]:
    cleaned = token.strip().replace("-", " ")
    if not cleaned:
        return None
    try:
        if " " in cleaned:
            return sum(float(Fraction(part)) for part in cleaned.split())
        return float(Fraction(cleaned))
    except Exception:
        return None


def cleanup_name(text: str) -> str:
    cleaned = re.sub(r"\([^)]*\)", "", text)
    cleaned = re.split(r"\s+or\s+", cleaned, maxsplit=1)[0]
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,.;:-")
    cleaned = re.sub(r"^(firmly packed|packed|soft)\s+", "", cleaned, flags=re.IGNORECASE)
    for pattern in PREP_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,.;:-")
    return cleaned


def parse_ingredient_item(raw_text: str) -> Tuple[Dict[str, Any], List[str]]:
    warnings: List[str] = []
    original = str(raw_text).strip()
    if not original:
        return {"name": "", "quantity": None, "unit": None, "required": True}, ["empty ingredient"]

    quantity: Optional[float] = None
    unit: Optional[str] = None
    text = original
    match = re.match(r"^\s*(\d+\s+\d+/\d+|\d+/\d+|\d+(?:\.\d+)?)\b", text)
    if match:
        quantity = parse_fraction(match.group(1))
        text = text[match.end():].lstrip()

    if text.startswith("("):
        depth = 0
        consumed = 0
        for index, char in enumerate(text):
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    consumed = index + 1
                    break
        if consumed:
            text = text[consumed:].lstrip(" ,")

    tokens = text.split()
    if tokens:
        token = tokens[0].lower().strip(",.;:")
        if token in UNITS:
            unit = tokens[0].strip(",")
            text = " ".join(tokens[1:])
        elif token.endswith(".") and token[:-1] in UNITS:
            unit = tokens[0]
            text = " ".join(tokens[1:])

    name = cleanup_name(text)
    if quantity is None and not name:
        name = cleanup_name(original)
    if not name:
        warnings.append("ingredient name could not be extracted")
    elif name.lower() == original.lower():
        pass
    elif not name:
        warnings.append("ingredient cleanup produced empty name")

    return {
        "name": name,
        "quantity": quantity,
        "unit": unit,
        "required": True,
    }, warnings


def extract_servings(directions: Sequence[str]) -> int:
    text = " ".join(str(item) for item in directions)
    patterns = [
        r"\bserves?\s+(\d+)\b",
        r"\byields?\s+(\d+)\b",
        r"\bmakes?\s+(\d+)\b",
        r"\b(\d+)\s+servings?\b",
    ]
    lowered = text.lower()
    for pattern in patterns:
        match = re.search(pattern, lowered)
        if match:
            return int(match.group(1))
    return DEFAULT_SERVINGS


def build_summary(primary_ingredients: Sequence[str]) -> str:
    ingredients = [item for item in primary_ingredients if item][:2]
    if len(ingredients) >= 2:
        return f"{ingredients[0]}, {ingredients[1]} recipe from raw dataset."
    if len(ingredients) == 1:
        return f"{ingredients[0]} recipe from raw dataset."
    return "Recipe from raw dataset."


def infer_tool(direction: str) -> str:
    lowered = direction.lower()
    for keyword, tool in TOOL_KEYWORDS:
        if keyword in lowered:
            return tool
    return "general"


def extract_minutes(direction: str) -> int:
    lowered = direction.lower()
    hour_match = re.search(r"(\d+)\s*(?:to|-)\s*(\d+)\s*hours?", lowered)
    if hour_match:
        return int(hour_match.group(1)) * 60
    minute_match = re.search(r"(\d+)\s*(?:to|-)\s*(\d+)\s*minutes?", lowered)
    if minute_match:
        return int(minute_match.group(1))
    single_hour_match = re.search(r"(\d+)\s*hours?", lowered)
    if single_hour_match:
        return int(single_hour_match.group(1)) * 60
    single_minute_match = re.search(r"(\d+)\s*minutes?", lowered)
    if single_minute_match:
        return int(single_minute_match.group(1))
    return DEFAULT_STEP_MINUTES


def extract_step_title(direction: str, step_number: int) -> str:
    words = re.findall(r"[A-Za-z']+", direction)
    for word in words[:5]:
        lowered = word.lower()
        if lowered in COOKING_VERBS:
            return lowered.capitalize()
    if words:
        return words[0].capitalize()
    return f"Step {step_number}"


def match_step_ingredients(direction: str, candidates: Sequence[str], fallback: Sequence[str]) -> List[str]:
    lowered = direction.lower()
    matched: List[str] = []
    for candidate in candidates:
        text = str(candidate).strip()
        if not text:
            continue
        words = [part for part in re.findall(r"[a-z0-9]+", text.lower()) if part]
        if words and all(word in lowered for word in words):
            matched.append(text)
    matched = dedupe_preserve(matched, max_items=3)
    if matched:
        return matched
    return dedupe_preserve(fallback, max_items=2)


def load_first_rows(path: Path, limit: int) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(
                {
                    "row_id": row.get("", ""),
                    "title": row.get("title", ""),
                    "ingredients": row.get("ingredients", ""),
                    "directions": row.get("directions", ""),
                    "link": row.get("link", ""),
                    "source": row.get("source", ""),
                    "NER": row.get("NER", ""),
                }
            )
            if len(rows) >= limit:
                break
    return rows


def build_recipe_record(row: Dict[str, str], workflow_path: Path) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, str]], Optional[List[Dict[str, Any]]]]:
    review_entries: List[Dict[str, str]] = []
    title = row["title"].strip()
    if not title:
        review_entries.append(make_review_entry(row, "missing title"))
        return None, review_entries, None

    ingredient_values, ingredient_error = safe_parse_list(row["ingredients"])
    if ingredient_error:
        review_entries.append(make_review_entry(row, ingredient_error))
        return None, review_entries, None

    direction_values, direction_error = safe_parse_list(row["directions"])
    if direction_error:
        review_entries.append(make_review_entry(row, direction_error))
        return None, review_entries, None
    if not direction_values:
        review_entries.append(make_review_entry(row, "directions are empty"))
        return None, review_entries, None

    ner_values, _ = safe_parse_list(row["NER"])

    required_ingredients: List[Dict[str, Any]] = []
    parsed_ingredient_names: List[str] = []
    for item in ingredient_values:
        parsed_item, warnings = parse_ingredient_item(str(item))
        if parsed_item["name"]:
            required_ingredients.append(parsed_item)
            parsed_ingredient_names.append(parsed_item["name"])
        else:
            review_entries.append(make_review_entry(row, "; ".join(warnings or ["ingredient name could not be extracted"])))

    if not required_ingredients:
        review_entries.append(make_review_entry(row, "no required ingredients extracted"))
        return None, review_entries, None

    primary_ingredients = dedupe_preserve(
        [str(item).strip() for item in ner_values if str(item).strip()] + parsed_ingredient_names,
        max_items=DISPLAY_INGREDIENT_LIMIT,
    )
    if not primary_ingredients:
        review_entries.append(make_review_entry(row, "no primary ingredients extracted"))
        return None, review_entries, None

    search_keywords = dedupe_preserve(
        [str(item).strip() for item in ner_values if str(item).strip()] + parsed_ingredient_names,
        max_items=SEARCH_KEYWORD_LIMIT,
    )
    if not search_keywords:
        review_entries.append(make_review_entry(row, "search keywords are empty"))
        return None, review_entries, None

    recipe_id = f"raw_{row['row_id']}_{slugify(title)}"
    workflow_steps = build_workflow_steps(recipe_id, direction_values, search_keywords, primary_ingredients)
    if not workflow_steps:
        review_entries.append(make_review_entry(row, "workflow step generation failed"))
        return None, review_entries, None

    record = {
        "id": recipe_id,
        "title": title,
        "cuisine": "Unknown",
        "summary": build_summary(primary_ingredients),
        "servings": extract_servings(direction_values),
        "primary_ingredients": primary_ingredients,
        "required_ingredients": required_ingredients,
        "optional_ingredients": [],
        "search_keywords": search_keywords,
        "workflow_file": workflow_path.as_posix(),
    }
    return record, review_entries, workflow_steps


def build_workflow_steps(
    recipe_id: str,
    directions: Sequence[str],
    search_keywords: Sequence[str],
    primary_ingredients: Sequence[str],
) -> List[Dict[str, Any]]:
    steps: List[Dict[str, Any]] = []
    for index, direction in enumerate(directions, start=1):
        description = " ".join(str(direction).split()).strip()
        if not description:
            continue
        steps.append(
            {
                "recipe_id": recipe_id,
                "step_number": index,
                "title": extract_step_title(description, index),
                "description": description,
                "ingredients": match_step_ingredients(description, search_keywords, primary_ingredients),
                "tool": infer_tool(description),
                "estimated_minutes": extract_minutes(description),
            }
        )
    return steps


def make_review_entry(row: Dict[str, str], reason: str) -> Dict[str, str]:
    return {
        "row_id": row["row_id"],
        "title": row["title"].strip(),
        "reason": reason,
        "raw_title": row["title"],
        "raw_ingredients": row["ingredients"],
        "raw_directions": row["directions"],
    }


def write_jsonl(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")


def main() -> None:
    args = parse_args()
    project_root = Path(__file__).resolve().parents[1]
    input_path = (project_root / args.input).resolve()
    output_dir = (project_root / args.output_dir).resolve()
    workflow_dir = output_dir / "workflows"

    rows = load_first_rows(input_path, args.limit)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    workflow_dir.mkdir(parents=True, exist_ok=True)

    accepted: List[Dict[str, Any]] = []
    review_entries: List[Dict[str, str]] = []
    parse_counts = {
        "ingredient_list_success": 0,
        "ingredient_list_failure": 0,
        "direction_list_success": 0,
        "direction_list_failure": 0,
        "ner_list_success": 0,
        "ner_list_failure": 0,
    }
    seen_ids = set()

    for row in rows:
        ingredients, ingredient_error = safe_parse_list(row["ingredients"])
        directions, direction_error = safe_parse_list(row["directions"])
        ner_values, ner_error = safe_parse_list(row["NER"])
        parse_counts["ingredient_list_success" if not ingredient_error else "ingredient_list_failure"] += 1
        parse_counts["direction_list_success" if not direction_error else "direction_list_failure"] += 1
        parse_counts["ner_list_success" if not ner_error else "ner_list_failure"] += 1

        workflow_rel_path = args.output_dir / "workflows" / f"raw_{row['row_id']}_{slugify(row['title'])}.jsonl"
        workflow_path = project_root / workflow_rel_path
        record, row_reviews, workflow_steps = build_recipe_record(row, workflow_path)

        if record is None or workflow_steps is None:
            review_entries.extend(row_reviews)
            continue
        if record["id"] in seen_ids:
            review_entries.append(make_review_entry(row, "duplicate recipe id"))
            continue

        seen_ids.add(record["id"])
        accepted.append(record)
        review_entries.extend(row_reviews)
        write_jsonl(workflow_path, workflow_steps)

    for record in accepted:
        record["workflow_file"] = Path(record["workflow_file"]).relative_to(project_root).as_posix()

    accepted.sort(key=lambda item: int(item["id"].split("_", 2)[1]))
    review_entries.sort(key=lambda item: (int(item["row_id"] or 0), item["reason"]))

    write_jsonl(output_dir / "recipes.jsonl", accepted)
    write_jsonl(output_dir / "review.jsonl", review_entries)
    write_jsonl(
        output_dir / "report.jsonl",
        [
            {
                "input_rows": len(rows),
                "accepted_recipes": len(accepted),
                "review_entries": len(review_entries),
                **parse_counts,
            }
        ],
    )

    print(f"Input rows: {len(rows)}")
    print(f"Accepted recipes: {len(accepted)}")
    print(f"Review entries: {len(review_entries)}")
    print("Parse counts:")
    for key, value in parse_counts.items():
        print(f"  - {key}: {value}")


if __name__ == "__main__":
    main()
