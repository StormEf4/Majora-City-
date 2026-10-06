# Majora City: Core Mechanics

Every mechanic below says which **existing engine systems** it builds on. The decomp gives us the source of all
of them; the cheapest path is always to extend what Majora's Mask already does.

## 1. Heat (wanted level)

The HUD shows 0–5 small Majora masks under the clock.

| Level | Trigger examples | Response |
|---|---|---|
| 1 | Breaking shop pots, hitting a citizen, riding Epona on Old Town sidewalks | One MCPD officer on foot chases you |
| 2 | Attacking an officer, stealing from a stall | 3 officers with spears; gates of the current district close |
| 3 | Assaulting multiple officers, robbing the bank | **Garo ninjas** join the hunt |
| 4 | Destroying property during a heist, fighting at City Hall | **Iron Knuckle riot squad** in the Old Town |
| 5 | Story-only (Majora Corp infiltration) | Wizzrobe "searchlights" sweep from the rooftops |

**Losing Heat:**
- Break line of sight for a time that scales with level.
- **Change masks out of sight.** Witnesses remember a *face*: if you swap to a mask MCPD hasn't seen during this
  pursuit, Heat drops by 2 levels. This is the signature mechanic.
- Visit the **Mask Shop back room** (Pay 'n' Spray), which clears Heat for 100 rupees.
- Play the **Song of Time**, which clears Heat (the city forgets).

**Getting busted:** if an officer catches you while you're stunned, you wake up in the MCPD booth minus 20% of
your carried rupees, and you lose any item picked up during the pursuit.

**Engine basis:** a global `McHeat` state in the code segment (`mc_core.c`); officers reuse the Clock Town
guard actor (`En_Stop_heishi`), Garo (`En_Jso`), and Iron Knuckle (`En_Ik`) with new AI params. The HUD
element is drawn in `z_parameter.c` beside the clock.

## 2. Getting around

| Mode | Built on | Notes |
|---|---|---|
| **Epona** | `En_Horse` | The hack's car. Call her anywhere outdoors with Epona's Song once she's out of the impound. New: Epona can enter the *Old Town* streets (wider gates in remodelled scenes). |
| **Goron roll** | Player Goron form | The motorbike: fastest on roads, can't swim. |
| **Zora swim** | Player Zora form | The jet-ski for the canals and bay. |
| **Deku flight** | Player Deku form | Rooftop traversal via Deku flowers; Phase 3 adds the Deku Copter upgrade (sustained flight). |
| **Carriages & carts** | `En_Horse` donkey/bandit variants, `Obj_Um` (Cremia's cart) | Phase 3: commandeer the Gorman Bros. wagon, the milk cart and city carriages. |
| **Hookshot ziplines** | Hookshot targets | Rooftop wire lines between skyscrapers. |
| **Owl Statues → Subway** | Owl warp | Fast travel, presented as subway stations. |

## 3. Ocarina Radio

While riding Epona or rolling as a Goron, **press L** to cycle stations. Each station is a playlist of existing
sequences (and later, new ones), with short **talk segments** shown as non-blocking text.

| Station | Format | Content |
|---|---|---|
| **K-ZORA 105** | Rock | Indigo-Go's tracks, Zora Hall themes |
| **Deku Beats** | World / chill | Deku Palace, Woodfall, the swamp themes |
| **Goron Gospel** | Drums & brass | Goron Village, Goron race, Snowhead |
| **Ikana After Dark** | Lounge / spooky | Ikana Castle, the music box house, Sharp's Curse |
| **Gorman Circus FM** | Show tunes | Gorman troupe, Milk Bar, the Carnival of Time |
| **Pirate FM** *(unlocked)* | Pirate radio | Gerudo fortress themes, plus Tael's cryptic broadcasts |
| **Guru-Guru Late Show** *(talk)* | Talk radio | Anju's advice, Majora Corp ads, Tingle's gossip, Mayor's speeches |

**Engine basis:** `SEQ_PLAYER_BGM_MAIN` sequence switching through `Audio_*` / `SEQCMD_*`; the station choice
is saved in `McSaveData.radioStation`. No new audio is needed for the first version.

## 4. Missions, contacts & the Job Book

- The **Bombers' Notebook becomes the Job Book**. Vanilla already tracks people, schedules and events, so we
  add Majora City contacts and missions to its tables (`src/code/z_play_hireso.c`).
- **Mission markers:** blips on the minimap; Gossip Stones work as **payphones** that start missions.
- **Tatl calls:** non-blocking messages (as with vanilla's Tatl C-Up hints) for mission briefings.
- **Mission failure:** "Mission failed!" text and a retry from the contact. No lost cycle time beyond what was
  spent.

## 5. Money

- Max wallet raised to **9,999** (Giant's Wallet+1, the "Kingpin Wallet").
- The **Bank of Termina** persists across cycles (vanilla) and receives **business income** each Dawn of the
  First Day.
- Rupee sinks: businesses, the Mask Shop back room, bribes (pay off an officer at Heat 1), Epona impound fees,
  casino.

## 6. Combat additions

- **Brawling:** unarmed lock-on punch combos in human form, with Goron-strength punches when wearing the
  Brawler's Mask.
- **Takedowns:** a quiet B-press behind an unaware enemy (Garo, guards) knocks them out.
- **Over-the-shoulder aim** for the bow and hookshot (the camera-setting change already exists for the bow).

## 7. Safehouses & saving

Vanilla Owl Statues and Song of Time saves remain. Safehouses (Stock Pot Hotel room, Romani barn, a Zora
Hall apartment, Kafei's office) add:
- a full save (not just an owl save),
- a wardrobe (tunic colours, Phase 4),
- an Epona hitching post (she's always parked outside).

## 8. Time & world state

- The three-day clock stays. Default time speed is the vanilla speed; the Inverted Song of Time still slows it.
- New **city-wide events** on the schedule: the Majora Corp parade (Day 2, 13:00), the blackout (Night 2) and
  the final-hours looting (Night 3).
- Every NPC added to the city uses the **schedule scripting language** the decomp already documents
  (`docs/schedule_scripting_language.md` upstream).
