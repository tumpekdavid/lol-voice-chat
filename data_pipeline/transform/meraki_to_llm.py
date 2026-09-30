"""Convert Meraki Analytics champion JSON into compact, LLM-readable markdown.

Usage:
    python -m data_pipeline.transform.meraki_to_llm path/to/champion.json > champion.md
    python -m data_pipeline.transform.meraki_to_llm data/raw --output-dir data/champions
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from data_pipeline.shared.logging_config import get_logger

logger = get_logger(__name__)

_ABILITY_SLOTS = ("P", "Q", "W", "E", "R")

_MAX_CHAMPION_LEVEL = 18
_EMPTY_METADATA_VALUES = (None, "", "null", "none", "None")
# The wiki's toggleable text: "[A][B]" shows the same fact worded two ways.
_TOGGLE_TEXT_PATTERN = re.compile(r"\[([^\]]*)\]\[([^\]]*)\]")
_FOOTNOTE_MARKER_PATTERN = re.compile(r"\[\d+\]")
_MULTIPLE_SPACES_PATTERN = re.compile(r" {2,}")
_SPACE_BEFORE_PUNCTUATION_PATTERN = re.compile(r" +(?=[.,;](\s|$))")
_ABILITY_METADATA_FIELDS = (
    ("Targeting", "targeting"),
    ("Affects", "affects"),
    ("Damage type", "damageType"),
    ("Spell effects", "spellEffects"),
    ("Spellshieldable", "spellshieldable"),
    ("Projectile", "projectile"),
    ("On-hit effects", "onHitEffects"),
    ("Per-target cooldown", "onTargetCdStatic"),
    ("Cast time", "castTime"),
    ("Speed", "speed"),
    ("Width", "width"),
    ("Angle", "angle"),
    ("Target range", "targetRange"),
    ("Effect radius", "effectRadius"),
    ("Inner radius", "innerRadius"),
    ("Tether radius", "tetherRadius"),
)


def transform_directory(input_dir: Path, output_dir: Path) -> None:
    """Render every `<name>.json` in `input_dir` to `<name>.md` in `output_dir`."""
    output_dir.mkdir(parents=True, exist_ok=True)
    champion_paths = sorted(input_dir.glob("*.json"))
    logger.info("Found %d champions in %s", len(champion_paths), input_dir)
    for champion_path in champion_paths:
        markdown = champion_to_markdown(_load_champion(champion_path))
        destination = output_dir / f"{champion_path.stem}.md"
        destination.write_text(markdown, encoding="utf-8")
        logger.info("Transformed %s", champion_path.stem)


def champion_to_markdown(champion: dict[str, Any]) -> str:
    """Render one champion's Meraki JSON as a markdown document.

    >>> print(champion_to_markdown({
    ...     "name": "Alistar", "title": "the Minotaur", "resource": "MANA",
    ...     "attackType": "MELEE", "adaptiveType": "MAGIC_DAMAGE",
    ...     "roles": ["TANK", "SUPPORT"], "patchLastChanged": "25.04",
    ...     "abilities": {"Q": [{"name": "Pulverize", "targeting": "Auto"}]},
    ... }))
    # Alistar — the Minotaur
    <BLANKLINE>
    - Resource: MANA
    - Attack type: MELEE
    - Adaptive damage: MAGIC_DAMAGE
    - Roles: TANK, SUPPORT
    - Patch last changed: 25.04
    <BLANKLINE>
    # Abilities
    <BLANKLINE>
    ## Q — Pulverize
    - Targeting: Auto
    <BLANKLINE>
    <BLANKLINE>
    """
    lines = [
        f"# {champion.get('name', '')} — {champion.get('title', '')}",
        "",
        f"- Resource: {champion.get('resource', '')}",
        f"- Attack type: {champion.get('attackType', '')}",
        f"- Adaptive damage: {champion.get('adaptiveType', '')}",
    ]
    if champion.get("roles"):
        lines.append(f"- Roles: {', '.join(champion['roles'])}")
    if champion.get("positions"):
        lines.append(f"- Positions: {', '.join(champion['positions'])}")
    lines.append(f"- Patch last changed: {champion.get('patchLastChanged', '')}")
    lines.append("")

    lines.append("# Abilities")
    lines.append("")

    abilities_by_slot = champion.get("abilities", {})
    for slot in _ABILITY_SLOTS:
        for ability in abilities_by_slot.get(slot, []):
            lines.append(_format_ability(slot, ability))
            lines.append("")

    return "\n".join(lines)


def _load_champion(champion_path: Path) -> dict[str, Any]:
    """Read one champion's Meraki JSON from `champion_path`."""
    return json.loads(champion_path.read_text(encoding="utf-8"))


