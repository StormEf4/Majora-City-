#ifndef MC_MC_H
#define MC_MC_H

/**
 * Majora City core API.
 *
 * Everything that is shared between Majora City actors and the patched engine files lives here: story flags,
 * the save accessors, the text IDs, and the hooks called from Play_Init / Sram.
 * Design reference: docs/tech/architecture.md
 */

#include "ultra64.h"
#include "z64math.h"
#include "mc/mc_save.h"

struct PlayState;

/* ---------------------------------------------------------------------------------------------------------------
 * Story & cycle flags
 * ------------------------------------------------------------------------------------------------------------- */

typedef enum McStoryFlag {
    /* 0x00 */ MC_STORY_INTRO_DONE,       // Watched "Highway to the City"
    /* 0x01 */ MC_STORY_EPONA_IMPOUNDED,  // Prologue P2
    /* 0x02 */ MC_STORY_MUGGED,           // Prologue P3
    /* 0x03 */ MC_STORY_MET_SALESMAN,     // Prologue P4
    /* 0x04 */ MC_STORY_EPONA_RECOVERED,  // Act I-8 "Grand Theft Epona"
    /* 0x05 */ MC_STORY_JOB_BOOK,         // Act I-2 "Bombers' Code"
    /* 0x06 */ MC_STORY_MET_VISCEN,       // Act I-6 "Night Watch"
    /* 0x07 */ MC_STORY_CITY_HALL,        // Act I-10, opens the boroughs
    /* 0x80 */ MC_STORY_MAX = MC_STORY_FLAG_WORDS * 32
} McStoryFlag;

typedef enum McCycleFlag {
    /* 0x00 */ MC_CYCLE_SKYLINE_SEEN, // First time the skyline was shown this cycle (used for Tatl comments)
    /* 0x40 */ MC_CYCLE_MAX = MC_CYCLE_FLAG_WORDS * 32
} McCycleFlag;

typedef enum McFaction {
    /* 0 */ MC_FACTION_MCPD,
    /* 1 */ MC_FACTION_BOMBERS,
    /* 2 */ MC_FACTION_DEKU_TRADING,
    /* 3 */ MC_FACTION_GORON_UNION,
    /* 4 */ MC_FACTION_ZORA_GUILD,
    /* 5 */ MC_FACTION_GERUDO_SYNDICATE,
    /* 6 */ MC_FACTION_IKANA_OLD_MONEY,
    /* 7 */ MC_FACTION_GORMAN_TRUCKING,
    /* 8 */ MC_FACTION_MAX
} McFaction;

typedef enum McSideJob {
    /*  0 */ MC_JOB_EPONA_CAB,
    /*  1 */ MC_JOB_NIGHT_WATCH,
    /*  2 */ MC_JOB_FAIRY_MEDIC,
    /*  3 */ MC_JOB_BUCKET_BRIGADE,
    /*  4 */ MC_JOB_POSTMAN_ROUTE,
    /*  5 */ MC_JOB_MILK_RUN,
    /*  6 */ MC_JOB_BOUNTY_BOARD,
    /*  7 */ MC_JOB_STREET_RACES,
    /*  8 */ MC_JOB_GORON_GRAND_PRIX,
    /*  9 */ MC_JOB_BOMBER_RALLY,
    /* 10 */ MC_JOB_FIGHT_NIGHT,
    /* 11 */ MC_JOB_TABLOID,
    /* 12 */ MC_JOB_MAX
} McSideJob;

typedef enum McChapter {
    /* 0 */ MC_CHAPTER_PROLOGUE,
    /* 1 */ MC_CHAPTER_SMALL_TIME,
    /* 2 */ MC_CHAPTER_TURF,
    /* 3 */ MC_CHAPTER_THE_TOWER,
    /* 4 */ MC_CHAPTER_POST_GAME
} McChapter;

#define MC_SAVE (gSaveContext.save.saveInfo.mc)

