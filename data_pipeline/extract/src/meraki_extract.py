import argparse
import json
from pathlib import Path

import httpx

MERAKI_BASE = "https://cdn.merakianalytics.com/riot/lol/resources/latest/en-US"


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
    print(f"Found {len(champion_names)} champions")
    skipped = []
    for name in champion_names:
        try:
            data = fetch_champion(name)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                skipped.append(name)
                print(f"  {name} (skipped — not on CDN yet)")
                continue
            raise
        dest = output_dir / f"{name.lower()}.json"
        dest.write_text(json.dumps(data, indent=2))
        print(f"  {name}")
    if skipped:
        print(
            f"\nSkipped {len(skipped)} champion(s) with no CDN data: {', '.join(skipped)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="data/raw", type=Path)
    args = parser.parse_args()
    extract(args.output_dir)
