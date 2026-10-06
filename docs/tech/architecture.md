# Architecture

Majora City is C source layered on top of the [zeldaret/mm](https://github.com/zeldaret/mm) decompilation of
Majora's Mask (N64 US 1.0). This repository contains **only Majora City's own files and small patches**. The
decompilation is fetched at a pinned commit, the player's ROM provides the assets, and the result ships as a BPS
patch.

```
 this repo                                   build/mm  (managed decomp checkout, zeldaret/mm @ decomp.lock)
 ─────────                                   ──────────────────────────────────────────────────────────────
 mod/       new files ──── copied ─────────► src/overlays/actors/ovl_Mc_*/, src/code/mc/, include/mc/, assets/text/
 patches/   diffs     ──── git apply ──────► spec, actor table, z64save.h, z_play.c, z_sram_NES.c, text, Makefile
 tools/     setup / apply / build / check                │
                                                          ▼  make (IDO 7.1, the original compiler)
 your ROM ────────────────────────────────► baseroms/n64-us/ ──► build/n64-us/mm-n64-us-compressed.z64
                                                                         │
                                                tools/bps.py create      ▼
                                                                 dist/majora-city.bps   (what players download)
```

## Repository layout

| Path | Contents |
|---|---|
| `mod/` | New files, laid out exactly as they go into the decomp tree. `tools/apply.sh` refuses to let these overwrite a decomp file. |
| `patches/` | Unified diffs against the pinned decomp, one per engine file, applied in order. |
| `decomp.lock` | The decomp repository URL and commit. |
| `majora-city` | The user-facing builder: `build`, `update`, `doctor`, `patch`, `info`, `clean` (see BUILDING.md). |
| `tools/` | `apply.py` (incremental), `check.sh`, `test_cli.sh`, `rom.py`, `bps.py`, `gen_skyline.py`, `preview_skyline.py`, `check_stubs/` |
| `VERSION`, `CHANGELOG.md` | The patch version (names the `.bps`) and player-facing release notes. |
| `docs/design/` | Game design: story, world, cast, mechanics, masks, side missions, opening storyboard. |
| `docs/tech/` | This file and the custom-model pipeline. |

## Workflow

```bash
./majora-city build [ROM]    # first run: fetch decomp, check + install ROM, extract assets, build vanilla;
                             # every run: apply mod + patches, build, write dist/MajoraCity-v<VERSION>.bps/.zip/.z64
./majora-city update         # git pull, then build
tools/check.sh --ido                         # no ROM needed: data, patches, C checks, IDO compile
```

`build/mm` is a **managed workspace**. Every `apply.sh` run resets its tracked files to the pinned commit,
re-applies `patches/` and re-copies `mod/`, writing only files whose content changed so `make` stays incremental. Edit files in this repository, never in `build/mm`. Extracted assets,
the ROM and build output are untracked there and survive.

### Changing an engine file

1. Run `tools/apply.sh`, then edit the file inside `build/mm`.
2. Export the change: `git -C build/mm diff -- src/code/z_whatever.c > patches/00NN-short-name.patch`.
   If the file already has a patch, regenerate that patch instead of adding a second one.
3. Run `tools/check.sh` to confirm everything applies from scratch.

Keep engine patches **small and hook-shaped**: call into `mc_core.c` or an actor instead of writing gameplay
inside vanilla files. That keeps rebases onto newer decomp commits cheap.

## Engine hooks (current patches)

| Patch | What and why |
|---|---|
| `0001-register-actors` | Appends `Mc_Intro` (0x2B2) and `Mc_Skyline` (0x2B3) to the actor table. New actors always go at the end. |
| `0002-spec-segments` | Links `mc_core.o` into `code`; adds the `ovl_Mc_*` overlay segments. |
| `0003-save-data` | Replaces the unused 84-byte `SaveInfo.unk_DF4[0x54]` with `McSaveData mc`. The struct size is unchanged, so flash layout and checksums are unaffected. |
| `0004-sram-hooks` | `Sram_OpenSave`: files that never reached Clock Town start at `McCore_GetFreshFileEntrance()`. `Sram_SaveEndOfCycle`: calls `McCore_OnCycleReset()` (Song of Time). |
| `0005-play-init-hook` | `Play_Init`: calls `McCore_OnPlayInit()` once Player and the room's actors exist, and before entrance cutscenes start. |
| `0006-text-bank` | Includes `mc_message_data.h` into the message table (before the 0xFFFC/0xFFFD terminators). |
| `0007-makefile-text-dep` | Rebuilds the encoded text when the Majora City text bank changes. |

## Core module (`mc_core.c`)

- **Scene augmentation**: `sMcSceneSpawns[]` lists actors to spawn in vanilla scenes (scene, actor, params,
  condition). This is how Majora City adds content to existing areas without shipping or editing ROM-extracted
  scene data. New districts that need new geometry will be real new scenes (M10).
- **Story & cycle flags**: `MC_CHECK_STORY/MC_SET_STORY` (128 permanent flags) and `MC_CHECK_CYCLE/MC_SET_CYCLE`
  (64 flags cleared by the Song of Time).
- **Helpers**: `McCore_FindCityCenter` (locates the Clock Tower actor in the scene), `McCore_AddRespect`.

`mc_core.c` lives in the `code` segment, so it is always resident. Keep it small: gameplay belongs in
overlays, which are only loaded while in use.

## Save data (`McSaveData`, 0x54 bytes at `SaveInfo + 0xDF4`)

| Offset | Field | Purpose |
|---|---|---|
| 0x00 | `u32 storyFlags[4]` | 128 permanent story flags (`McStoryFlag`) |
| 0x10 | `u32 cycleFlags[2]` | 64 per-cycle flags (`McCycleFlag`), cleared by the Song of Time |
| 0x18 | `u32 tagsSprayed[2]` | 64 graffiti tags |
| 0x20 | `u32 stuntJumpsDone` | 32 Epona stunt jumps |
| 0x24 | `u32 rampagesDone` | 32 Masked Rampages |
| 0x28 | `s16 factionRep[8]` | Respect per `McFaction`, −1000…1000 |
| 0x38 | `u8 sideJobLevel[12]` | Progress per `McSideJob` |
| 0x44 | `u8 chapter` | `McChapter` |
| 0x45 | `u8 radioStation` | Last Ocarina Radio station |
| 0x46 | `u8 safehouseFlags` | Owned safehouses |
| 0x47 | `u8 businessFlags` | Owned businesses |
| 0x48 | `u8 reserved[0xC]` | Free |

`mc_core.c` contains a compile-time size check: the build fails if this struct ever stops being exactly 0x54
bytes. New files get it zeroed by vanilla's `bzero(&saveInfo)`; every save path writes it to flash with the
rest of `SaveInfo`.

## ID ranges

| Kind | Majora City range | Notes |
|---|---|---|
| Actor IDs | 0x2B2 and up | Appended after the last vanilla actor (`En_Rsn`, 0x2B1). |
| Text IDs | 0x4D00–0x4DFF | `check.sh` fails if extracted vanilla text ever uses this range. |
| Story flags | `McStoryFlag` | Never reorder; flags are stored by index in saves. Append only. |

## Adding a new actor (checklist)

1. Create `mod/src/overlays/actors/ovl_Mc_Name/z_mc_name.{c,h}` with an `ActorProfile Mc_Name_Profile`.
2. Append `DEFINE_ACTOR(Mc_Name, ACTOR_MC_NAME, ALLOCTYPE_NORMAL, "Mc_Name")` to `0001-register-actors.patch`.
3. Add its `ovl_Mc_Name` segment to `0002-spec-segments.patch`.
4. Spawn it from a scene (`sMcSceneSpawns[]`) or from another actor.
5. `tools/check.sh --ido`.

Write C89 that IDO accepts: declarations at the top of blocks and no designated initializers. `//` comments
are fine (the decomp compiles with `-Xcpluscomm`). `check.sh` enforces `-Wdeclaration-after-statement`.

## Verification levels

| Level | What it proves | Needs |
|---|---|---|
| `tools/check.sh` | Generated data is current; BPS round-trips; patches apply to the pinned commit; all Majora City C (and every patched engine file) type-checks against the real decomp headers; the text bank encodes and compiles | Nothing (no ROM) |
| `tools/check.sh --ido` | The same files compile with IDO 7.1, the compiler Nintendo used | Network once (downloads IDO recomp) |
| `tools/test_cli.sh` | The whole `./majora-city` flow (setup, rebuild, update, patch naming, bad ROMs) with a fake ROM and a stand-in for `make` | Nothing |
| `./majora-city build` | Full link, relocation and ROM build | Your ROM |
| Emulator / hardware | Behaviour, tuning, performance | Your ROM + Ares / EverDrive |

`tools/check_stubs/` provides minimal stand-ins for the few ROM-extracted headers the decomp's global headers
include, so the no-ROM check can run. They come last on the include path, so the real extracted headers always
win after the one-time setup.

## Budgets

| Resource | Budget | Current |
|---|---|---|
| Skyline, Termina Field | ≤ 600 triangles | 200 (10 towers) |
| Skyline, Old Town | ≤ 800 triangles | 540 (24 towers) |
| Skyline textures | 1 × 32×32 I8 resident per frame | 1 KB (day or night) |
| `code` segment growth | Keep `mc_core.c` under ~2 KB of code | Small helpers only |

## Updating the decomp pin

1. Change `DECOMP_COMMIT` in `decomp.lock`.
2. `tools/check.sh`. If a patch fails, re-create it against the new commit (see *Changing an engine file*).
3. Rebuild and smoke-test the opening in an emulator before merging.

## Legal

No ROM, extracted asset, or decompiled-but-Nintendo-authored *data* is committed here. Code under `mod/` and
`tools/` is original. Distribute only `dist/majora-city.bps`; players apply it to their own dump.
