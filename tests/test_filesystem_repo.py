import json
from pathlib import Path

import pytest

from infrastructure.filesystem_repo import FilesystemChampionRepository


@pytest.fixture
def repository(tmp_path: Path) -> FilesystemChampionRepository:
    """A repository over two champions, one in a file not named after it."""
    index = {"Aatrox": "aatrox.md", "Wukong": "monkeyking.md"}
    (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")
    (tmp_path / "aatrox.md").write_text("# Aatrox — the Darkin Blade\n")
    (tmp_path / "monkeyking.md").write_text("# Wukong — the Monkey King\n")
    return FilesystemChampionRepository(tmp_path)


def test_lists_index_display_names_sorted(
    repository: FilesystemChampionRepository,
) -> None:
    """The served names are the index's display names, not file names."""
    assert repository.list_display_names() == ["Aatrox", "Wukong"]


def test_reads_markdown_from_the_indexed_file(
    repository: FilesystemChampionRepository,
) -> None:
    """A display name is served from the markdown file the index points it at."""
    markdown = repository.get_champion_markdown("Wukong")

    assert markdown == "# Wukong — the Monkey King\n"


@pytest.mark.parametrize("display_name", ["monkeyking", "wukong", "Nobody"])
def test_rejects_names_not_in_the_index(
    repository: FilesystemChampionRepository, display_name: str
) -> None:
    """File stems, other casings and unknown names are all refused; no normalization."""
    with pytest.raises(KeyError):
        repository.get_champion_markdown(display_name)
