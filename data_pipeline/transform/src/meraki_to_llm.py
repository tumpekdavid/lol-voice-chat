"""Convert a Meraki Analytics champion JSON into compact, LLM-readable markdown.

Usage:
    python meraki_to_llm.py path/to/champion.json > champion.md
"""

import json
import sys
from typing import Any

_ABILITY_SLOTS = ("P", "Q", "W", "E", "R")

_MAX_CHAMPION_LEVEL = 18
_EMPTY_METADATA_VALUES = (None, "", "null", "none")
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
    ("Recharge", "rechargeRate"),
)


def champion_to_markdown(champion: dict[str, Any]) -> str:
    """Render one champion's Meraki JSON as a markdown document."""
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


def _format_ability(slot: str, ability: dict[str, Any]) -> str:
    lines = [f"## {slot} — {ability.get('name', '')}"]

    for label, key in _ABILITY_METADATA_FIELDS:
        value = ability.get(key)
        if value not in _EMPTY_METADATA_VALUES:
            lines.append(f"- {label}: {value}")

    cooldown = _format_cooldown(ability.get("cooldown"))
    if cooldown:
        lines.append(f"- Cooldown: {cooldown}")

    cost = _format_cost(ability.get("cost"))
    if cost:
        lines.append(f"- Cost: {cost}")

    lines.append("")

    for effect_number, effect in enumerate(ability.get("effects", []), 1):
        description = (effect.get("description") or "").strip()
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
        first_block = notes.split("\n\n")[0].strip()
        if first_block:
            lines.append(f"*Notes:* {first_block}")
            lines.append("")

    return "\n".join(lines)


def _format_cooldown(cooldown: dict[str, Any] | None) -> str:
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
    if not cost:
        return ""
    return _format_modifiers(cost.get("modifiers", []))


def _format_modifiers(modifiers: list[dict[str, Any]]) -> str:
    """Join modifiers as base plus scalings, e.g. "10/25/40 (+60/67.5/75% AD)"."""
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
    """Format as a per-level range, a single value, or per-rank "a/b/c"."""
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
    """Render without a trailing .0 and with at most four decimals."""
    if isinstance(number, float):
        if number.is_integer():
            return str(int(number))
        return f"{number:.4f}".rstrip("0").rstrip(".")
    return str(number)


if __name__ == "__main__":
    # Champion text contains non-ASCII (em dashes, accents) that a non-UTF-8
    # console encoding would fail on.
    sys.stdout.reconfigure(encoding="utf-8")
    path = sys.argv[1] if len(sys.argv) > 1 else "/dev/stdin"
    with open(path, encoding="utf-8") as champion_file:
        champion = json.load(champion_file)
    print(champion_to_markdown(champion))
