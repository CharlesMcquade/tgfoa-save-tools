# tgfoa-save-tools

Read quest and objective state from *Tainted Grail: The Fall of Avalon* saves: what's in your journal, which objectives are done and what changed between two saves. Pure Python 3 standard library, with no game install or extraction step.

> Unofficial fan project. Not affiliated with or endorsed by Questline or Awaken Realms. The save format was reverse-engineered on PC (Steam) patch 1.30 and may change with future patches. Contains no game code or assets. `quest_templates.json` maps quest GUIDs to their internal template names only.

## What it reads

- **Journal snapshot:** every quest the save has touched, split into *active (in journal)* and *completed or dormant*.
- **Objective state** for any quest: *completed*, *current* or *not started*.
- **Save diff:** quests that started, ended or changed state between two saves.

## Quickstart

```bash
git clone https://github.com/CharlesMcquade/tgfoa-save-tools
cd tgfoa-save-tools
python3 scripts/tgfoa_save.py quests     "/path/to/QuickSave_12.zip"
python3 scripts/tgfoa_save.py objectives "/path/to/QuickSave_12.zip" Monk
python3 scripts/tgfoa_save.py diff       QuickSave_11.zip QuickSave_12.zip
```

Example (`quests`):

```
ACTIVE (in journal):
   MQ_AWorldToWin
   SQ_Monk
   ...
OTHER (completed or dormant):
   ...
```

## Where the saves are

```
%USERPROFILE%\AppData\LocalLow\Questline\Fall of Avalon\<steamid>\Saved\*.zip
```

The folder is named after the developer, **Questline**, not the publisher. On the gaming PC, `where` prints the path and `pull` copies every save into `./saves/` (with no save argument, `quests` reads the newest save there). To read from another machine over SSH:

```bash
python3 scripts/tgfoa_save.py pull --host mygamingpc \
  --path "/c/Users/<you>/AppData/LocalLow/Questline/Fall of Avalon/<steamid>/Saved"
python3 scripts/tgfoa_save.py quests        # newest save in ./saves
```

`pull --host` streams the saves over ssh+tar, which keeps the original timestamps so "newest save" stays correct. The remote must have `tar`; Windows 10+ includes it.

## Reading the output

Quests print as internal template names: `MQ_*` main quests, `SQ_*` side quests and `TASK_*` tasks. These are not journal titles. Search by NPC or trial name; the *Fists of Fury* DLC questline, for example, is `SQ_Monk`. Objectives print as GUIDs. A quest at state 0 may be completed or never started; use `objectives`, or `diff` across several saves, to tell which. See `SKILL.md`.

## Files

| Path | Purpose |
|---|---|
| `scripts/tgfoa_save.py` | Reader: `quests`, `objectives`, `diff`, `pull`, `where` |
| `scripts/quest_templates.json` | Quest GUID → template name, 269 quests (patch 1.30) |
| `SKILL.md` | Save format, state encodings, regenerating the GUID map after a patch. Also usable as an AI-agent skill. |

## License

MIT
