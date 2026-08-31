from pathlib import Path


class CDCLoader:
    """
    Loads CDC knowledge documents from the local knowledge directory.
    """

    def __init__(self, knowledge_dir: str = "knowledge/cdc"):
        self.knowledge_dir = Path(knowledge_dir)

    def exists(self) -> bool:
        return self.knowledge_dir.exists()

    def list_documents(self) -> list[Path]:
        if not self.exists():
            return []

        return sorted(
            self.knowledge_dir.rglob("*"),
            key=lambda p: str(p)
        )
