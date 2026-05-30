import argparse
import json
from pathlib import Path

import httpx

from data_pipeline.shared.logging_config import get_logger

MERAKI_BASE = "https://cdn.merakianalytics.com/riot/lol/resources/latest/en-US"

logger = get_logger(__name__)


def get_champion_names() -> list[str]:
    resp = httpx.get(f"{MERAKI_BASE}/champions.json", timeout=30)
    resp.raise_for_status()
    return list(resp.json().keys())


def fetch_champion(champion_name: str) -> dict:
    resp = httpx.get(
        f"{MERAKI_BASE}/champions/{champion_name}.json", timeout=30)
    resp.raise_for_status()
    return resp.json()


def extract(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    champion_names = get_champion_names()
    logger.info("Found %d champions", len(champion_names))
    skipped = []
    for name in champion_names:
        try:
            data = fetch_champion(name)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                skipped.append(name)
                logger.warning("Skipped %s (not on CDN yet)", name)
                continue
            raise
        dest = output_dir / f"{name.lower()}.json"
        dest.write_text(json.dumps(data, indent=2))
        logger.info("Fetched %s", name)
    if skipped:
        logger.warning(
            "Skipped %d champion(s) with no CDN data: %s",
            len(skipped),
            ", ".join(skipped),
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="data/raw", type=Path)
    args = parser.parse_args()
    extract(args.output_dir)
