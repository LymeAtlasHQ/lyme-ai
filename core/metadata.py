from pathlib import Path
from datetime import datetime


class MetadataExtractor:
    def extract(self, file_path: Path):
        stat = file_path.stat()

        return {
            "filename": file_path.name,
            "path": str(file_path),
            "extension": file_path.suffix,
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }
