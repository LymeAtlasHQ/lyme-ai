from pathlib import Path


class DocumentReader:
    def list_documents(self, directory: str):
        path = Path(directory)
        return [file for file in path.rglob("*") if file.is_file()]
