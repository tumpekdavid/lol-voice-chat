import pytest

from core.query_handler import ChampionQueryHandler, UnknownChampionError

_DISPLAY_NAMES = ["Kha'Zix", "Nunu & Willump", "Wukong"]


class _InMemoryChampionRepository:
    def __init__(self, display_names: list[str]) -> None:
        self._markdown_by_display_name = {
            display_name: f"# {display_name}" for display_name in display_names
        }

    def list_display_names(self) -> list[str]:
        return sorted(self._markdown_by_display_name)

    def get_champion_markdown(self, display_name: str) -> str:
        return self._markdown_by_display_name[display_name]


@pytest.fixture
def handler() -> ChampionQueryHandler:
    """A handler over an in-memory repository of `_DISPLAY_NAMES`."""
    return ChampionQueryHandler(_InMemoryChampionRepository(_DISPLAY_NAMES))


def test_list_champions_returns_repository_names(
    handler: ChampionQueryHandler,
) -> None:
    """The listed names are exactly the repository's display names."""
    assert handler.list_champions() == sorted(_DISPLAY_NAMES)


@pytest.mark.parametrize("champion_name", _DISPLAY_NAMES)
def test_listed_name_returns_markdown(
    handler: ChampionQueryHandler, champion_name: str
) -> None:
    """Every listed name, punctuation and all, returns that champion's markdown."""
    assert handler.get_champion_abilities(champion_name) == f"# {champion_name}"


@pytest.mark.parametrize("champion_name", ["khazix", "Nunu", "MonkeyKing", ""])
def test_unlisted_name_raises_unknown_champion(
    handler: ChampionQueryHandler, champion_name: str
) -> None:
    """Near misses are refused, not resolved; the enum is the only vocabulary."""
    with pytest.raises(UnknownChampionError):
        handler.get_champion_abilities(champion_name)


def test_unknown_champion_message_names_the_request(
    handler: ChampionQueryHandler,
) -> None:
    """The error quotes the rejected name so the model can see what it sent."""
    with pytest.raises(UnknownChampionError, match="'Kazix'"):
        handler.get_champion_abilities("Kazix")