def _format_ability(slot: str, ability: dict[str, Any]) -> str:
    r"""Render one ability: heading, metadata bullets, effects, then notes.

    >>> print(_format_ability("Q", {
    ...     "name": "Pulverize",
    ...     "targeting": "Auto",
    ...     "castTime": "None",
    ...     "cooldown": {
    ...         "modifiers": [
    ...             {"values": [14, 13, 12, 11, 10], "units": ["", "", "", "", ""]},
    ...         ],
    ...         "affectedByCdr": True,
    ...     },
    ...     "effects": [{
    ...         "description": "Knocks up nearby enemies.",
    ...         "leveling": [{"attribute": "Magic Damage", "modifiers": [
    ...             {
    ...                 "values": [60, 100, 140, 180, 220],
    ...                 "units": ["", "", "", "", ""],
    ...             },
    ...             {
    ...                 "values": [80, 80, 80, 80, 80],
    ...                 "units": ["% AP", "% AP", "% AP", "% AP", "% AP"],
    ...             },
    ...         ]}],
    ...     }],
    ...     "notes": "Pulverize can be cast while dashing[2].\n\nBig table.",
    ... }))
    ## Q — Pulverize
    - Targeting: Auto
    - Cooldown: 14/13/12/11/10s (affected by ability haste)
    <BLANKLINE>
    **Effect 1.** Knocks up nearby enemies.
      - Magic Damage: 60/100/140/180/220 (+80% AP)
    <BLANKLINE>
    *Notes:* Pulverize can be cast while dashing.
    <BLANKLINE>
    """
    lines = [f"## {slot} — {ability.get('name', '')}"]

    for label, key in _ABILITY_METADATA_FIELDS:
        value = ability.get(key)
        if value not in _EMPTY_METADATA_VALUES:
            lines.append(f"- {label}: {value}")

    recharge_seconds = ability.get("rechargeRate")
    if recharge_seconds:
        lines.append(f"- Recharge: {_format_values(recharge_seconds, ['s'])}")

    cooldown = _format_cooldown(ability.get("cooldown"))
    if cooldown:
        lines.append(f"- Cooldown: {cooldown}")

    cost = _format_cost(ability.get("cost"))
    if cost:
        lines.append(f"- Cost: {cost}")

    lines.append("")

    for effect_number, effect in enumerate(ability.get("effects", []), 1):
        description = _clean_wiki_text(effect.get("description") or "")
        if description:
            lines.append(f"**Effect {effect_number}.** {description}")
        for leveling in effect.get("leveling", []):
            attribute = leveling.get("attribute", "")
            value = _format_modifiers(leveling.get("modifiers", []))
            if value:
                lines.append(f"  - {attribute}: {value}")
        lines.append("")

    notes = (ability.get("notes") or "").strip()
    if notes:
        # The wiki notes often end in huge cast-time interaction tables; keep only
        # the first prose block.
        first_block = _clean_wiki_text(notes.split("\n\n")[0])
        if first_block:
            lines.append(f"*Notes:* {first_block}")
            lines.append("")

    return "\n".join(lines)


def _format_cooldown(cooldown: dict[str, Any] | None) -> str:
    """Render a cooldown in seconds, noting whether ability haste reduces it.

    >>> _format_cooldown({
    ...     "modifiers": [
    ...         {"values": [14, 13, 12, 11, 10], "units": ["", "", "", "", ""]},
    ...     ],
    ...     "affectedByCdr": True,
    ... })
    '14/13/12/11/10s (affected by ability haste)'
    >>> _format_cooldown({
    ...     "modifiers": [{"values": [120, 100, 80], "units": ["", "", ""]}],
    ...     "affectedByCdr": False,
    ... })
    '120/100/80s (static, no ability haste)'
    """
    if not cooldown:
        return ""
    value = _format_modifiers(cooldown.get("modifiers", []))
    if not value:
        return ""
    haste = (
        "affected by ability haste"
        if cooldown.get("affectedByCdr")
        else "static, no ability haste"
    )
    if value.endswith(" per level"):
        value = value.replace(" per level", "s per level")
    else:
        value = value + "s"
    return f"{value} ({haste})"


def _format_cost(cost: dict[str, Any] | None) -> str:
    """Render an ability's resource cost.

    >>> _format_cost({
    ...     "modifiers": [
    ...         {"values": [50, 55, 60, 65, 70], "units": ["", "", "", "", ""]},
    ...     ],
    ... })
    '50/55/60/65/70'
    """
    if not cost:
        return ""
    return _format_modifiers(cost.get("modifiers", []))


