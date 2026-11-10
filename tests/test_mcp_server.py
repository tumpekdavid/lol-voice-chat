from collections.abc import AsyncIterator

import pytest
from mcp import Client
from mcp.types import TextContent

from adapters.mcp_server import build_mcp_server
from core.query_handler import ChampionQueryHandler

pytestmark = pytest.mark.anyio

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
def anyio_backend() -> str:
    """Run the async tests on asyncio only."""
    return "asyncio"


@pytest.fixture
async def client() -> AsyncIterator[Client]:
    """An in-process MCP client connected to a server over `_DISPLAY_NAMES`."""
    repository = _InMemoryChampionRepository(_DISPLAY_NAMES)
    server = build_mcp_server(ChampionQueryHandler(repository))
    async with Client(server) as connected_client:
        yield connected_client


async def test_champion_name_enum_lists_every_champion(client: Client) -> None:
    """The one tool's schema offers exactly the served names as a required enum."""
    listing = await client.list_tools()

    (tool,) = listing.tools
    assert tool.name == "get_champion_abilities"
    champion_name_schema = tool.input_schema["properties"]["champion_name"]
    assert champion_name_schema["enum"] == sorted(_DISPLAY_NAMES)
    assert tool.input_schema["required"] == ["champion_name"]


async def test_listed_name_returns_markdown(client: Client) -> None:
    """A listed name returns its markdown as plain text, with no structured copy."""
    result = await client.call_tool(
        "get_champion_abilities", {"champion_name": "Kha'Zix"}
    )

    assert not result.is_error
    assert result.content == [TextContent(type="text", text="# Kha'Zix")]
    assert result.structured_content is None


@pytest.mark.parametrize("champion_name", ["Kazix", "wukong"])
async def test_unlisted_name_returns_tool_error(
    client: Client, champion_name: str
) -> None:
    """An unlisted name is a tool error the model can read, not a guess."""
    result = await client.call_tool(
        "get_champion_abilities", {"champion_name": champion_name}
    )

    assert result.is_error
    (content,) = result.content
    assert isinstance(content, TextContent)
    assert f"Unknown champion {champion_name!r}" in content.text
