"""CSV / JSON file export helpers ([Unit II] File Management).

Writing exported rows to a real file is one of the file-management
requirements: files are opened with ``with`` context managers so they are
always closed, even if an error happens mid-write.
"""

import csv
import json
import os
from datetime import datetime

from config import SETTINGS
from utils.exceptions import ValidationError


def export_to_file(entity, rows, file_format="csv"):
    """Write ``rows`` (list of dicts) to data/exports/<entity>_<timestamp>.<ext>."""
    if file_format not in ("csv", "json"):
        raise ValidationError("Format must be 'csv' or 'json'.")

    exports_dir = SETTINGS["exports_dir"]
    os.makedirs(exports_dir, exist_ok=True)  # create folder if missing

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{entity}_{timestamp}.{file_format}"
    path = os.path.join(exports_dir, filename)

    if file_format == "csv":
        # newline="" avoids blank lines between rows on Windows
        with open(path, "w", newline="", encoding="utf-8") as csv_file:
            fieldnames = list(rows[0].keys()) if rows else ["(no rows)"]
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    else:
        with open(path, "w", encoding="utf-8") as json_file:
            json.dump(rows, json_file, indent=2, ensure_ascii=False)

    return {
        "entity": entity,
        "format": file_format,
        "file": filename,
        "path": path,
        "rows": len(rows),
        "size_bytes": os.path.getsize(path),
        "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def list_export_files():
    """List previously exported files (newest first)."""
    exports_dir = SETTINGS["exports_dir"]
    if not os.path.isdir(exports_dir):
        return []

    files = []
    # Timestamps in filenames sort chronologically, so reverse = newest first
    for name in sorted(os.listdir(exports_dir), reverse=True):
        full_path = os.path.join(exports_dir, name)
        if os.path.isfile(full_path):
            stats = os.stat(full_path)
            files.append(
                {
                    "file": name,
                    "size_bytes": stats.st_size,
                    "modified": datetime.fromtimestamp(stats.st_mtime).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                }
            )
    return files
