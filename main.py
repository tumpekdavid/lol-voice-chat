import logging
import os
import sys
from pathlib import Path

from adapters.mcp_server import build_mcp_server
from core.query_handler import ChampionQueryHandler
from infrastructure.filesystem_repo import FilesystemChampionRepository

_DEFAULT_DATA_DIR = Path(__file__).resolve().parent / "data"
_LOG_FORMAT = "%(asctime)s %(levelname)-5s [%(name)s] %(message)s"

_logger = logging.getLogger(__name__)


def main() -> None:
    """Serve champion abilities to an MCP client over stdio."""
    # stdout carries the MCP protocol, so logs go to stderr. Configured before the
    # server is built, which makes the SDK's own logging.basicConfig a no-op.
    logging.basicConfig(
        stream=sys.stderr,
        level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        format=_LOG_FORMAT,
    )
    data_dir = Path(os.environ.get("DATA_DIR", _DEFAULT_DATA_DIR))
    repository = FilesystemChampionRepository(data_dir / "champions")
    query_handler = ChampionQueryHandler(repository)
    server = build_mcp_server(query_handler)
    _logger.info(
        "Serving %d champions from %s", len(query_handler.list_champions()), data_dir
    )
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
