from core.repository import ChampionRepository


class ChampionQueryHandler:
    """The champion tools' behavior, shared by every adapter that exposes them."""

    def __init__(self, repository: ChampionRepository) -> None:
        self._repository = repository

    def list_champions(self) -> list[str]:
        """Return every champion name; adapters offer these as the tool's enum."""
        return self._repository.list_display_names()

    def get_champion_abilities(self, champion_name: str) -> str:
        """Return one champion's markdown; raise UnknownChampionError if unlisted."""
        try:
            return self._repository.get_champion_markdown(champion_name)
        except KeyError:
            raise UnknownChampionError(champion_name) from None


class UnknownChampionError(LookupError):
    """A champion name outside `list_champions()`; the message is for the model."""

    def __init__(self, champion_name: str) -> None:
        super().__init__(
            f"Unknown champion {champion_name!r}. Use one of the listed champion "
            "names, spelled exactly as listed."
        )
