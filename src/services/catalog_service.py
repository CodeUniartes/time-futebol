from copy import deepcopy

from src.models.catalog_models import (
    BLANK_CATALOG,
    SCHEMA_VERSION,
    categories_for_features,
    default_features,
    normalize_category,
)
from src.utils.json_utils import load_json, save_json
from src.utils.path_utils import CONFIG_DIR
from src.utils.text_utils import slugify


class CatalogService:
    def __init__(self, catalog_path=None):
        self.catalog_path = catalog_path or CONFIG_DIR / "catalogo.json"
        self.ensure_catalog_exists()

    def ensure_catalog_exists(self):
        if not self.catalog_path.exists():
            save_json(self.catalog_path, deepcopy(BLANK_CATALOG))

    def load_catalog(self):
        data = load_json(self.catalog_path, deepcopy(BLANK_CATALOG))
        if not isinstance(data, dict):
            data = deepcopy(BLANK_CATALOG)
        data.setdefault("schema_version", 1)
        self.migrate(data)
        data.setdefault("configured", False)
        data.setdefault("settings", deepcopy(BLANK_CATALOG["settings"]))
        data.setdefault("teams", [])
        for team in data.get("teams", []):
            for model in team.get("models", []):
                model["categories"] = [
                    normalize_category(category) for category in model.get("categories", [])
                ]
        return data

    def migrate(self, data):
        # Em memória: o arquivo só muda na próxima gravação.
        version = data["schema_version"]
        if isinstance(version, int) and version >= SCHEMA_VERSION:
            return
        for team in data.get("teams", []):
            for model in team.get("models", []):
                model.setdefault("active", True)
        data["schema_version"] = SCHEMA_VERSION

    def save_catalog(self, catalog):
        save_json(self.catalog_path, catalog)

    def is_configured(self):
        catalog = self.load_catalog()
        if not catalog.get("configured"):
            return False
        for team in catalog.get("teams", []):
            for model in team.get("models", []):
                if model.get("categories"):
                    return True
        return False

    def get_teams(self):
        return self.load_catalog().get("teams", [])

    def get_team(self, team_id):
        for team in self.get_teams():
            if team.get("id") == team_id:
                return team
        return None

    def get_model(self, team_id, model_id):
        team = self.get_team(team_id)
        if not team:
            return None
        for model in team.get("models", []):
            if model.get("id") == model_id:
                return model
        return None

    def unique_id(self, base_name, existing_ids):
        base = slugify(base_name)
        candidate = base
        index = 2
        while candidate in existing_ids:
            candidate = f"{base}_{index}"
            index += 1
        return candidate

    def create_initial_catalog(self, team_name, model_name, description, features, folder_paths, output_folder):
        team_id = self.unique_id(team_name, set())
        model_id = self.unique_id(model_name, set())
        catalog = deepcopy(BLANK_CATALOG)
        catalog["configured"] = True
        catalog["settings"]["default_output_folder"] = output_folder or ""
        catalog["teams"] = [
            {
                "id": team_id,
                "name": team_name.strip(),
                "models": [
                    {
                        "id": model_id,
                        "name": model_name.strip(),
                        "description": description.strip(),
                        "features": {**default_features(), **features},
                        "categories": categories_for_features(features, folder_paths),
                    }
                ],
            }
        ]
        self.save_catalog(catalog)
        return catalog

    def add_team(self, name):
        catalog = self.load_catalog()
        existing_ids = {team.get("id") for team in catalog.get("teams", [])}
        team = {"id": self.unique_id(name, existing_ids), "name": name.strip(), "models": []}
        catalog.setdefault("teams", []).append(team)
        catalog["configured"] = any(team.get("models") for team in catalog["teams"])
        self.save_catalog(catalog)
        return team

    def add_model(self, team_id, name, description="", features=None, folder_paths=None):
        catalog = self.load_catalog()
        for team in catalog.get("teams", []):
            if team.get("id") == team_id:
                existing_ids = {model.get("id") for model in team.get("models", [])}
                features = {**default_features(), **(features or {})}
                model = {
                    "id": self.unique_id(name, existing_ids),
                    "name": name.strip(),
                    "description": description.strip(),
                    "features": features,
                    "categories": categories_for_features(features, folder_paths or {}),
                }
                team.setdefault("models", []).append(model)
                catalog["configured"] = True
                self.save_catalog(catalog)
                return model
        return None

    def update_model(self, team_id, model_id, name, description, features, folder_paths):
        catalog = self.load_catalog()
        for team in catalog.get("teams", []):
            if team.get("id") != team_id:
                continue
            for model in team.get("models", []):
                if model.get("id") == model_id:
                    model["name"] = name.strip()
                    model["description"] = description.strip()
                    model["features"] = {**default_features(), **features}
                    model["categories"] = categories_for_features(model["features"], folder_paths)
                    catalog["configured"] = True
                    self.save_catalog(catalog)
                    return model
        return None

    def update_settings(self, settings):
        catalog = self.load_catalog()
        catalog.setdefault("settings", {}).update(settings)
        self.save_catalog(catalog)
        return catalog["settings"]
