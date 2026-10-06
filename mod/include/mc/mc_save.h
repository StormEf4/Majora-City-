#ifndef MC_MC_SAVE_H
#define MC_MC_SAVE_H

/**
 * Majora City persistent save data.
 *
 * This struct replaces the unused `UNK_TYPE1 unk_DF4[0x54]` region of `SaveInfo` (see patches/), so the save
 * file layout and flash page usage stay byte-for-byte the same size as vanilla. It is zeroed for new files by
 * the existing `bzero(&gSaveContext.save.saveInfo, ...)` in Sram_ResetSave, and written to flash with the rest
 * of SaveInfo by every regular, owl and special save.
 *
 * The size is checked at compile time in mc_core.c. Never grow this struct past 0x54 bytes.
 */

#include "PR/ultratypes.h"

#define MC_SAVE_DATA_SIZE 0x54

#define MC_STORY_FLAG_WORDS 4 // 128 permanent story flags
#define MC_CYCLE_FLAG_WORDS 2 // 64 flags cleared by the Song of Time
#define MC_TAG_WORDS 2        // 64 graffiti tags
#define MC_FACTION_COUNT 8
#define MC_SIDE_JOB_COUNT 12

typedef struct McSaveData {
    /* 0x00 */ u32 storyFlags[MC_STORY_FLAG_WORDS];  // McStoryFlag, survive the Song of Time
    /* 0x10 */ u32 cycleFlags[MC_CYCLE_FLAG_WORDS];  // McCycleFlag, cleared by McCore_OnCycleReset
    /* 0x18 */ u32 tagsSprayed[MC_TAG_WORDS];        // Tagger's Mask collectibles
    /* 0x20 */ u32 stuntJumpsDone;                   // Epona stunt jumps
    /* 0x24 */ u32 rampagesDone;                     // Masked Rampages
    /* 0x28 */ s16 factionRep[MC_FACTION_COUNT];     // McFaction, Respect in [-1000, 1000]
    /* 0x38 */ u8 sideJobLevel[MC_SIDE_JOB_COUNT];   // McSideJob, progress in repeatable jobs
    /* 0x44 */ u8 chapter;                           // McChapter, coarse story progress
    /* 0x45 */ u8 radioStation;                      // McRadioStation, last station played
    /* 0x46 */ u8 safehouseFlags;                    // McSafehouse bit field
    /* 0x47 */ u8 businessFlags;                     // McBusiness bit field
    /* 0x48 */ u8 reserved[0xC];                     // Free for future use; keep zeroed
} McSaveData; // size = 0x54

#endif
