import argparse
import json
from pathlib import Path
from typing import Any

import httpx

from data_pipeline.shared.logging_config import get_logger

MERAKI_BASE_URL = "https://cdn.merakianalytics.com/riot/lol/resources/latest/en-US"

logger = get_logger(__name__)


def extract(output_dir: Path) -> None:
    """Download every champion's JSON into `output_dir`, skipping any not on the CDN."""
    output_dir.mkdir(parents=True, exist_ok=True)
    champion_names = get_champion_names()
    logger.info("Found %d champions", len(champion_names))
    skipped_champion_names: list[str] = []
    for champion_name in champion_names:
        try:
            champion = fetch_champion(champion_name)
        except httpx.HTTPStatusError as error:
            if error.response.status_code == 404:
                skipped_champion_names.append(champion_name)
                logger.warning("Skipped %s (not on CDN yet)", champion_name)
                continue
            raise
        destination = output_dir / f"{champion_name.lower()}.json"
        destination.write_text(json.dumps(champion, indent=2))
        logger.info("Fetched %s", champion_name)
    if skipped_champion_names:
        logger.warning(
            "Skipped %d champion(s) with no CDN data: %s",
            len(skipped_champion_names),
            ", ".join(skipped_champion_names),
        )


def get_champion_names() -> list[str]:
    """Return every champion key listed in the Meraki CDN index."""
    response = httpx.get(f"{MERAKI_BASE_URL}/champions.json", timeout=30)
    response.raise_for_status()
    return list(response.json().keys())


def fetch_champion(champion_name: str) -> dict[str, Any]:
    """Fetch one champion's raw JSON document from the Meraki CDN."""
    response = httpx.get(
        f"{MERAKI_BASE_URL}/champions/{champion_name}.json", timeout=30
    )
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="data/raw", type=Path)
    arguments = parser.parse_args()
    extract(arguments.output_dir)
