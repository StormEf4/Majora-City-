# Majora City: World & Districts

Majora City is laid out like vanilla Termina at a much larger scale. The old Clock Town walls still stand as a
ring of historic districts ("the Old Town"), skyscrapers rise inside and behind them, and Termina Field becomes
the **Outer Boroughs**, a ring of roads and suburbs leading to the four regions.

```
                         SNOWHEAD HEIGHTS
                       (steel town, ski roads)
                                 |
                          Northside Park
                                 |
   GREAT BAY BEACH --- Westside --+-- CLOCK TOWER --+-- Eastside --- OLD IKANA
   (Vice Beach, docks)  Market    |   (Downtown)    |   Hotel Row   (casinos, Stone Tower)
                                  |                 |
                            Downtown / Canal District
                                 |
                       Termina Freeway (south)
                                 |
                          WOODFALL BAYOU
                      (swamp, airboats, Deku)
                                 |
                       Romani Ranch & Impound
                       (south-west, via Milk Road)
```

## The Old Town (inside the walls)

| District | Vanilla source | Majora City identity | Key locations |
|---|---|---|---|
| **Downtown** | South Clock Town | The heart of the city. Clock Tower Plaza, Festival of Time stage, MCPD booth, taxi rank (Epona Cab) | Clock Tower skyscraper (Majora Corp HQ), Salesman's mask shop, the South Gate toll checkpoint |
| **Canal District** | Laundry Pool | Narrow canals, nightlife, back alleys | Guru-Guru's busking spot, Kafei's hideout and office, a Curiosity Shop back entrance |
| **Westside Market** | West Clock Town | Shopping strip, banks, pawn shops | Bank of Termina (persistent savings), Curiosity Shop (fence), Trading Post, Boom-Nation bomb shop, Swordsman's Academy |
| **Eastside / Hotel Row** | East Clock Town | Glitz and vice | Stock Pot Hotel & Casino, Milk Bar (nightclub), City Hall (Mayor's office), Honey & Darling's Arcade, the Observatory |
| **Northside Park** | North Clock Town | Green space, kids' turf | Great Fairy fountain, Bombers' clubhouse, Deku Playground, Tingle's tabloid kiosk |

## The Skyline

The skyscrapers are what most clearly separate Majora City from vanilla Clock Town.

- **Phase 1 (implemented in M1):** a procedural skyline. Code-generated Art Deco towers (no Nintendo assets)
  ring the Clock Tower. From Termina Field they rise above the old walls; from inside the Old Town they stand
  outside the walls like a modern downtown. See `mod/src/overlays/actors/ovl_Mc_Skyline`.
- **Phase 2:** hand-built landmark towers (Blender + Fast64) with interiors for missions: the Clock Tower
  skyscraper, the Stock Pot Hotel tower, City Hall annex, Majora Corp HQ floors.
- **Phase 3:** new walkable districts beyond the walls, built as new scenes with streaming rooms.

## The Outer Boroughs (Termina Field)

Termina Field is repainted as freeway and suburbs:

- **Termina Freeway**: paved roads radiating from each city gate (the four roads of vanilla Termina Field
  become the four highways). Carriage traffic and Gorman Bros. trucks run on them.
- **Billboards** for Majora Corp, Chateau Romani, the Indigo-Go's tour and Honey & Darling.
- **Gas station → Stable stop**: carrot and hay vendors that refill Epona's dash carrots.
- The **Observatory** becomes a radio tower, home of the Ocarina Radio network.
- Grotto entrances become **subway stations** (fast travel between Owl Statues, Phase 3).

## The Four Regions

| Region | Vanilla | Majora City | Vibe reference |
|---|---|---|---|
| **Woodfall Bayou** | Southern Swamp, Deku Palace, Woodfall | Airboat tours, stilt shacks, a palace that is now a trading company HQ | Vice City's Everglades |
| **Snowhead Heights** | Mountain Village, Goron Village, Snowhead | Foundries, union halls, icy switchback roads | Industrial Liberty City |
| **Great Bay Beach** | Great Bay Coast, Zora Hall, Pirates' Fortress | Beach hotels, rock venue, docks run by the Gerudo Syndicate | Ocean Beach, Vice City |
| **Old Ikana** | Ikana Canyon, Graveyard, Stone Tower | Haunted casinos, old money, the inverted skyscraper | Las Venturas meets a ghost town |
| **Romani Ranch & Impound** | Romani Ranch, Milk Road | Ranch plus the city's vehicle impound lot; Gorman Bros. Trucking next door | Countryside / truck stop |

## Day, night & the 72 hours

- **Day:** markets are open and traffic is heavy; MCPD patrols on foot.
- **Night:** neon lights up the skyline (Phase 2 lighting work), nightclubs open, gangs move, and Heat
  responses escalate faster.
- **Final hours:** the city panics. Traffic jams, looting (Heat-free crimes!) and evacuation convoys run in
  the outer boroughs.
