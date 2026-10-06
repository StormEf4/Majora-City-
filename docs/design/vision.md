# Majora City: Vision & Design Pillars

> *"You've met with a terrible fate, haven't you? ...Welcome to the big city, kid."*

## The pitch

**Majora City** is a total-conversion ROM hack of *The Legend of Zelda: Majora's Mask* (N64, US 1.0).
Majora's Mask has warped Termina. Clock Town is now a sprawling metropolis, still recognisable at its core,
with a skyline of Art Deco skyscrapers, neon signs, freeways and boroughs that push out into what used to be
Termina Field. The game plays like a Zelda adventure crossed with *GTA III* and *Vice City*. You get an open
city, a crime-drama story told through missions, a Heat system, side jobs, businesses to buy, a radio, and
you get around on Epona.

The moon still hangs over the skyline, and the three-day clock still ticks.

## Design pillars

1. **Clock Town, but massive.** Every district is a remix of a place players already know. The Clock Tower is
   still at the centre, now the tallest skyscraper in the city. South Clock Town is Downtown, the Laundry Pool
   is the Canal District, and Stone Tower becomes an upside-down financial tower. Familiar landmarks keep
   players oriented in a much larger space.
2. **Masks are identity.** In GTA you change clothes or respray your car to lose the cops. Here, *you change
   your face*. Masks double as disguises, Heat breakers, faction passes and gameplay tools. This is the hack's
   signature mechanic.
3. **The 72-hour heartbeat stays.** The three-day cycle and the NPC schedule system are Majora's Mask's soul,
   and they suit a living city well: shops open and close, gangs move around, and timed heists happen at
   specific hours. The Song of Time is the city's "wasted/busted" safety net and its long-game reset.
4. **Crime-drama tone, Zelda heart.** The story is pulpy, funny and occasionally dark, in the vein of a Vice City
   radio ad or a GTA III cutscene. It never becomes cruel. Link is still a hero; the city's underworld is a
   symptom of the mask's corruption, and the finale is about un-warping Termina.
5. **N64-honest.** Everything must run on real hardware and accurate emulators (Ares, Mupen64Plus with
   accurate RDP, Project64 with GLideN64 as a secondary target). That means budgeted polygon counts,
   streaming-friendly room splits, and new mechanics built on engine systems that already exist (schedules,
   cutscenes, actor cues, the horse and minigame frameworks).

## What "GTA-like" means here (and what it doesn't)

| GTA III / Vice City element | Majora City translation |
|---|---|
| Stealing cars | Commandeering Epona, carriages, Goron rolling, Zora jet-swimming, plus later "jackable" mounts and carts |
| Wanted stars | **Heat**: 0–5 Majora masks on the HUD; the MCPD (the Clock Town Guard reimagined) escalates its response |
| Pay 'n' Spray | Swapping to an unseen mask, or a visit to the **Mask Shop back room** |
| Radio stations | **Ocarina Radio**: stations you cycle while riding, built from the existing soundtrack and new sequences |
| Payphone missions | **Gossip Stone** payphones and **Tatl's call-ins** |
| Hidden packages | **Lost Fairies**, 100 hidden across the city |
| Unique stunt jumps | **Epona stunt jumps** with slow-motion camera |
| Rampages | **Masked Rampages**: timed combat challenges |
| Taxi / Vigilante / Ambulance / Firefighter | **Epona Cab / Night Watch / Fairy Medic / Bucket Brigade** |
| Property & assets | Buy the **Milk Bar, Trading Post, Stock Pot Inn**, and more for income and new missions |
| Gunplay | Bow, hookshot, bombs and new lock-on brawling; no firearms (keeps it Zelda) |

What we **won't** do: no random civilian killing as a goal (attacking citizens raises Heat and Link stumbles
or gets knocked back, as in vanilla), no firearms, and no content that breaks the T-for-Teen spirit of the
original.

## Audience & scope

- Players who know Majora's Mask well and want a new, long campaign (target: 20–30 hours).
- Distributed only as a **BPS patch** applied to the player's own legally-dumped US ROM. No Nintendo assets live
  in this repository.
- Built on the [zeldaret/mm](https://github.com/zeldaret/mm) decompilation, so the hack is C source and can be
  ported later to N64Recomp-style PC builds.

See [`../../ROADMAP.md`](../../ROADMAP.md) for the phased production plan.
