# Majora City: Side Missions & Activities

Side content is where the GTA influence shows most. Every activity uses an engine system Majora's Mask already
has (schedules, minigame timers, the horse race code, the Postman's route, the shooting galleries), so each one
can be built in a bounded amount of work.

Legend: **Repeatable** jobs have levels (stored in `McSaveData.sideMissionLevel[]`); **One-shot** quests are
story-like.

## Repeatable city jobs

| Job | GTA analogue | How it plays | Unlock | Reward at max level |
|---|---|---|---|---|
| **Epona Cab** | Taxi | Pick up citizens waiting at hitching posts and ride them to their destination before the timer runs out. Fares scale with distance and with how much you scare them. | Get Epona back (Act I-8) | **Racer's Mask** (Epona never runs out of carrots) |
| **Night Watch** | Vigilante | Ride with the MCPD at night; Tatl calls in a "masked suspect" and you chase and subdue them. | Act I-6 | **Officer's Cap**: minor crimes don't raise Heat |
| **Fairy Medic** | Ambulance | Collect injured citizens (fairy-in-a-bottle) and heal them at a fountain on a timer. | Great Fairy (Act I-3) | Max magic regeneration |
| **Bucket Brigade** | Firefighter | Fires break out in the Old Town; put them out with bottled water / Zora bubbles. | Zora Mask | Fire-resistant tunic |
| **Postman's Route** | Courier (Vice City's pizza boy) | Timed letter deliveries across rooftops. | Act I-9 | **Postman's Hat** upgrade: sprint never tires |
| **Milk Run** | Trucking | Escort Cremia's milk cart along Milk Road; the Gorman Bros. ambush it. | Get Epona back | Chateau Romani, plus Respect with Romani Ranch |
| **Bounty Board** | Assassination contracts (toned down) | Wanted posters in MCPD booths: track down Garo ninjas, Gerudo couriers and Bombers rivals, and bring them in. | Night Watch level 3 | **Garo's Mask** upgrade (shadow step) |

## Racing & stunts

| Activity | Description |
|---|---|
| **Street Races** | Point-to-point races through the Outer Boroughs on Epona, on the Goron roll, or swimming as a Zora. Each borough has 3 races; win all 12 to earn the **Blast Mask** upgrade (cooldown removed). |
| **Epona Stunt Jumps** | 32 ramps (fences, crates, broken bridges) around the city. Hitting one triggers a slow-mo camera like a GTA unique stunt jump. Tracked in `McSaveData.stuntJumpsDone`. |
| **Goron Grand Prix** | Expanded vanilla Goron race, now a 5-race league. |
| **Bomber Bike Rally** | Deku-flower aerial checkpoint races over the rooftops. |

## Collectibles

| Collectible | Count | Reward |
|---|---|---|
| **Lost Fairies** (city-wide stray fairies) | 100 | Every 10 unlocks a "care package" at the Salesman's shop: rupees, then bombchus, then a heart piece. At 100, Fierce Deity free-roam (post-game). |
| **Tags** (graffiti spots, sprayed with the **Tagger's Mask**) | 64 | Bombers Respect, Bombers' clubhouse decorations, and a secret Bombers mission. |
| **Masked Rampages** | 32 | Glowing Majora-mask pickups that start a 60-second combat challenge ("defeat 15 ChuChus with the Goron punch"). |
| **Heart Pieces** | 52 (vanilla) | Some are moved to new city locations; the hint text calls them "investments". |

## Businesses (the "asset" system)

As in Vice City, Link can buy properties. Each one has an **unlock mission chain**, then generates rupees
**per cycle** (paid into the bank at the Dawn of the First Day), and some change the world.

| Business | Price | Mission chain | Effect |
|---|---|---|---|
| **Milk Bar** | 5,000 | "Last Call": book the Indigo-Go's for a sold-out show | +300/cycle; unlocks a Milk Bar radio playlist |
| **Trading Post** | 3,000 | "Inventory": stop a Gerudo Syndicate shakedown | +200/cycle; 10% shop discount everywhere |
| **Stock Pot Hotel** | 8,000 | "Room Service" (Kafei Case epilogue) | +500/cycle; a safehouse room you can save in |
| **Swordsman's Academy** | 2,500 | "Discipline": spar the Swordsman 3 times | +100/cycle; new sword-combo training |
| **Honey & Darling's Arcade** | 4,000 | "High Score": beat all 3 games' records in one cycle | +250/cycle; arcade minigames become free |
| **Romani Ranch Stables** | 6,000 | "Close the Impound": buy out the city's impound contract | Epona can never be impounded again |

Owned businesses are a bit field (`McSaveData.businessFlags`).

## Casino & minigames

- **Stock Pot Casino:** new card table (high/low) and slot machine minigames; the **Hustler's Mask** shows the
  next card.
- **Honey & Darling's Arcade:** vanilla treasure/bombchu/archery games, plus a new "Moon Defense" shooting game.
- **Milk Bar Fight Night:** Gorman's underground boxing ring. Fists only (Brawler's Mask), 5 opponents.
- **Tingle's Tabloid:** photograph celebrities (Mikau, the Mayor, Kafei in disguise) with the Pictograph Box
  for Tingle's gossip rag.

## One-shot side stories (selection)

| Quest | Summary |
|---|---|
| **Grandma's Stories, Remixed** | Anju's grandmother tells two new stories about the city "before the skyscrapers". |
| **The Ballad of Guru-Guru** | Help the street musician get his song on the radio. |
| **Kamaro's Dance-Off** | Dance battles on rooftops at midnight. |
| **Bombers' Big Score** | Help the Bombers pull an (adorable) heist on the Curiosity Shop. |
| **Lost & Found** | Return items stolen by Takkuri, the thieving bird, to their owners across all four boroughs. |
| **The Mayor's Secret** | Find out who really signed the Festival contract. |
