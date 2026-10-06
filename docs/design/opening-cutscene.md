# Opening Cutscene: "Highway to the City"

The first thing a player sees on a new file. Link rides Epona across Termina at dawn toward a skyline that
shouldn't exist: Clock Town, grown into a city of skyscrapers. This page is both the storyboard and the
implementation reference for milestone **M1**.

Implementation: [`mod/src/overlays/actors/ovl_Mc_Intro/z_mc_intro.c`](../../mod/src/overlays/actors/ovl_Mc_Intro/z_mc_intro.c)
(director) and [`ovl_Mc_Skyline`](../../mod/src/overlays/actors/ovl_Mc_Skyline/z_mc_skyline.c) (skyline).

## Storyboard

Frame numbers are game frames at 20 fps. Camera positions are relative to Epona, so the shots work wherever the
ride happens to pass.

| Shot | Frames | Camera | On screen | Audio |
|---|---|---|---|---|
| **1 · Horizon** | 0–79 | Low behind Epona (300 back, 60 up), aimed past Link at the skyline | Link and Epona silhouetted against dawn. Skyscrapers loom over the old Clock Town walls. Narration: *"Three days' ride from Hyrule, the old trade road turned to stone..."* | Termina Field theme, hooves |
| **2 · Tracking** | 80–169 | Alongside on Link's right (260 out, 70 up), leading slightly | Epona at full gallop; grass and fences streak past. Narration: *"...then to steel."* | |
| **3 · Hooves** | 170–219 | Ground level, front-left, aimed at Epona's legs | A low, fast shot of hooves throwing up dirt. The controller rumbles. | |
| **4 · Crane reveal** | 220–339 | Starts low in front of Link, then cranes up and back while turning toward the city. FOV opens from 60° to 75°. | The full skyline comes into view: dozens of Art Deco towers around the Clock Tower. **Title card: MAJORA CITY** (frame 240). | |
| **5 · Chase** | 340–arrival | Classic chase cam 360 back, 110 up | The walls grow closer; the skyscrapers fill the frame. | |
| **6 · Arrival** | arrival + 0–59 | Low in front of Epona, looking up | Epona rears at the South Gate with the Clock Tower behind. | Neigh |
| **7 · Fade** | arrival + 60 | — | Fade to white, then hand off (see below) | |

The ride ends when Epona reaches `MC_INTRO_GATE_RADIUS` (1400 units) from the Clock Tower. A stuck detector ends
the ride early if Epona hits an obstacle, and a hard cap (`MC_INTRO_RIDE_MAX_FRAMES`) means the cutscene can
never soft-lock.

## How it works

```
New file ─► Sram_OpenSave (patched) ─► entrance = ENTRANCE(TERMINA_FIELD, 1)   (from Road to Southern Swamp)
                                         │
Play_Init (patched) ─► McCore_OnPlayInit ─┤
                                         ├─► spawns Mc_Skyline (layout: Termina Field ring)
                                         └─► spawns Mc_Intro   (only if MC_STORY_INTRO_DONE is not set)

Mc_Intro:
  Init    spawn En_Horse(ENHORSE_PARAM_4000 | ENHORSE_9)   ← Epona in cutscene mode
          Player_MountHorse + Player_SetCameraHorseSetting ← the same calls vanilla makes for a mounted spawn
  Start   Cutscene_StartManual, Play_CreateSubCamera, neutral override input
  Ride    every frame: play->csCtx.playerCue = &this->cue
            cue.id 36 (gallop to cue.endPos)   → EnHorse_CsMoveToPoint
            cue.id 38 (rear up)                → EnHorse_CsRearing
          The camera director computes eye/at from Epona's position and yaw for each shot
  Title   Message_DisplaySceneTitleCard(play, MC_TEXT_TITLE_MAJORA_CITY)
  Exit    set MC_STORY_INTRO_DONE, fade to white, hand off to the next sequence
```

**Why "synthetic cues"?** A scripted cutscene would need hand-placed absolute coordinates inside Termina Field
scene data, which only exists in the player's ROM. Instead, the director feeds Epona the same actor-cue structure
a scripted cutscene would (`CsCmdActorCue`), but computes the waypoints at runtime: from Link's spawn point
toward the Clock Tower actor (`Obj_Tokeidai`), with floor raycasts for the height. The intro therefore runs on
an unmodified Termina Field scene.

## Hand-off (M1 vs M2)

`MC_INTRO_HANDOFF` in `mod/include/mc/mc.h` chooses what happens after the fade:

| Value | Destination | When |
|---|---|---|
| `MC_HANDOFF_VANILLA_PROLOGUE` *(M1 default)* | `ENTRANCE(CUTSCENE, 0)`, the vanilla Lost Woods prologue | Until the new Prologue missions exist. Keeps the game completable: Skull Kid, the Deku curse and the Clock Tower all still happen as in vanilla. |
| `MC_HANDOFF_SOUTH_GATE` *(M2)* | `ENTRANCE(SOUTH_CLOCK_TOWN, 0)`, followed by Prologue P2 "Impounded" | Once P2–P4 replace the vanilla prologue. |

## Tuning checklist (needs a real ROM + emulator)

These values are educated starting points. They need tuning in-game:

- [ ] `MC_INTRO_GATE_RADIUS`: Epona should stop just outside the South Gate.
- [ ] Shot offsets (`sShots[]`): no camera clipping through the walls or trees on the ride line.
- [ ] Skyline ring radii and heights (`tools/gen_skyline.py`): towers must clear the walls from the field but
      never poke through the walls when seen from inside the Old Town.
- [ ] Confirm `ENTRANCE(TERMINA_FIELD, 1)` is the Road to Southern Swamp spawn on US 1.0 (community entrance
      tables say yes; spawn 10 = telescope and 12 = moon crash are confirmed in the decomp source).
- [ ] Narration text timing.
- [ ] No scene entrance cutscene plays at this spawn. If one does, its end (`CS_STATE_STOP`) switches Epona out of
      cutscene mode before the ride starts, and she would ignore the director's cues.
