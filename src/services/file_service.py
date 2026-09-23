import json
import os
import shutil
from datetime import datetime
from pathlib import Path

from src.models.catalog_models import ALL_FILES_LABEL, normalize_category
from src.services.catalog_lookup import context_name, resolve_cart_item_context
from src.utils.file_name_utils import accepted_files, find_item_file
from src.utils.path_utils import ensure_dir
from src.utils.text_utils import safe_filename


class FileService:
    def make_order_folder(self, output_folder, order_info):
        date_text = datetime.now().strftime("%Y%m%d")
        number = safe_filename(order_info.get("numero_pedido", ""), "sem_numero")
        client = safe_filename(order_info.get("cliente", ""), "cliente")
        base = Path(output_folder) / f"PEDIDO_{number}_{client}_{date_text}"
        candidate = base
        index = 2
        while candidate.exists():
            candidate = Path(f"{base}_{index}")
            index += 1
        candidate.mkdir(parents=True, exist_ok=False)
        return candidate

    def copy_file(self, source, target_dir, quantity, copy_mode, name_prefix=""):
        source = Path(source)
        target_dir = ensure_dir(target_dir)
        copied = []
        prefix = f"{name_prefix}_" if name_prefix else ""
        if copy_mode == "prefix_quantity":
            target = self.unique_target(target_dir / f"{quantity}x {prefix}{source.name}")
            shutil.copy2(source, target)
            copied.append(str(target))
            return copied

        for index in range(1, int(quantity) + 1):
            target = self.unique_target(target_dir / f"{prefix}{source.stem}_{index:03d}{source.suffix}")
            shutil.copy2(source, target)
            copied.append(str(target))
        return copied

    def unique_target(self, target):
        target = Path(target)
        if not target.exists():
            return target
        index = 2
        while True:
            candidate = target.with_name(f"{target.stem}_{index}{target.suffix}")
            if not candidate.exists():
                return candidate
            index += 1

    def generate(self, output_folder, order_info, catalog_or_team, model, cart_items, settings, validation_result=None):
        order_folder = self.make_order_folder(output_folder, order_info)
        copy_mode = settings.get("copy_mode", "duplicate_files")
        copied = []
        missing = []
        catalog = catalog_or_team if catalog_or_team and catalog_or_team.get("teams") else None
        fallback_team = None if catalog else catalog_or_team
        fallback_model = model

        for item in cart_items:
            context = self.resolve_context(catalog_or_team, item, fallback_team, fallback_model)
            if not context:
                missing.append(f"Configuração não encontrada: {item.source_label} / {item.category_name} - {item.item_label}")
                continue

            category = context["category"]
            target_dir = order_folder
            name_prefix = self.output_prefix(context)
            copy_all_files = category.get("type") == "all_files_from_folder" or (
                category.get("quick_action_all_files") and item.item_label == ALL_FILES_LABEL
            )
            if copy_all_files:
                files = accepted_files(category.get("folder_path", ""), category.get("extensions"))
                if not files:
                    missing.append(f"Nenhum arquivo em {context_name(context)}")
                    continue
                for file_path in files:
                    copied.extend(self.copy_file(file_path, target_dir, item.quantity, copy_mode, name_prefix))
            else:
                file_path = find_item_file(category, item.item_label)
                if not file_path:
                    missing.append(f"Arquivo não encontrado: {context_name(context)} - {item.item_label}")
                    continue
                copied.extend(self.copy_file(file_path, target_dir, item.quantity, copy_mode, name_prefix))

        conference_dir = ensure_dir(order_folder / "99_CONFERENCIA")
        self.write_summary(conference_dir / "resumo_do_pedido.txt", order_info, catalog_or_team, model, cart_items, copied, missing)
        with (conference_dir / "carrinho.json").open("w", encoding="utf-8") as file:
            json.dump(
                {
                    "order": order_info,
                    "items": [item.to_dict() for item in cart_items],
                    "flat_output": True,
                    "generated_at": datetime.now().isoformat(timespec="seconds"),
                },
                file,
                ensure_ascii=False,
                indent=2,
            )
            file.write("\n")
        with (conference_dir / "arquivos_faltando.txt").open("w", encoding="utf-8") as file:
            if missing:
                file.write("\n".join(missing))
                file.write("\n")
            else:
                file.write("Nenhum arquivo faltando.\n")

        if settings.get("open_folder_after_generate"):
            try:
                os.startfile(order_folder)
            except OSError:
                pass
        return order_folder, copied, missing

    def resolve_context(self, catalog_or_team, item, fallback_team, fallback_model):
        if catalog_or_team and catalog_or_team.get("teams"):
            return resolve_cart_item_context(catalog_or_team, item, fallback_team, fallback_model)

        if fallback_team and fallback_model:
            for category in fallback_model.get("categories", []):
                if category.get("id") == item.category_id:
                    return {
                        "team": fallback_team,
                        "model": fallback_model,
                        "category": normalize_category(category),
                    }
        return None

    def output_prefix(self, context):
        parts = [
            context["team"].get("name", ""),
            context["model"].get("name", ""),
            context["category"].get("name", ""),
        ]
        safe_parts = [safe_filename(part, "")[:32] for part in parts if part]
        return "_".join(part for part in safe_parts if part)

    def write_summary(self, path, order_info, team_or_catalog, model, cart_items, copied, missing):
        lines = [
            "RESUMO DO PEDIDO",
            "",
            f"Cliente: {order_info.get('cliente', '')}",
            f"Pedido: {order_info.get('numero_pedido', '')}",
            f"Observação: {order_info.get('observacao', '')}",
            f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            "",
            "ITENS",
        ]
        for item in cart_items:
            lines.append(
                f"- {item.source_label} | {item.category_name}: {item.item_label} | quantidade {item.quantity}"
            )
        lines.extend(
            [
                "",
                f"Total de itens diferentes: {len(cart_items)}",
                f"Total de quantidades: {sum(item.quantity for item in cart_items)}",
                f"Arquivos copiados: {len(copied)}",
                "",
                "ARQUIVOS FALTANDO",
            ]
        )
        if missing:
            lines.extend(f"- {message}" for message in missing)
        else:
            lines.append("Nenhum arquivo faltando.")
        Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
