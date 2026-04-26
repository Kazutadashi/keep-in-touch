"""Simple backup helpers."""

import shutil
from datetime import datetime
from pathlib import Path


def create_backup_zip(data_dir: Path, backups_dir: Path) -> Path:
    """Create a zip backup of the data directory.

    Args:
        data_dir: Directory containing JSONL data files.
        backups_dir: Directory where the backup should be written.

    Returns:
        Path to the created zip file.

    Example:
        # backup_path = create_backup_zip(data_dir, data_dir / "backups")
    """

    backups_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base_name = backups_dir / f"keep-in-touch-backup-{stamp}"
    archive = shutil.make_archive(str(base_name), "zip", root_dir=data_dir)
    return Path(archive)
