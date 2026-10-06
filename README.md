# Majora City

**A total-conversion ROM hack of *The Legend of Zelda: Majora's Mask* (N64, US 1.0).**
Majora's Mask has warped Termina into a sprawling neon metropolis. Clock Town is now a downtown of Art Deco
skyscrapers, and the game plays like a Zelda adventure crossed with *GTA III* and *Vice City*. You get an open
city, a crime-drama story told through missions, a Heat system, side jobs, businesses to buy, a radio, and
Epona as your ride. The moon still hangs over the skyline, and you still have 72 hours.

| The skyline from Termina Field at dawn | …and at night | From South Clock Town |
|---|---|---|
| ![Skyline at dawn](docs/images/skyline_field_dawn.png) | ![Skyline at night](docs/images/skyline_field_night.png) | ![Skyline from town](docs/images/skyline_town_day.png) |

<sub>Software renders of the real generated display lists (`tools/preview_skyline.py`). The grey walls and Clock
Tower are stand-ins; in-game they come from your ROM.</sub>

## Status

**Milestone M1: "Highway to the City" (code complete, needs in-game tuning).** A new file opens on a brand-new
cutscene: Link gallops on Epona across Termina at dawn toward a skyline of skyscrapers rising over the old Clock
Town walls, under a **MAJORA CITY** title card. See the [storyboard](docs/design/opening-cutscene.md).

What's in place:
- The opening director (`Mc_Intro`): Epona ride, a 7-shot camera sequence, narration, a title card, START to
  skip, and a stuck-proof ride that can't soft-lock
- The procedural skyline (`Mc_Skyline`): generated towers, no Nintendo assets, tinted for day, dusk and night,
  with lit windows after dark
- Engine hooks, a Majora City save block that keeps the vanilla save size, a text bank, and the build and patch
  tooling

All Majora City C code compiles with the original N64 compiler (IDO 7.1) and type-checks against the
decompilation's headers. Nothing has been run on a real ROM yet. Tuning values such as camera offsets and the
gate radius need an emulator pass, and the checklist is in the storyboard doc. Full plan:
**[ROADMAP.md](ROADMAP.md)**.

## Design

| Doc | What's in it |
|---|---|
| [Vision & pillars](docs/design/vision.md) | The pitch and how "GTA-like" translates to Zelda |
| [Story bible](docs/design/story.md) | Prologue, Acts I–III, every main mission, the ending |
| [World & districts](docs/design/world.md) | Downtown, Westside, Hotel Row, the four boroughs |
| [Cast & factions](docs/design/characters.md) | Who everyone is in the city, the 8 factions and Respect |
| [Mechanics](docs/design/mechanics.md) | Heat, getting around, Ocarina Radio, the Job Book, money, combat |
| [Masks & abilities](docs/design/masks-and-abilities.md) | 15 new masks, transformation upgrades, new moves |
| [Side missions](docs/design/side-missions.md) | City jobs, races, collectibles, businesses, casino |
| [Opening cutscene](docs/design/opening-cutscene.md) | Shot-by-shot storyboard and how it's implemented |
| [Architecture](docs/tech/architecture.md) | How the hack is built on the decomp, hooks, save layout, ID ranges |
| [Custom models](docs/tech/custom-models.md) | Procedural and Blender/Fast64 pipelines, budgets, style |

## Playing it

Patches are named **`MajoraCity-vX.Y.Z.bps`**. You need your own dump of *Majora's Mask* (USA, N64) in `.z64`,
`.n64` or `.v64` format. The easiest way is [Rom Patcher JS](https://www.marcrobledo.com/RomPatcher.js/) in a
browser. [Flips](https://github.com/Alcaro/Flips) or `./majora-city patch your-rom.z64 MajoraCity-vX.Y.Z.bps`
work too. Play on an accurate emulator (Ares recommended) or real hardware with an Expansion Pak.

## Building the patch

One command, on Linux, Windows (via WSL: double-click `majora-city.cmd`) or macOS:

```bash
git clone https://github.com/StormEf4/Majora-City-.git && cd Majora-City-
cp "/path/to/Majora's Mask (USA).z64" rom/      # or give the path to the command, or drag it in when asked
./majora-city build
```

It checks your computer (and offers to install missing tools), checks your ROM is the right one, does the one-time
setup, builds, and writes:

```
dist/MajoraCity-v0.1.0.bps   the patch
dist/MajoraCity-v0.1.0.zip   patch + how-to-play + changelog, ready to share
dist/MajoraCity-v0.1.0.z64   your playable ROM (don't share it)
```

**Every update after that:** `./majora-city update`, which pulls the latest changes and builds the new patch.
Full step-by-step guide per OS and troubleshooting: **[BUILDING.md](BUILDING.md)**.

Contributors without a ROM can still verify their changes:

```bash
tools/check.sh --ido   # generated data, BPS self-test, patches apply, C checks against the decomp, IDO compile
```

## Repository layout

```
mod/            new files, laid out as they go into the decomp tree
  include/mc/                     core API and the save block
  src/code/mc/mc_core.c           story flags, per-scene spawns, hooks
  src/overlays/actors/ovl_Mc_Intro/    opening cutscene director
  src/overlays/actors/ovl_Mc_Skyline/  procedural skyline (+ generated data)
  assets/text/mc_message_data.h   Majora City text bank
patches/        small diffs to decomp files (actor table, spec, save layout, hooks, text)
majora-city     the one-command builder (majora-city.cmd on Windows)
rom/            put your ROM here (never committed)
tools/          apply, check, test_cli, rom.py, bps.py, gen_skyline.py, preview_skyline.py
VERSION         patch version; CHANGELOG.md says what changed
docs/           design and technical docs
decomp.lock     the zeldaret/mm commit we build against
```

## Legal

This repository contains **no ROM, no Nintendo assets and no extracted game data**. It contains original code and
documents plus small patches to the [zeldaret/mm](https://github.com/zeldaret/mm) decompilation, which you
build with your own legally obtained copy of the game. *The Legend of Zelda* and *Majora's Mask* are trademarks
of Nintendo. This is a non-commercial fan project and is not affiliated with Nintendo, Rockstar Games or the
ZeldaRET team.
