from datetime import datetime
from pathlib import Path
import shutil

from src.utils.path_utils import CONFIG_DIR, ensure_dir


class BackupService:
    def __init__(self, catalog_path):
        self.catalog_path = Path(catalog_path)
        self.backup_dir = ensure_dir(CONFIG_DIR / "backups")

    def create_backup(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target = self.backup_dir / f"catalogo_{timestamp}.json"
        shutil.copy2(self.catalog_path, target)
        return target

    def restore_backup(self, backup_path):
        backup_path = Path(backup_path)
        shutil.copy2(backup_path, self.catalog_path)
        return self.catalog_path
