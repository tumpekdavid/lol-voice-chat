from typing import Any

from data_pipeline.transform.meraki_to_llm import champion_to_markdown


def test_none_metadata_value_is_omitted() -> None:
    """A metadata field Meraki fills with the string "None" is left out."""
    markdown = _render_ability(castTime="None", affects="None")

    assert "Cast time" not in markdown
    assert "Affects" not in markdown


def test_partially_none_metadata_value_is_kept() -> None:
    """A mixed value like "0.25 / None" still carries information and is kept."""
    markdown = _render_ability(castTime="0.25 / None")

    assert "- Cast time: 0.25 / None" in markdown


def test_recharge_list_renders_as_per_rank_seconds() -> None:
    """The `rechargeRate` number list renders like other per-rank values."""
    markdown = _render_ability(rechargeRate=[16, 15.5, 15, 14.5, 14])

    assert "- Recharge: 16/15.5/15/14.5/14s" in markdown


def test_toggle_text_keeps_both_wordings() -> None:
    """Wiki toggle text "[A][B]" becomes "A (or B)", sharing trailing punctuation."""
    markdown = _render_ability(
        effects=[
            {
                "description": "can critically strike for[ (122.5% + 28%) damage. ]"
                "[ 70% total critical damage. ]",
                "leveling": [],
            }
        ]
    )

    assert (
        "can critically strike for (122.5% + 28%) damage "
        "(or 70% total critical damage)." in markdown
    )


def test_toggle_text_in_notes_is_spaced_before_following_word_and_comma() -> None:
    """Toggle text glued to surrounding words gets spaces, but none before a comma."""
    markdown = _render_ability(
        notes="Attack range is reduced[ to 0 ][ by 500 ], making him path near"
        " enemies[ 1 ][ 2 ]and more."
    )

    assert (
        "Attack range is reduced to 0 (or by 500), making him path near"
        " enemies 1 (or 2) and more." in markdown
    )


def test_footnote_markers_are_removed() -> None:
    """Wiki citation markers like "[3]" are dropped from notes."""
    markdown = _render_ability(notes="A max range of 2600 units[3].")

    assert "*Notes:* A max range of 2600 units." in markdown


def test_leveling_row_with_formula_in_units_is_skipped() -> None:
    """A row Meraki mis-parsed (formula left in the units) is dropped entirely."""
    markdown = _render_ability(
        effects=[
            {
                "description": "Fires a shot.",
                "leveling": [
                    {
                        "attribute": "Minimum Physical Damage per Bullet",
                        "modifiers": [
                            {"values": [0] * 5, "units": ["[25 / 30 ] × [1"] * 5},
                            {"values": [15] * 5, "units": ["% AD"] * 5},
                        ],
                    },
                    {
                        "attribute": "Physical Damage",
                        "modifiers": [
                            {"values": [10, 20, 30, 40, 50], "units": [""] * 5}
                        ],
                    },
                ],
            }
        ]
    )

    assert "Minimum Physical Damage per Bullet" not in markdown
    assert "  - Physical Damage: 10/20/30/40/50" in markdown


def _render_ability(**ability_fields: Any) -> str:
    ability = {"name": "Test Ability", "effects": [], **ability_fields}
    champion = {"name": "Tester", "title": "the Test", "abilities": {"Q": [ability]}}
    return champion_to_markdown(champion)
