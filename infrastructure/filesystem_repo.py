import json
from pathlib import Path

# Written by data_pipeline/transform/meraki_to_llm.py, mapping each display name
# to its markdown file name ("Wukong" → "monkeyking.md"); the layout is the contract.
_INDEX_FILE_NAME = "index.json"


class FilesystemChampionRepository:
    """Serves the transform's output: `index.json` plus one `.md` per champion."""

    def __init__(self, champions_dir: Path) -> None:
        self._champions_dir = champions_dir
        index_path = champions_dir / _INDEX_FILE_NAME
        self._markdown_file_names_by_display_name: dict[str, str] = json.loads(
            index_path.read_text(encoding="utf-8")
        )

    def list_display_names(self) -> list[str]:
        """Return every display name in the index, sorted."""
        return sorted(self._markdown_file_names_by_display_name)

    def get_champion_markdown(self, display_name: str) -> str:
        """Return one champion's markdown; raise KeyError for an unlisted name."""
        markdown_file_name = self._markdown_file_names_by_display_name[display_name]
        markdown_path = self._champions_dir / markdown_file_name
        return markdown_path.read_text(encoding="utf-8")
