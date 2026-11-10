# Open work

Picked up from the session on 2026-11-10. Do these in order: the validation set is only worth writing once the data comes from a live source.

## 1. Replace the data source (Meraki is dead)

Meraki's CDN stopped updating in mid-2025, so our data is more than a year behind the live game. The tool description still calls it "patch-current" and tells the model to prefer it over its own memory, which is currently false.

Evidence (checked 2026-11-10):

- The CDN's `champions.json` has `Last-Modified: Fri, 01 Aug 2025`.
- The newest champion in it is Yunara (released 2025-07-16).
- The newest `patchLastChanged` is 25.15 on the live CDN and 25.08 in our `data/raw/` (fetched 2026-05-26). Riot live is 26.22 (Data Dragon `16.22.1`).
- The scraper behind it, [meraki-analytics/lolstaticdata](https://github.com/meraki-analytics/lolstaticdata), was last committed to on 2025-11-12. We decided not to run it ourselves.

Candidates, probed but not evaluated:

- **CommunityDragon**: raw game files, current (`content-metadata.json` reports `16.22`). Example: `https://raw.communitydragon.org/latest/game/data/characters/aatrox/aatrox.bin.json`. Exact numbers, but tooltips are templated and spell calculations have to be resolved, the same problem that ruled out Data Dragon.
- **LoL Wiki via the MediaWiki API**: per-ability data templates, maintained (the Aatrox Q template was last edited 2026-10-03). Example: `https://wiki.leagueoflegends.com/en-us/api.php?action=query&prop=revisions&rvprop=content|timestamp&rvslots=main&format=json&titles=Template:Data_Aatrox/The_Darkin_Blade`. Wikitext with `#vardefine` and nested templates, so it needs a parser.

Changing the source changes a locked-in decision: update [decisions.md](decisions.md) ("Meraki Analytics CDN, not Riot Data Dragon"), the extract step, and the commands in [operations.md](operations.md).

## 2. Put the data's patch number in the tool response

Decided: one line at the top of each champion's markdown, written by the transform (for example "Data as of patch 26.22"). Put it in the response, not the tool description. In the response it sits next to the numbers the model quotes, and it stays correct if the ETL re-runs while a session is open. Remove "patch-current" from `_TOOL_DESCRIPTION` in `adapters/mcp_server.py`.

Where the number comes from depends on the new source. Meraki has no dataset-level version, only `patchLastChanged` per champion.

## 3. Write the validation question set

Phase 1 still has to show, against a real model, that names resolve, that the model calls the tool, and that the data can answer real players' questions. Run the prompt below in a fresh Claude Code session. It is written for the Meraki data: once the source changes, update its "Context" paragraph to match.

````text
Build a validation question set for this project's MCP server (tool: get_champion_abilities). Write it to docs/validation.md.

Context: this repo renders League of Legends champion ability data from the Meraki CDN into data/champions/<key>.md, one file per champion, plus data/champions/index.json, which maps display names to file names. Phase 1 exists to check, against a real model, whether (a) it resolves champion names correctly, (b) it calls the tool instead of answering from memory, and (c) the data can actually answer real players' questions. Read docs/architecture.md and docs/decisions.md first for context.

GOAL
Write about 25 questions that a Platinum+ player would actually ask mid-game or in champ select. They should be short, casual and specific, the way people type in chat or say out loud. Examples of the tone:
- "does alistar E give movement speed?"
- "what does gwen W block exactly?"
- "is yasuo windwall able to block ashe ult?"
- "how long is malph ult knockup?"
Don't write textbook questions ("Describe Aatrox's kit"). Real players ask about thresholds, cooldowns at a given rank, what counts as a cast, what can be blocked or cleansed, whether something applies on-hit, and power spikes.

CATEGORIES (at least the stated count each; label every question with its category):
1. Name resolution (≥5). Refer to champions the way players do: nicknames, misspellings, missing apostrophes or spaces, and titles or descriptions. Examples: "wu kong", "kaisa", "mf", "j4", "nunu", "tf", "the void bug", "asol", "reksai", "kog". Include at least one tricky case where the display name differs from the file key (Wukong → monkeyking.md, Nunu & Willump → nunu.md). The expected answer must give the exact display name from index.json that the model should pick.
2. Tool use / exact numbers (≥6). Questions whose answer is a number the model might misremember from an older patch: cooldowns at a specific rank, base damage at rank N, AP/AD ratios, shield or heal amounts, slow percentage, durations, ranges, mana costs. Prefer champions whose "Patch last changed" is recent, since those are the ones where memory is most likely stale.
3. Data quality / mechanics and edge cases (≥6). Interactions and passives: what triggers a passive, whether something is a dash or a blink, whether it can be cancelled, whether it applies on-hit effects, what a shield or untargetability blocks, stack counts, thresholds, recast windows, and whether a cooldown refunds on kill or takedown.
4. Matchups (≥4). Two-champion questions that need both kits, so the model should make two tool calls (in parallel, ideally). Examples: "can I dodge darius Q pull with ezreal E", "who wins level 2 between renekton and fiora, cooldown-wise", "does morgana black shield block leona E".
5. Negative / out-of-data (≥4):
   - one question about a champion that doesn't exist (expected: the model says so and doesn't guess),
   - one about items, runes or summoner spells (out of scope per docs/operations.md; expected: the model says the tool doesn't cover it),
   - two plausible ability questions where the markdown genuinely does NOT contain the answer (expected: the model says the data doesn't cover it and doesn't invent a number).

EXPECTED ANSWERS — IMPORTANT
- Derive every expected answer ONLY from data/champions/<key>.md (and index.json for names). Do NOT use your own LoL knowledge as ground truth. Open the file and quote it.
- For each question, record: the champion file(s) used, the exact quoted line(s) from the markdown supporting the answer, and a 1–2 sentence expected answer.
- If you find that the markdown can't answer a question a real player would ask, keep the question and mark it "DATA GAP", noting what's missing (for example, the patch is unknown, a per-rank value is missing, an interaction isn't described, or the formatting is garbled). These gaps are a key output.
- If the markdown seems to contradict what you believe the current in-game behaviour is, keep the markdown answer as expected, but add a "SUSPECT" note with your concern.

FORMAT for docs/validation.md:
- A short intro: what the file is for and how to use it (ask each question in a fresh Claude Code session with the lol-champions MCP server connected, then fill in the result columns).
- One table per category with columns:
  # | Question | Champion(s) / expected tool calls | Expected answer | Source (file + quoted line) | Notes (DATA GAP / SUSPECT) | Result: tool called? | Result: correct? | Result: notes
  Leave the three Result columns empty.
- At the end, a "Data gaps found while writing" summary listing every DATA GAP and SUSPECT item.

Rules:
- Cover a spread of champions: different classes, roles and resource types. Don't use the same champion more than twice.
- Don't modify any code or data, only create docs/validation.md.
- Don't commit.
- When done, reply with: the number of questions per category, and the list of data gaps.
````
