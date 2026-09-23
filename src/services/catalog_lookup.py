from src.models.catalog_models import normalize_category


def resolve_cart_item_context(catalog, item, fallback_team=None, fallback_model=None):
    if catalog and catalog.get("teams"):
        exact = find_in_catalog(catalog, item)
        if exact:
            return exact

    if fallback_team and fallback_model:
        for category in fallback_model.get("categories", []):
            if category.get("id") == item.category_id:
                return {
                    "team": fallback_team,
                    "model": fallback_model,
                    "category": normalize_category(category),
                }

    return None


def find_in_catalog(catalog, item):
    for team in catalog.get("teams", []):
        if item.team_id and team.get("id") != item.team_id:
            continue
        for model in team.get("models", []):
            if item.model_id and model.get("id") != item.model_id:
                continue
            for category in model.get("categories", []):
                if category.get("id") == item.category_id:
                    return {
                        "team": team,
                        "model": model,
                        "category": normalize_category(category),
                    }
    return None


def context_name(context):
    team = context["team"].get("name", "")
    model = context["model"].get("name", "")
    category = context["category"].get("name", "")
    return " / ".join(part for part in [team, model, category] if part)
