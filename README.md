# tgfoa-save-tools

Read **exact quest and objective state** out of *Tainted Grail: The Fall of Avalon* save files — which quests are in your journal, which objectives are done, and what changed between two saves.

> **Disclaimer:** Unofficial fan tooling based on reverse-engineering; not affiliated with Larian / Awaken Realms / Questline. May break on game updates. No game assets redistributed.

## What you can learn from a save

- Every quest the game has touched, split into **active (in journal)** vs **completed-or-dormant**
- Per-objective state for any quest: **completed / current / not started**
- A quest-state diff between two saves ("what did that last session actually change?")

## Quickstart (zero setup — Python 3 stdlib only)

```bash
git clone https://github.com/CharlesMcquade/tgfoa-save-tools
cd tgfoa-save-tools
python3 scripts/tgfoa_save.py quests "/path/to/QuickSave_12.zip"
python3 scripts/tgfoa_save.py objectives "/path/to/QuickSave_12.zip" Monk
python3 scripts/tgfoa_save.py diff old.zip new.zip
```

Saves live at `%USERPROFILE%\AppData\LocalLow\Questline\Fall of Avalon\<steamid>\Saved\*.zip`
(note: the developer folder is **Questline**, not the publisher Awaken Realms). On Windows, `python3 scripts/tgfoa_save.py where` finds it and `pull` copies saves into `./saves/`.
From another machine over SSH:

```bash
python3 scripts/tgfoa_save.py pull --host mygamingpc \
  --path "/c/Users/<you>/AppData/LocalLow/Questline/Fall of Avalon/<steamid>/Saved"
python3 scripts/tgfoa_save.py quests        # newest save in ./saves
```

Quest names are internal template names (`SQ_*` side quests, `MQ_*` main quests, `TASK_*` tasks), mapped from GUIDs by `scripts/quest_templates.json`. Objectives print as GUIDs.

## Files

- `SKILL.md` — save-format notes + workflow (also usable as an AI-agent skill)
- `scripts/tgfoa_save.py` — the reader
- `scripts/quest_templates.json` — quest GUID → template name map (269 quests, patch 1.30). See SKILL.md → *Regenerating the template map* after game patches.

License: MIT
