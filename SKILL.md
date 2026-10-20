---
name: tgfoa-save-tools
description: Read quest/objective state from Tainted Grail - The Fall of Avalon save files (Unity, raw-deflate .data, template GUID map). Use when a player asks what quest stage they are at, what a session changed, or whether an objective is done.
---

# Tainted Grail: The Fall of Avalon — save format & workflow

Verified against patch 1.30, mono branch (PC/Steam).

## Locating saves

- `%USERPROFILE%\AppData\LocalLow\Questline\Fall of Avalon\<steamid>\Saved\*.zip`
- The LocalLow folder is named after the **developer**, Questline, not the publisher, so searching for "Awaken Realms" finds nothing.
- Each save `.zip` holds `MetaData.data` (version string, save name, JPEG thumbnail) plus one `.data` file per visited location (`CampaignMap_HOS` = world map) and `Gameplay.data` (global state, including quests).

## Payload encoding

- Every `.data` is **raw deflate** — no header, no encryption: `zlib.decompressobj(-15).decompress(blob)`.
- `TG.Main.dll` contains `StringCipher` / `RijndaelManaged` + passphrase code. That's for cloud sync only. Don't chase it.

## Gameplay.data layout

Decompressed it's an ECS-style binary model store:

1. A name table of LEB128-length-prefixed ASCII model paths (`Quest:N`, `Quest:N:Objective:M`, …)
2. A typed data region with UTF-16 strings and template GUIDs

### Quest-level state

```
7c 7d 7c 87 00 <32 hex chars: template guid> 00   7c <LEB128 tag 0x56|0x57> <LEB128 value>
```

- value **1 = active (in journal)**
- value **0 = completed OR dormant** (ambiguous at quest level; use objectives to tell them apart)
- The same `87 00 <guid>` signature also matches achievements and other systems. Filter to GUIDs present in the quest template map.

### Objective-level state

- Key: UTF-16LE string `<32-hex quest guid>/<dashed 36-char objective guid>`
- Preceded (somewhere within ~1500 bytes; long `once.N` lists can sit in between) by a UTF-16 `state` field: `s\0t\0a\0t\0e\0 \0\0 06 <value>`
- **2 = completed, 1 = current, 0/absent = not started**

## Template map (GUID → quest name)

Source: `<install>\Fall of Avalon_Data\StreamingAssets\aa\StandaloneWindows64\templates.quests_assets_all.bundle` (Unity Addressables). 269 quests + 981 objectives at patch 1.30.

- Quest templates: GameObject name = `SQ_*` / `MQ_*` / `TASK_*`, each with a 32-hex GUID.
- Objective templates have a dashed `guid` field. Their `description.ID` localization key **ends with the parent quest's GUID**; that's how objectives link to quests.
- Objectives reference map markers via `targetLocationReference.tags` (e.g. `Monk:BearLocation`).
- Display titles aren't in the bundle. Search by NPC/trial names, not the journal title (e.g. the *Fists of Fury* DLC questline is template `SQ_Monk`).

### Regenerating the template map

Do this after game patches if new quests show up as unmapped. Needs `pip install UnityPy`:

- `UnityPy.load(path)` returns an empty object list on this bundle (container revision `0.0.0`). Set `UnityPy.config.FALLBACK_UNITY_VERSION = '2022.3.0f1'` and instantiate `BundleFile(EndianBinaryReader(data), UnityPy.Environment())` directly.
- Walk MonoBehaviour typetrees and emit `{guid, go_name, questType, questCategory, objectives, path_id}` records into `scripts/quest_templates.json` (only `guid` and `go_name` are required by the reader).

### Localization

`StreamingAssets/Languages/languages.arch` is a UnityFS-style container (per-block zlib despite LZ4 flag bits). Its position table resolves to a non-English language, so English objective text isn't reliably recoverable from it. Absence of English there isn't absence of content.

## Workflow

1. Get the save(s): `scripts/tgfoa_save.py pull` (local) or `pull --host H --path P` (ssh).
2. `quests <save>` for the journal snapshot; `objectives <save> <QuestFragment>` for stage detail.
3. **Calibrate before trusting:** check 2–3 quests against the player's in-game journal, especially after a patch.
4. For "what did I just do", `diff` two saves that bracket a known play session. Use 3+ saves to separate *completed* from *dormant* (1 → 0 after a turn-in vs never-active).

## If a patch breaks the reader

- Confirm the `.data` files still inflate with raw deflate. A location file you didn't revisit should be byte-identical across two saves, which rules out per-save encryption.
- Save-model code lives in `Fall of Avalon_Data/Managed/TG.Main.dll` (mono build), not `Assembly-CSharp`. Decompile it with `dnfile` + `dncil` rather than guessing at new tags. C# string literals sit in the `#US` heap as UTF-16LE.
- Re-check the quest and objective state values against the in-game journal before trusting new output.
