from dataclasses import dataclass, field

from src.models.catalog_models import ALL_FILES_LABEL, normalize_category
from src.services.catalog_lookup import context_name, resolve_cart_item_context
from src.utils.file_name_utils import accepted_files, find_item_file


@dataclass
class ValidationResult:
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    found_files: dict = field(default_factory=dict)
    missing_items: list = field(default_factory=list)

    @property
    def ok(self):
        return not self.errors


class ValidationService:
    def validate_folder(self, category):
        folder = category.get("folder_path", "")
        files = accepted_files(folder, category.get("extensions"))
        if not folder:
            return False, "Pasta não selecionada.", 0
        if not files:
            return False, "Nenhum arquivo .tif/.tiff encontrado.", 0
        return True, "Pasta OK.", len(files)

    def validate_order(self, output_folder, catalog_or_model, cart_items, fallback_team=None, fallback_model=None):
        result = ValidationResult()
        if not output_folder:
            result.errors.append("Escolha uma pasta de saída.")
        if not catalog_or_model:
            result.errors.append("Selecione uma camisa/modelo.")
            return result
        if not cart_items:
            result.errors.append("Adicione pelo menos um item ao carrinho.")

        unique_contexts = self.collect_contexts(catalog_or_model, cart_items, fallback_team, fallback_model, result)
        if not unique_contexts and cart_items:
            result.errors.append("Nenhuma categoria ativa encontrada para os itens do carrinho.")

        for key, context in unique_contexts.items():
            category = context["category"]
            ok, message, count = self.validate_folder(category)
            label = context_name(context)
            if not ok:
                result.errors.append(f"{label}: {message}")
            else:
                result.found_files["|".join(key)] = count

        for item in cart_items:
            context = resolve_cart_item_context(catalog_or_model, item, fallback_team, fallback_model)
            if not context:
                result.errors.append(
                    f"Categoria removida da configuração: {item.source_label} / {item.category_name}."
                )
                continue

            category = context["category"]
            if item.item_label == ALL_FILES_LABEL and category.get("quick_action_all_files"):
                continue
            if category.get("type") == "individual_from_folder":
                file_path = find_item_file(category, item.item_label)
                if not file_path:
                    result.errors.append(f"Arquivo não encontrado: {context_name(context)} - {item.item_label}.")
                    result.missing_items.append(item.to_dict())

        return result

    def collect_contexts(self, catalog_or_model, cart_items, fallback_team, fallback_model, result):
        if catalog_or_model.get("teams"):
            unique_contexts = {}
            for item in cart_items:
                context = resolve_cart_item_context(catalog_or_model, item, fallback_team, fallback_model)
                if not context:
                    result.errors.append(
                        f"Configuração não encontrada: {item.source_label} / {item.category_name} - {item.item_label}."
                    )
                    continue
                category = context["category"]
                key = (
                    context["team"].get("id", ""),
                    context["model"].get("id", ""),
                    category.get("id", ""),
                )
                unique_contexts[key] = context
            return unique_contexts

        categories = {
            category["id"]: normalize_category(category)
            for category in catalog_or_model.get("categories", [])
            if category.get("enabled")
        }
        return {
            ("", "", category_id): {
                "team": fallback_team or {},
                "model": fallback_model or catalog_or_model,
                "category": category,
            }
            for category_id, category in categories.items()
        }
