# Majora City: Masks & Abilities

Masks are identity. Every new mask has a **street use** (how it works in the open city) and, where
relevant, a **Heat interaction**. All 24 vanilla masks stay; some get upgrades.

## New masks

| # | Mask | How you get it | Street use | Heat interaction |
|---|---|---|---|---|
| 1 | **Officer's Cap** | Night Watch, level 10 | MCPD ignores Heat-1 crimes; opens the MCPD armory | Wearing it during a pursuit *raises* Heat by 1 (impersonating an officer) |
| 2 | **Getaway Mask** | Kafei Case, part 2 | Heat decays twice as fast; Link sprints 15% faster | Counts as an "unseen face" for the mask-swap trick |
| 3 | **Neon Mask** | Milk Bar business chain | Glows at night: lights alleys and dazzles enemies with a Deku-nut style flash on Z | None |
| 4 | **Broker's Mask** | Trading Post business | 25% discount at shops and a better bank interest rate | None |
| 5 | **Hustler's Mask** | Stock Pot Casino | Shows the next card at high/low; better odds at the slots | Casino security notices after 3 big wins (Heat 1) |
| 6 | **Racer's Mask** | Epona Cab, max level | Infinite Epona carrots; race checkpoints give bonus time | None |
| 7 | **Tagger's Mask** | Bombers' Code | Spray tags at 64 tag spots (collectible) | Spraying in view of MCPD gives Heat 1 |
| 8 | **Paparazzi Mask** | Tingle's Tabloid | Pictograph Box zoom ×2; photo-ops for Tingle | None |
| 9 | **Ghost Mask** | Old Ikana: "Captain's Orders" | Standing still for 2 seconds makes Link invisible to guards and cameras | Pausing out of sight halves Heat search time |
| 10 | **Brawler's Mask** | Milk Bar Fight Night | Goron-strength punches in human form; 3-hit combo plus uppercut | None |
| 11 | **Medic's Mask** | Fairy Medic, max level | Heals nearby citizens; Fairy Medic jobs pay double | None |
| 12 | **DJ Mask** | The Ballad of Guru-Guru | Choose any radio station on foot; plays a buff song (faster magic regeneration) | None |
| 13 | **Hawk Mask** | Rooftop races (Bomber Bike Rally) | Longer jumps between rooftops and grab ledges further away | None |
| 14 | **Smuggler's Mask** | Gerudo Syndicate side jobs | Disguise in Syndicate territory (like the vanilla Stone Mask, but only for Gerudo) | Counts as an unseen face |
| 15 | **Kingpin's Mask** | 100% city completion | Call Bombers backup (up to 3 kids who distract enemies); +1 max Heat ignore | Heat never exceeds 3 |

## Transformation masks: city roles

| Mask | Vanilla | City role and upgrades |
|---|---|---|
| **Deku Mask** | Bubble shots, flower launch | Rooftop courier. *Deku Copter* upgrade (Woodfall Bayou) gives 5 seconds of powered flight |
| **Goron Mask** | Roll, punch, pound | The motorbike. *Nitro Roll* upgrade (Snowhead Grand Prix) builds spikes faster and adds a boost button |
| **Zora Mask** | Swim, boomerang fins, barrier | The jet-ski. *Wake Jump* upgrade (Great Bay) launches out of the water onto piers |
| **Fierce Deity's Mask** | Moon only | Post-game free roam at 100 Lost Fairies |

## Vanilla mask changes

| Mask | Change |
|---|---|
| **Bunny Hood** | Also increases Epona's top speed by 10% while riding. |
| **Stone Mask** | Also makes MCPD stop pursuing at Heat ≤ 2 if you stand still. |
| **Captain's Hat** | Skeleton gangs in Ikana respect you, and the Gerudo Syndicate gives you a wide berth. |
| **Kafei's Mask** | Starts the Kafei Case noir chain. |
| **Postman's Hat** | Opens mailboxes for rupees (vanilla), and Postman's Route jobs pay more. |
| **Bremen Mask** | Lead citizens in a parade to block MCPD pursuers (Heat escape tool). |
| **Blast Mask** | Cooldown removed after the street-race reward. |
| **Mask of Truth** | Shows the next mission marker for gangs and spies. |

## New abilities (not mask-bound)

| Ability | Unlock | Description | Engine notes |
|---|---|---|---|
| **Sprint** | Start | Hold R+A (no shield): 1.4× run speed, drains a stamina ring around the magic meter | `Player` speed scaling plus a new HUD meter |
| **Ledge vault** | Start | Auto-mantle low walls and city railings | Uses existing ledge climb actions with a lower height threshold |
| **Epona's Whistle** | Act I-8 | Epona's Song calls her to the nearest road node, even in the Old Town | Extend `Horse_IsValidSpawn` and the scene list |
| **Takedown** | Act I-6 | B behind an unaware humanoid enemy knocks them out | Enemy stun state plus a new player action |
| **Brawl lock-on** | Act I-6 | Unarmed punches when no sword is equipped (or with the Brawler's Mask) | New player action reusing Goron punch hit logic |
| **Hookshot zipline** | Great Bay | Hookshot onto wire anchors and slide between rooftops | New `Mc_Zipline` actor using hookshot target flags |
| **Quick-mask wheel** | Act I-5 | Hold D-pad Up for a radial menu of 8 masks | Kaleido-style overlay; the vanilla 3 C-buttons stay |

## Mask-swap Heat rule (reference implementation)

```
on mask change, while Heat > 0 and no MCPD officer has line of sight:
    if mask not in pursuit.seenMasks:
        heat = max(0, heat - 2)
        pursuit.seenMasks += mask
```
Wearing **no mask** counts as Link's own face, which is always "seen" after the first crime of a pursuit.