#define MC_FLAG_WORD(flag) ((flag) >> 5)
#define MC_FLAG_BIT(flag) (1u << ((flag) & 0x1F))

#define MC_CHECK_STORY(flag) (MC_SAVE.storyFlags[MC_FLAG_WORD(flag)] & MC_FLAG_BIT(flag))
#define MC_SET_STORY(flag) (MC_SAVE.storyFlags[MC_FLAG_WORD(flag)] |= MC_FLAG_BIT(flag))
#define MC_CLEAR_STORY(flag) (MC_SAVE.storyFlags[MC_FLAG_WORD(flag)] &= ~MC_FLAG_BIT(flag))

#define MC_CHECK_CYCLE(flag) (MC_SAVE.cycleFlags[MC_FLAG_WORD(flag)] & MC_FLAG_BIT(flag))
#define MC_SET_CYCLE(flag) (MC_SAVE.cycleFlags[MC_FLAG_WORD(flag)] |= MC_FLAG_BIT(flag))
#define MC_CLEAR_CYCLE(flag) (MC_SAVE.cycleFlags[MC_FLAG_WORD(flag)] &= ~MC_FLAG_BIT(flag))

/* ---------------------------------------------------------------------------------------------------------------
 * Text IDs (mod/assets/text/mc_message_data.h)
 * ------------------------------------------------------------------------------------------------------------- */

#define MC_TEXT_TITLE_MAJORA_CITY 0x4D00
#define MC_TEXT_INTRO_NARRATION_1 0x4D01
#define MC_TEXT_INTRO_NARRATION_2 0x4D02

/* ---------------------------------------------------------------------------------------------------------------
 * Opening ("Highway to the City")
 * ------------------------------------------------------------------------------------------------------------- */

// Where a brand-new file starts: Termina Field, spawn from the Road to Southern Swamp (south edge, facing town).
#define MC_INTRO_ENTRANCE ENTRANCE(TERMINA_FIELD, 1)

// What the intro hands off to once Epona reaches the gate.
#define MC_HANDOFF_VANILLA_PROLOGUE 0 // M1: vanilla Lost Woods prologue, keeps the game completable
#define MC_HANDOFF_SOUTH_GATE 1       // M2: arrive in South Clock Town, start Prologue P2 "Impounded"

#ifndef MC_INTRO_HANDOFF
#define MC_INTRO_HANDOFF MC_HANDOFF_VANILLA_PROLOGUE
#endif

/* ---------------------------------------------------------------------------------------------------------------
 * Skyline layouts (ovl_Mc_Skyline params)
 * ------------------------------------------------------------------------------------------------------------- */

typedef enum McSkylineLayout {
    /* 0 */ MC_SKYLINE_LAYOUT_FIELD, // Termina Field: towers inside the walls, around the Clock Tower
    /* 1 */ MC_SKYLINE_LAYOUT_TOWN,  // Old Town scenes: towers outside the walls
    /* 2 */ MC_SKYLINE_LAYOUT_MAX
} McSkylineLayout;

/* ---------------------------------------------------------------------------------------------------------------
 * Core hooks (mc_core.c)
 * ------------------------------------------------------------------------------------------------------------- */

// Called from Play_Init once Player and the room's actors exist. Spawns Majora City actors for the scene.
void McCore_OnPlayInit(struct PlayState* play);

// Called from Sram_SaveEndOfCycle (Song of Time / Dawn of a New Day). Clears per-cycle state.
void McCore_OnCycleReset(void);

// Entrance used by Sram_OpenSave for files that have never reached Clock Town.
u16 McCore_GetFreshFileEntrance(void);

// Finds the Clock Tower in the current scene. Writes its position to `outPos` and returns true if found.
s32 McCore_FindCityCenter(struct PlayState* play, Vec3f* outPos);

// Adds `amount` Respect with `faction`, clamped to [-1000, 1000].
void McCore_AddRespect(s32 faction, s32 amount);

#endif
