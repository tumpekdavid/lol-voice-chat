from typing import Protocol


class ChampionRepository(Protocol):
    """Champion ability markdown, looked up by exact display name such as "Kai'Sa"."""

    def list_display_names(self) -> list[str]:
        """Return the display name of every champion served, sorted."""
        ...

    def get_champion_markdown(self, display_name: str) -> str:
        """Return one champion's markdown; raise KeyError for an unlisted name."""
        ...
