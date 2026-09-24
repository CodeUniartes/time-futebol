import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from src.models.catalog_models import ALL_FILES_LABEL
from src.utils.file_name_utils import accepted_files, build_item_index, natural_key
from src.utils.json_utils import load_json, save_json
from src.utils.preview_image import contact_sheet, make_preview, save_webp
from src.utils.text_utils import slugify
from src.utils.tiff_reader import TiffReadError, read_tiff

GENERATOR_VERSION = 1
PUBLIC_SCHEMA_VERSION = 1
FILM_WIDTH_CM = 58.0
FILM_TOLERANCE_CM = 0.2
CATALOG_FILE = "catalog.public.json"
CACHE_FILE = ".cache.json"
REPORT_FILE = "relatorio.txt"
PREVIEWS_DIR = "previews"
ALL_FILES_FALLBACK_SLUG = "todos_os_arquivos"


@dataclass
class PublishResult:
    output_dir: Path
    generated: int = 0
    reused: int = 0
    item_count: int = 0
    failures: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    cancelled: bool = False


class _Cancelled(Exception):
    pass


class PublishService:
    def __init__(self, catalog_service, site_config):
        self.catalog_service = catalog_service
        self.site_config = site_config

    def publish(self, progress=None, cancel=None):
        output_dir = self.site_config.publish_dir()
        result = PublishResult(output_dir=output_dir)
        catalog = self._catalog_with_version()
        plan = self._plan(catalog)
        run = _Run(
            service=self,
            output_dir=output_dir,
            result=result,
            progress=progress,
            cancel=cancel,
            total=sum(category.file_count for category in plan.categories),
            fingerprint=self._fingerprint(),
        )
        try:
            public = run.build(catalog, plan)
        except _Cancelled:
            result.cancelled = True
            return result
        save_json(output_dir / CATALOG_FILE, public)
        run.finish()
        return result

    def _catalog_with_version(self):
        catalog = self.catalog_service.load_catalog()
        if not catalog.get("updated_at"):
            self.catalog_service.save_catalog(catalog)
            catalog = self.catalog_service.load_catalog()
        return catalog

    def _fingerprint(self):
        watermark = self.site_config.watermark()
        raw = f"{GENERATOR_VERSION}|{self.site_config.preview_max_side()}|{watermark}"
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]

    def _plan(self, catalog):
        plan = _Plan()
        for team in catalog.get("teams", []):
            for model in team.get("models", []):
                if not model.get("active", True):
                    continue
                for category in model.get("categories", []):
                    entry = _category_plan(team, model, category)
                    if entry:
                        plan.categories.append(entry)
        return plan


@dataclass
class _CategoryPlan:
    team: dict
    model: dict
    category: dict
    labeled: list  # [(label, path)] itens individuais, já em ordem natural
    all_files: list  # [path] arquivos para o item "Todos os arquivos" (vazio se não houver)

    @property
    def file_count(self):
        return len(self.labeled) + len(self.all_files)


@dataclass
class _Plan:
    categories: list = field(default_factory=list)


def _category_plan(team, model, category):
    if not category.get("enabled", True):
        return None
    folder = category.get("folder_path") or ""
    if not folder or not Path(folder).is_dir():
        return None
    all_files_type = category.get("type") == "all_files_from_folder"
    labeled = []
    if not all_files_type:
        index = build_item_index(category)
        ordered = sorted(index.values(), key=lambda entry: natural_key(entry["label"]))
        labeled = [(entry["label"], entry["path"]) for entry in ordered]
    all_files = []
    if all_files_type or category.get("quick_action_all_files"):
        all_files = accepted_files(folder, category.get("extensions"))
    if not labeled and not all_files:
        return None
    return _CategoryPlan(team=team, model=model, category=category, labeled=labeled, all_files=all_files)


