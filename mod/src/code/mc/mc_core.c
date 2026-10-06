/**
 * @file mc_core.c
 *
 * Majora City core: story flags, per-scene actor spawning ("scene augmentation"), and the small hooks the
 * patched engine files call into. It lives in the `code` segment, so keep it small; gameplay belongs in
 * actor overlays.
 */

#include "global.h"
#include "mc/mc.h"
#include "overlays/actors/ovl_Obj_Tokeidai/z_obj_tokeidai.h"

// McSaveData replaces SaveInfo.unk_DF4[0x54]; it must never change size.
typedef char McSaveDataSizeCheck[(sizeof(McSaveData) == MC_SAVE_DATA_SIZE) ? 1 : -1];

typedef enum McSpawnCondition {
    /* 0 */ MC_SPAWN_ALWAYS,
    /* 1 */ MC_SPAWN_INTRO_PENDING // Fresh file arriving at MC_INTRO_ENTRANCE without having seen the intro
} McSpawnCondition;

typedef struct McSceneSpawn {
    /* 0x0 */ s16 sceneId;
    /* 0x2 */ s16 actorId;
    /* 0x4 */ s16 params;
    /* 0x6 */ u8 condition; // McSpawnCondition
} McSceneSpawn;              // size = 0x8

/**
 * Actors spawned on top of a scene's own actor list. This lets Majora City add things to vanilla scenes without
 * editing scene data extracted from the player's ROM, which we can't (and don't want to) ship.
 */
static McSceneSpawn sMcSceneSpawns[] = {
    { SCENE_00KEIKOKU, ACTOR_MC_SKYLINE, MC_SKYLINE_LAYOUT_FIELD, MC_SPAWN_ALWAYS },
    { SCENE_00KEIKOKU, ACTOR_MC_INTRO, 0, MC_SPAWN_INTRO_PENDING },
    { SCENE_CLOCKTOWER, ACTOR_MC_SKYLINE, MC_SKYLINE_LAYOUT_TOWN, MC_SPAWN_ALWAYS },
};

static s32 McCore_CheckSpawnCondition(PlayState* play, McSceneSpawn* spawn) {
    switch (spawn->condition) {
        case MC_SPAWN_ALWAYS:
            return true;

        case MC_SPAWN_INTRO_PENDING:
            return !MC_CHECK_STORY(MC_STORY_INTRO_DONE) && !gSaveContext.save.isFirstCycle &&
                   (gSaveContext.save.entrance == MC_INTRO_ENTRANCE) && (gSaveContext.sceneLayer == 0) &&
                   (gSaveContext.respawnFlag == 0);

        default:
            return false;
    }
}

void McCore_OnPlayInit(PlayState* play) {
    Player* player = GET_PLAYER(play);
    s32 i;

    if (player == NULL) {
        return;
    }

    for (i = 0; i < ARRAY_COUNT(sMcSceneSpawns); i++) {
        McSceneSpawn* spawn = &sMcSceneSpawns[i];

        if ((spawn->sceneId == play->sceneId) && McCore_CheckSpawnCondition(play, spawn)) {
            Actor_Spawn(&play->actorCtx, play, spawn->actorId, player->actor.world.pos.x, player->actor.world.pos.y,
                        player->actor.world.pos.z, 0, player->actor.shape.rot.y, 0, spawn->params);
        }
    }
}

void McCore_OnCycleReset(void) {
    s32 i;

    for (i = 0; i < MC_CYCLE_FLAG_WORDS; i++) {
        MC_SAVE.cycleFlags[i] = 0;
    }
}

u16 McCore_GetFreshFileEntrance(void) {
    if (!MC_CHECK_STORY(MC_STORY_INTRO_DONE)) {
        return MC_INTRO_ENTRANCE;
    }
    return ENTRANCE(CUTSCENE, 0);
}

s32 McCore_FindCityCenter(PlayState* play, Vec3f* outPos) {
    Actor* actor;
    Actor* found = NULL;

    for (actor = play->actorCtx.actorLists[ACTORCAT_PROP].first; actor != NULL; actor = actor->next) {
        if (actor->id != ACTOR_OBJ_TOKEIDAI) {
            continue;
        }

        // The wall ring (Termina Field) and the tower clock (South Clock Town) sit on the tower's axis; any other
        // Clock Tower part is still close enough to the centre for placing a skyline.
        if ((OBJ_TOKEIDAI_TYPE(actor) == OBJ_TOKEIDAI_TYPE_TOWER_WALLS_TERMINA_FIELD) ||
            (OBJ_TOKEIDAI_TYPE(actor) == OBJ_TOKEIDAI_TYPE_TOWER_CLOCK_CLOCK_TOWN)) {
            found = actor;
            break;
        }
        if (found == NULL) {
            found = actor;
        }
    }

    if (found == NULL) {
        return false;
    }

    *outPos = found->world.pos;
    return true;
}

void McCore_AddRespect(s32 faction, s32 amount) {
    s32 rep;

    if ((faction < 0) || (faction >= MC_FACTION_MAX)) {
        return;
    }

    rep = MC_SAVE.factionRep[faction] + amount;
    MC_SAVE.factionRep[faction] = CLAMP(rep, -1000, 1000);
}