def _clean_wiki_text(text: str) -> str:
    """Rewrite toggle text "[A][B]" as "A (or B)"; drop footnotes and extra spaces.

    >>> _clean_wiki_text("strike for[ 50% damage. ][ 70% total damage. ]  Heals.[3]")
    'strike for 50% damage (or 70% total damage). Heals.'
    >>> _clean_wiki_text("range is reduced[ to 0 ][ by 500 ], so he walks")
    'range is reduced to 0 (or by 500), so he walks'
    """
    text = _TOGGLE_TEXT_PATTERN.sub(_format_toggle_text, text)
    text = _FOOTNOTE_MARKER_PATTERN.sub("", text)
    text = _MULTIPLE_SPACES_PATTERN.sub(" ", text)
    return _SPACE_BEFORE_PUNCTUATION_PATTERN.sub("", text).strip()


def _format_toggle_text(match: re.Match[str]) -> str:
    """Turn one "[A][B]" match into " A (or B) ", hoisting shared end punctuation.

    >>> _format_toggle_text(_TOGGLE_TEXT_PATTERN.search("[ to 0. ][ by 500. ]"))
    ' to 0 (or by 500). '
    """
    first_wording = match.group(1).strip()
    second_wording = match.group(2).strip()
    shared_punctuation = ""
    if first_wording[-1:] in (".", ",") and second_wording[-1:] == first_wording[-1:]:
        shared_punctuation = first_wording[-1]
        first_wording = first_wording[:-1]
        second_wording = second_wording[:-1]
    return f" {first_wording} (or {second_wording}){shared_punctuation} "


def _format_modifiers(modifiers: list[dict[str, Any]]) -> str:
    """Join modifiers into one value: the first is the base, the rest are scalings.

    >>> _format_modifiers([
    ...     {"values": [60, 100, 140, 180, 220], "units": ["", "", "", "", ""]},
    ...     {
    ...         "values": [80, 80, 80, 80, 80],
    ...         "units": ["% AP", "% AP", "% AP", "% AP", "% AP"],
    ...     },
    ... ])
    '60/100/140/180/220 (+80% AP)'
    >>> _format_modifiers([
    ...     {"values": [0, 0], "units": ["[25 / 30 ] × [1", "[25 / 30 ] × [1"]},
    ... ])
    ''
    """
    # Meraki mis-parses some wiki formulas, leaving zeroed values and the formula
    # in the units; such a row is unrecoverable.
    if any("[" in unit for modifier in modifiers for unit in modifier.get("units", [])):
        return ""
    parts = []
    for modifier in modifiers:
        formatted = _format_values(
            modifier.get("values", []), modifier.get("units", [])
        )
        if formatted:
            parts.append(formatted)
    if not parts:
        return ""
    base, *scalings = parts
    return " ".join([base, *(f"(+{scaling})" for scaling in scalings)])


def _format_values(values: list[float], units: list[str]) -> str:
    """Collapse a value list into a per-level range, a single value, or per-rank.

    >>> _format_values([60, 100, 140, 180, 220], ["", "", "", "", ""])
    '60/100/140/180/220'
    >>> _format_values(
    ...     [80, 80, 80, 80, 80],
    ...     ["% AP", "% AP", "% AP", "% AP", "% AP"],
    ... )
    '80% AP'
    >>> _format_values(
    ...     [22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5],
    ...     ["s", "s", "s", "s", "s", "s", "s", "s", "s",
    ...      "s", "s", "s", "s", "s", "s", "s", "s", "s"],
    ... )
    '22-5s per level'
    """
    if not values:
        return ""
    formatted = [_format_number(value) for value in values]
    unit = units[0] if units else ""

    if len(values) == _MAX_CHAMPION_LEVEL:
        return f"{formatted[0]}-{formatted[-1]}{unit} per level"

    if len(set(formatted)) == 1:
        return f"{formatted[0]}{unit}"

    return f"{'/'.join(formatted)}{unit}"


def _format_number(number: float) -> str:
    """Render without a trailing .0 and with at most four decimals.

    >>> _format_number(14.0), _format_number(67.5), _format_number(0.123456)
    ('14', '67.5', '0.1235')
    """
    if isinstance(number, float):
        if number.is_integer():
            return str(int(number))
        return f"{number:.4f}".rstrip("0").rstrip(".")
    return str(number)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "input_path",
        nargs="?",
        default="/dev/stdin",
        type=Path,
        help="a champion JSON file (markdown goes to stdout) or a directory of them",
    )
    parser.add_argument("--output-dir", default="data/champions", type=Path)
    arguments = parser.parse_args()
    if arguments.input_path.is_dir():
        transform_directory(arguments.input_path, arguments.output_dir)
    else:
        # Champion text contains non-ASCII (em dashes, accents) that a non-UTF-8
        # console encoding would fail on.
        sys.stdout.reconfigure(encoding="utf-8")
        print(champion_to_markdown(_load_champion(arguments.input_path)))