class _Run:
    def __init__(self, service, output_dir, result, progress, cancel, total, fingerprint):
        self.service = service
        self.output_dir = Path(output_dir)
        self.result = result
        self.progress = progress
        self.cancel = cancel
        self.total = total
        self.fingerprint = fingerprint
        self.done = 0
        self.max_side = service.site_config.preview_max_side()
        self.watermark = service.site_config.watermark()
        self.old_cache = load_json(self.output_dir / CACHE_FILE, {}) if (self.output_dir / CACHE_FILE).exists() else {}
        if not isinstance(self.old_cache, dict):
            self.old_cache = {}
        self.new_cache = {}
        self.keep_previews = set()

    # ---- construção do catálogo público ----

    def build(self, catalog, plan):
        teams_out = {}
        for entry in plan.categories:
            items = self._items_for(entry)
            if not items:
                continue
            team_out = teams_out.setdefault(
                entry.team["id"], {"id": entry.team["id"], "name": entry.team.get("name", entry.team["id"]), "models": []}
            )
            model_out = next((m for m in team_out["models"] if m["id"] == entry.model["id"]), None)
            if model_out is None:
                model_out = _public_model(entry.model)
                team_out["models"].append(model_out)
            model_out["categories"].append(_public_category(entry, items))
            self.result.item_count += len(items)
        return {
            "schema_version": PUBLIC_SCHEMA_VERSION,
            "catalog_version": catalog["updated_at"],
            "teams": list(teams_out.values()),
        }

    def _items_for(self, entry):
        base = Path("previews") / entry.team["id"] / entry.model["id"] / entry.category["id"]
        used_names = set()
        items = []
        for label, path in entry.labeled:
            item = self._individual_item(base, label, path, used_names)
            if item:
                items.append(item)
        if entry.all_files:
            item = self._all_files_item(base, entry.all_files, used_names)
            if item:
                items.append(item)
        return items

    def _individual_item(self, base, label, path, used_names):
        self._check_cancel()
        relative = self._unique_relative(base, slugify(label, "item"), used_names)
        cached = self._cached_file(path, relative)
        if cached:
            measures = cached
            self.result.reused += 1
        else:
            try:
                measures = self._render_file(path, relative)
            except (TiffReadError, _PreviewSkipped) as error:
                self._fail(path, error)
                self._tick(path)
                return None
            self.result.generated += 1
        self._tick(path)
        self._check_size(label, path, measures)
        return {"label": label, "preview": relative, "width_cm": measures["width_cm"], "height_cm": measures["height_cm"]}

    def _all_files_item(self, base, files, used_names):
        relative = self._unique_relative(base, ALL_FILES_FALLBACK_SLUG, used_names)
        combined = "|".join(f"{path}:{self._file_key(path)}" for path in files)
        cache_key = hashlib.sha1(combined.encode("utf-8")).hexdigest()
        previous = self.old_cache.get(relative)
        target = self.output_dir / relative

        if previous and previous.get("key") == cache_key and previous.get("pieces") and target.exists():
            for path, piece in zip(files, previous["pieces"]):
                self._check_cancel()
                self._check_size(Path(path).stem, path, piece)
                self._tick(path)
            self.new_cache[relative] = previous
            self.keep_previews.add(relative)
            self.result.reused += 1
            return {"label": ALL_FILES_LABEL, "preview": relative, "pieces": previous["pieces"]}

        pieces, images, failed = [], [], False
        for path in files:
            self._check_cancel()
            try:
                image, measures, _key = self._measure_file(path)
            except (TiffReadError, _PreviewSkipped) as error:
                self._fail(path, error)
                failed = True
                self._tick(path)
                continue
            self._check_size(Path(path).stem, path, measures)
            pieces.append({"width_cm": measures["width_cm"], "height_cm": measures["height_cm"]})
            images.append(image)
            self._tick(path)
        if not pieces:
            return None
        save_webp(contact_sheet(images, self.max_side), target)
        self.result.generated += 1
        if not failed:
            self.new_cache[relative] = {"key": cache_key, "pieces": pieces}
        self.keep_previews.add(relative)
        return {"label": ALL_FILES_LABEL, "preview": relative, "pieces": pieces}

    # ---- arquivos individuais ----

    def _file_key(self, path):
        stat = Path(path).stat()
        return f"{stat.st_size}:{stat.st_mtime_ns}:{self.fingerprint}"

    def _cached_file(self, path, relative):
        entry = self.old_cache.get(relative)
        if not entry or entry.get("key") != self._file_key(path) or entry.get("source") != str(path):
            return None
        if not (self.output_dir / relative).exists():
            return None
        self.new_cache[relative] = entry
        self.keep_previews.add(relative)
        if entry.get("dpi_assumed"):
            self.result.warnings.append(f"{Path(path).name}: sem dpi gravado, assumido {300} dpi.")
        return entry

    def _render_file(self, path, relative):
        image, measures, key = self._measure_file(path)
        save_webp(image, self.output_dir / relative)
        entry = {"key": key, "source": str(path), **measures}
        self.new_cache[relative] = entry
        self.keep_previews.add(relative)
        return entry

    def _measure_file(self, path):
        tiff = read_tiff(path)
        try:
            preview = make_preview(tiff.rgba, tiff.dpi, max_side=self.max_side, watermark=self.watermark)
        except Exception as error:
            raise _PreviewSkipped(str(error)) from error
        measures = {
            "width_cm": preview.width_cm,
            "height_cm": preview.height_cm,
            "dpi_assumed": preview.dpi_assumed,
        }
        if preview.dpi_assumed:
            self.result.warnings.append(f"{Path(path).name}: sem dpi gravado, assumido 300 dpi.")
        return preview.image, measures, self._file_key(path)

    # ---- utilitários ----

    def _unique_relative(self, base, slug, used_names):
        name, counter = slug, 2
        while name in used_names:
            name = f"{slug}_{counter}"
            counter += 1
        used_names.add(name)
        return (base / f"{name}.webp").as_posix()

    def _check_size(self, label, path, measures):
        # A película tem 58 cm de largura e a peça pode girar 90 graus: só não cabe se o lado menor passar de 58 cm.
        width, height = measures["width_cm"], measures["height_cm"]
        if min(width, height) > FILM_WIDTH_CM + FILM_TOLERANCE_CM:
            self.result.warnings.append(
                f"{label} ({Path(path).name}): {width} x {height} cm não cabe na película de 58 cm."
            )

    def _fail(self, path, error):
        self.result.failures.append(f"{path}: {error}")

    def _tick(self, path):
        self.done += 1
        if self.progress:
            self.progress(self.done, self.total, Path(path).name)

    def _check_cancel(self):
        if self.cancel and self.cancel():
            raise _Cancelled()

    # ---- fechamento ----

    def finish(self):
        previews_root = self.output_dir / PREVIEWS_DIR
        if previews_root.exists():
            for file in previews_root.rglob("*.webp"):
                if file.relative_to(self.output_dir).as_posix() not in self.keep_previews:
                    file.unlink()
            for folder in sorted((p for p in previews_root.rglob("*") if p.is_dir()), reverse=True):
                if not any(folder.iterdir()):
                    folder.rmdir()
        save_json(self.output_dir / CACHE_FILE, self.new_cache)
        (self.output_dir / REPORT_FILE).write_text(self._report(), encoding="utf-8")

    def _report(self):
        lines = [
            f"Itens publicados: {self.result.item_count}",
            f"Prévias geradas: {self.result.generated} | reaproveitadas: {self.result.reused}",
        ]
        if self.result.failures:
            lines += ["", f"Falhas ({len(self.result.failures)}):"] + [f"- {failure}" for failure in self.result.failures]
        if self.result.warnings:
            lines += ["", f"Avisos ({len(self.result.warnings)}):"] + [f"- {warning}" for warning in self.result.warnings]
        return "\n".join(lines) + "\n"


class _PreviewSkipped(Exception):
    pass


def _public_model(model):
    public = {"id": model["id"], "name": model.get("name", model["id"])}
    if isinstance(model.get("season"), int) and not isinstance(model.get("season"), bool):
        public["season"] = model["season"]
    if model.get("description"):
        public["description"] = model["description"]
    public["categories"] = []
    return public


def _public_category(entry, items):
    category = entry.category
    return {
        "id": category["id"],
        "name": category.get("name", category["id"]),
        "type": category.get("type", ""),
        "allow_group_add": bool(category.get("allow_group_add")),
        "all_files_option": bool(entry.all_files),
        "items": items,
    }
