from typing import Annotated

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field

from core.query_handler import ChampionQueryHandler, UnknownChampionError

_SERVER_NAME = "lol-champions"

# The client's model decides when to call the tool from this text alone.
_TOOL_DESCRIPTION = (
    "Get a League of Legends champion's abilities as markdown: passive and Q/W/E/R "
    "effects, damage and scaling per rank, cooldowns, costs and ranges. The data is "
    "patch-current, regenerated from the LoL Wiki each patch, so prefer it over your "
    "own memory for any ability number. One champion per call; for matchups, call it "
    "in parallel for each champion."
)
_CHAMPION_NAME_DESCRIPTION = (
    "Exact champion name from the list; map nicknames and misspellings to one of these."
)


def build_mcp_server(query_handler: ChampionQueryHandler) -> MCPServer:
    """Return an MCP server exposing `get_champion_abilities` over `query_handler`."""
    server = MCPServer(_SERVER_NAME)
    champion_names = query_handler.list_champions()

    # The enum is advertised in the schema but not validated by the SDK (unlike a
    # Literal), so an unlisted name reaches the handler and gets its error message.
    @server.tool(description=_TOOL_DESCRIPTION, structured_output=False)
    def get_champion_abilities(
        champion_name: Annotated[
            str,
            Field(
                description=_CHAMPION_NAME_DESCRIPTION,
                json_schema_extra={"enum": champion_names},
            ),
        ],
    ) -> str:
        try:
            return query_handler.get_champion_abilities(champion_name)
        except UnknownChampionError as error:
            raise ToolError(str(error)) from None

    return server
