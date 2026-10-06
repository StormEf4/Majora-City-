# Majora City: Cast & Factions

Every character keeps their vanilla face, name and core personality. The city only changes their *job*.

## Principal cast

| Character | Majora City role | Notes |
|---|---|---|
| **Link** | "The kid from out of town" | Silent protagonist. Starts broke, horseless and cursed. |
| **Tatl** | Partner, navigator, the voice of the game | Explains mechanics, calls with mission tips (the hack's "phone"), and roasts Link constantly. |
| **Tael** | Tatl's brother, still with the Skull Kid | His cryptic radio broadcasts ("Swamp... Mountain... Ocean... Canyon...") point to the four bosses. |
| **The Salesman** (Happy Mask Salesman) | Link's first contact | Runs a mask shop that fronts a "mask recovery" business. Unsettling, polite, always knows the time. |
| **The Skull Kid** | Masked anarchist, face of the chaos | Leads a crew of street punks; Majora is the real power. |
| **Majora** | The mask behind Majora Corp | Never seen in person until Act III. Speaks through billboards, radio ads and contracts. |

## Downtown

| Character | Role |
|---|---|
| **Mayor Dotour** | Mayor; spineless, caught between the guard and Majora Corp's festival money |
| **Madame Aroma** | Socialite and the Mayor's wife; owns the Milk Bar; hires Link to find Kafei |
| **Captain Viscen** | Captain of the **MCPD** (Majora City Police Department, formerly the Clock Town Guard) |
| **Mutoh** | Construction magnate building the Festival stage and half the skyline |
| **Kafei** | Masked private eye on the Majora Corp case |
| **Anju** | Manages the Stock Pot Hotel & Casino |
| **Sakon** | The city's biggest fence, operating out of a hidden warehouse in Ikana |
| **Jim & the Bombers** | Kids' gang and informant network; their notebook becomes the Job Book |
| **Guru-Guru** | Street musician; hosts the *Guru-Guru Late Show* on Ocarina Radio |
| **Tingle** | Paparazzo and map seller who runs a gossip tabloid from his balloon |
| **The Postman** | Delivery company of one; hires Link for timed routes |
| **Honey & Darling** | Run the arcade on Hotel Row |
| **Toto & Gorman** | Gorman's traveling troupe performs at the Milk Bar; Toto manages the band bookings |

## Regions

| Character | Region | Role |
|---|---|---|
| **Koume & Kotake** | Woodfall Bayou | Airboat tours and a potion shop; bicker on the radio |
| **Deku King / Deku Butler** | Woodfall Bayou | CEO and COO of the Deku Trading Company |
| **Odolwa** | Woodfall Bayou | **Boss**, the Bayou Kingpin |
| **Darmani** (ghost) | Snowhead Heights | Late leader of the Rolling Thunder Goron biker gang |
| **Goron Elder & son** | Snowhead Heights | Union boss and his very loud kid |
| **Goht** | Snowhead Heights | **Boss**, a war machine built in the foundry |
| **Mikau, Lulu, Japas, Evan, Tijo** | Great Bay Beach | The Indigo-Go's, the hottest band in the city |
| **Aveil** | Great Bay Beach | Leader of the Gerudo Syndicate smuggling ring |
| **Gyorg** | Great Bay Beach | **Boss**, the thing in the bay |
| **Sharp & Flat** | Old Ikana | Ghost brothers: a casino owner and a record producer |
| **Pamela & her father** | Old Ikana | Living with a half-Gibdo dad in the music box house |
| **Igos du Ikana** | Old Ikana | Undead old-money king of the canyon |
| **Captain Keeta** | Old Ikana | Runs protection in the graveyard |
| **Twinmold** | Old Ikana | **Boss**, two possessed subway trains |
| **Cremia & Romani** | Romani Ranch | Milk trucking business, plus the impound lot they were forced to host |
| **Gorman Brothers** | Milk Road | Rival trucking outfit bootlegging "Chateau Romani" |

## Factions (Respect system)

Respect ranges from -1000 to 1000 per faction and persists across cycles. It unlocks prices, missions,
safehouses and backup.

| ID | Faction | Turf | You gain Respect by... | You lose Respect by... |
|---|---|---|---|---|
| 0 | **MCPD** | Downtown | Night Watch jobs, returning stolen goods | Heat, attacking officers |
| 1 | **The Bombers** | Northside | Bombers' Code, finding tags | Snitching to MCPD in certain missions |
| 2 | **Deku Trading Co.** | Woodfall Bayou | Deliveries, freeing the swamp | Siding with Koume & Kotake in their pricing war |
| 3 | **Goron Steelworkers' Union** | Snowhead Heights | The strike, racing | Crossing the picket line |
| 4 | **Indigo-Go's & Zora Guild** | Great Bay Beach | Gigs, the Egg Run | Selling bootleg tapes |
| 5 | **Gerudo Syndicate** | Great Bay docks | Smuggling side jobs | The Egg Run (unavoidable) |
| 6 | **Ikana Old Money** | Old Ikana | Casino jobs, healing the dead | Robbing the casino |
| 7 | **Gorman Bros. Trucking** | Milk Road | Escort and bootleg runs | Helping Cremia's milk run |

Faction IDs match `McFaction` in `mod/include/mc/mc.h` and the `factionRep[]` array in the save data.
