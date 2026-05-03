"""
Convert a Meraki Analytics champion JSON into a compact, LLM-readable
markdown document.

Usage:
    python meraki_to_llm.py path/to/Champion.json > Champion.md
"""

import json
import sys


def fmt_num(n):
    """Render numbers compactly (no trailing .0, no excessive decimals)."""
    if isinstance(n, bool):
        return str(n)
    if isinstance(n, float):
        if n.is_integer():
            return str(int(n))
        return f"{n:.4f}".rstrip("0").rstrip(".")
    return str(n)


def fmt_values(values, units):
    """
    Format a list of values + their units into a string.
    - 18 entries  -> per-level range, e.g. "22-10s (per level)"
    - all identical -> single value, e.g. "80% AD"
    - otherwise   -> per-rank, e.g. "10/25/40/55/70"
    """
    if not values:
        return ""
    formatted = [fmt_num(v) for v in values]
    unit = units[0] if units else ""

    if len(values) == 18:
        return f"{formatted[0]}-{formatted[-1]}{unit} per level"

    if len(set(formatted)) == 1:
        return f"{formatted[0]}{unit}"

    return f"{'/'.join(formatted)}{unit}"


def fmt_modifiers(modifiers):
    """
    Combine multiple modifiers into one string.
    First modifier is the base value; subsequent ones are scalings.
    e.g. base "10/25/40/55/70" + scaling "60/67.5/75/82.5/90% AD"
         -> "10/25/40/55/70 (+60/67.5/75/82.5/90% AD)"
    """
    parts = []
    for mod in modifiers:
        s = fmt_values(mod.get("values", []), mod.get("units", []))
        if s:
            parts.append(s)
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    return parts[0] + " " + " ".join(f"(+{p})" for p in parts[1:])


def fmt_cooldown(cd):
    if not cd:
        return ""
    s = fmt_modifiers(cd.get("modifiers", []))
    if not s:
        return ""
    haste = (
        "affected by ability haste"
        if cd.get("affectedByCdr")
        else "static, no ability haste"
    )
    # If value already ends with 'per level', insert 's' before that suffix.
    if s.endswith(" per level"):
        s = s.replace(" per level", "s per level")
    else:
        s = s + "s"
    return f"{s} ({haste})"


def fmt_cost(cost):
    if not cost:
        return ""
    return fmt_modifiers(cost.get("modifiers", []))


def fmt_ability(slot, ability):
    out = []
    out.append(f"## {slot} — {ability.get('name', '')}")

    # Metadata block
    meta_keys = [
        ("Targeting", ability.get("targeting")),
        ("Affects", ability.get("affects")),
        ("Damage type", ability.get("damageType")),
        ("Spell effects", ability.get("spellEffects")),
        ("Spellshieldable", ability.get("spellshieldable")),
        ("Projectile", ability.get("projectile")),
        ("On-hit effects", ability.get("onHitEffects")),
        ("Per-target cooldown", ability.get("onTargetCdStatic")),
        ("Cast time", ability.get("castTime")),
        ("Speed", ability.get("speed")),
        ("Width", ability.get("width")),
        ("Angle", ability.get("angle")),
        ("Target range", ability.get("targetRange")),
        ("Effect radius", ability.get("effectRadius")),
        ("Inner radius", ability.get("innerRadius")),
        ("Tether radius", ability.get("tetherRadius")),
        ("Recharge", ability.get("rechargeRate")),
    ]

    for label, val in meta_keys:
        if val not in (None, "", "null", "none"):
            out.append(f"- {label}: {val}")

    cd = fmt_cooldown(ability.get("cooldown"))
    if cd:
        out.append(f"- Cooldown: {cd}")

    cost = fmt_cost(ability.get("cost"))
    if cost:
        out.append(f"- Cost: {cost}")

    out.append("")  # blank line before effects

    # Effects
    for i, effect in enumerate(ability.get("effects", []), 1):
        desc = (effect.get("description") or "").strip()
        if desc:
            out.append(f"**Effect {i}.** {desc}")
        for lvl in effect.get("leveling", []):
            attr = lvl.get("attribute", "")
            val = fmt_modifiers(lvl.get("modifiers", []))
            if val:
                out.append(f"  - {attr}: {val}")
        out.append("")

    # Notes — keep, but trim. The wiki notes can be huge tables.
    notes = (ability.get("notes") or "").strip()
    if notes:
        # Drop the giant cast-time interaction tables; keep first prose block.
        first_block = notes.split("\n\n")[0].strip()
        if first_block:
            out.append(f"*Notes:* {first_block}")
            out.append("")

    return "\n".join(out)


def convert(data):
    out = []
    out.append(f"# {data.get('name', '')} — {data.get('title', '')}")
    out.append("")
    out.append(f"- Resource: {data.get('resource', '')}")
    out.append(f"- Attack type: {data.get('attackType', '')}")
    out.append(f"- Adaptive damage: {data.get('adaptiveType', '')}")
    if data.get("roles"):
        out.append(f"- Roles: {', '.join(data['roles'])}")
    if data.get("positions"):
        out.append(f"- Positions: {', '.join(data['positions'])}")
    out.append(f"- Patch last changed: {data.get('patchLastChanged', '')}")
    out.append("")

    out.append("# Abilities")
    out.append("")

    for slot in ("P", "Q", "W", "E", "R"):
        for ability in data.get("abilities", {}).get(slot, []):
            out.append(fmt_ability(slot, ability))
            out.append("")

    return "\n".join(out)


if __name__ == "__main__":
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", closefd=False)
    path = sys.argv[1] if len(sys.argv) > 1 else "/dev/stdin"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    print(convert(data))
