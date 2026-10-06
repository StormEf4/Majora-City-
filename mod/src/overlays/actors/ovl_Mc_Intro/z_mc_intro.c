/*
 * File: z_mc_intro.c
 * Overlay: ovl_Mc_Intro
 * Description: Majora City opening cutscene director, "Highway to the City".
 *
 * Link rides Epona across Termina Field toward the Majora City skyline. Storyboard and design notes are in
 * docs/design/opening-cutscene.md.
 *
 * How it works:
 * - Epona is spawned in cutscene mode (ENHORSE_9) and Link is mounted on her with the same two calls vanilla
 *   uses for a mounted scene entry (Player_MountHorse + Player_SetCameraHorseSetting).
 * - A manual cutscene is started and this actor writes a synthetic actor cue into play->csCtx.playerCue every
 *   frame. En_Horse's cutscene handler reads it exactly as it would read a cue from scripted cutscene data:
 *   cue 36 gallops to cue.endPos, cue 38 rears. Player ignores cues while riding, so Link stays in the saddle.
 * - Waypoints are computed at runtime from Link's spawn point toward the Clock Tower, with floor raycasts for
 *   height, so the intro needs no edits to the (ROM-extracted) Termina Field scene data.
 * - The camera is a sub camera driven by a small shot table, positioned relative to Epona.
 */

#include "z_mc_intro.h"
#include "z64horse.h"
#include "overlays/actors/ovl_En_Horse/z_en_horse.h"

#define FLAGS (ACTOR_FLAG_UPDATE_CULLING_DISABLED | ACTOR_FLAG_DRAW_CULLING_DISABLED)

// En_Horse cutscene cue IDs (sCsActionTable in z_en_horse.c)
#define MC_INTRO_CUE_GALLOP 36 // EnHorse_CsMoveToPoint: gallop toward cue.endPos
#define MC_INTRO_CUE_REAR 38   // EnHorse_CsRearing: rear up and neigh

// Epona stops this far from the Clock Tower, just outside the South Gate. Tune in-game.
#define MC_INTRO_GATE_RADIUS 1400.0f
// If no Clock Tower is found, ride this far straight ahead.
#define MC_INTRO_FALLBACK_RIDE 2600.0f
// Never ride less than this, even if Link spawned close to town.
#define MC_INTRO_MIN_RIDE 600.0f
// Advance to the next waypoint within this XZ distance (keeps the gallop continuous).
#define MC_INTRO_WAYPOINT_REACHED 80.0f
// Stuck detection. Either signal ends the ride early:
// - Epona moved less than MC_INTRO_STUCK_MOVE units per frame for MC_INTRO_STUCK_FRAMES (blocked by a wall),
// - she got no closer to the waypoint for MC_INTRO_NO_PROGRESS_FRAMES (sliding along an obstacle). This is longer
//   than a full U-turn (~41 frames at En_Horse's cutscene turn rate) so turning toward the city never trips it.
#define MC_INTRO_STUCK_MOVE 1.0f
#define MC_INTRO_STUCK_FRAMES 40
#define MC_INTRO_NO_PROGRESS_FRAMES 100
// Hard cap for the ride, so the cutscene can never soft-lock.
#define MC_INTRO_RIDE_MAX_FRAMES 600
#define MC_INTRO_ARRIVE_FRAMES 60
#define MC_INTRO_EXIT_FRAMES 30
// START skips the intro after this many frames of the ride.
#define MC_INTRO_SKIP_FRAMES 20

// Camera aims at the skyline this high above the Clock Tower's base.
#define MC_INTRO_SKYLINE_FOCUS_Y 1700.0f
#define MC_INTRO_CRANE_FOCUS_Y 2200.0f
// Keep the camera at least this far above the ground.
#define MC_INTRO_CAM_MIN_HEIGHT 20.0f

// Narration and title timing (frames since the ride started)
#define MC_INTRO_NARRATION_1_FRAME 10
#define MC_INTRO_NARRATION_2_FRAME 95
#define MC_INTRO_TITLE_FRAME 240

void McIntro_Init(Actor* thisx, PlayState* play);
void McIntro_Destroy(Actor* thisx, PlayState* play);
void McIntro_Update(Actor* thisx, PlayState* play);

ActorProfile Mc_Intro_Profile = {
    /**/ ACTOR_MC_INTRO,
    /**/ ACTORCAT_PROP,
    /**/ FLAGS,
    /**/ GAMEPLAY_KEEP,
    /**/ sizeof(McIntro),
    /**/ McIntro_Init,
    /**/ McIntro_Destroy,
    /**/ McIntro_Update,
    /**/ NULL,
};

typedef struct McIntroShotDef {
    /* 0x00 */ s16 startFrame; // Frames since the ride started (unused for the arrival shot)
    /* 0x02 */ s16 fov;
    /* 0x04 */ Vec3s eye; // Relative to Epona: x = forward, y = right, z = up
    /* 0x0A */ Vec3s at;  // Same convention
} McIntroShotDef;         // size = 0x10

static McIntroShotDef sShots[MC_INTRO_SHOT_MAX] = {
    /* MC_INTRO_SHOT_HORIZON  */ { 0, 60, { -300, 60, 60 }, { 0, 0, 0 } }, // `at` is the skyline
    /* MC_INTRO_SHOT_TRACKING */ { 80, 60, { 40, 260, 70 }, { 120, 0, 60 } },
    /* MC_INTRO_SHOT_HOOVES   */ { 170, 55, { 140, -90, 15 }, { 0, 0, 25 } },
    /* MC_INTRO_SHOT_CRANE    */ { 220, 60, { 250, 30, 40 }, { 0, 0, 70 } }, // Start pose, see sCraneEnd
    /* MC_INTRO_SHOT_CHASE    */ { 340, 60, { -360, 0, 110 }, { 200, 0, 80 } },
    /* MC_INTRO_SHOT_ARRIVAL  */ { 0, 55, { 260, 60, 20 }, { 0, 0, 120 } },
};

// The crane shot ends high behind Link, looking over his shoulder at the skyline.
static Vec3s sCraneEndEye = { -500, 120, 450 };
#define MC_INTRO_CRANE_FRAMES 120
#define MC_INTRO_CRANE_END_FOV 75

/**
 * Offsets `base` by `forward`/`right`/`up` in the frame of an actor facing `yaw`.
 * Facing +Z (yaw 0), "right" is -X.
 */
static void McIntro_Offset(Vec3f* dst, Vec3f* base, s16 yaw, f32 forward, f32 right, f32 up) {
    f32 sinYaw = Math_SinS(yaw);
    f32 cosYaw = Math_CosS(yaw);

    dst->x = base->x + (sinYaw * forward) - (cosYaw * right);
    dst->y = base->y + up;
    dst->z = base->z + (cosYaw * forward) + (sinYaw * right);
}

static void McIntro_Lerp(Vec3f* dst, Vec3f* a, Vec3f* b, f32 t) {
    dst->x = a->x + (b->x - a->x) * t;
    dst->y = a->y + (b->y - a->y) * t;
    dst->z = a->z + (b->z - a->z) * t;
}

static f32 McIntro_FloorY(PlayState* play, Vec3f* pos, f32 probeHeight, f32 fallback) {
    CollisionPoly* poly;
    Vec3f probe = *pos;
    f32 floorY;

    probe.y += probeHeight;
    floorY = BgCheck_EntityRaycastFloor1(&play->colCtx, &poly, &probe);
    return (floorY == BGCHECK_Y_MIN) ? fallback : floorY;
}

static void McIntro_BuildWaypoints(McIntro* this, PlayState* play, Vec3f* start) {
    f32 rideDist = Math_Vec3f_DistXZ(start, &this->cityCenter) - MC_INTRO_GATE_RADIUS;
    s16 yaw = Math_Vec3f_Yaw(start, &this->cityCenter);
    s32 i;

    rideDist = CLAMP_MIN(rideDist, MC_INTRO_MIN_RIDE);

    for (i = 0; i < MC_INTRO_WAYPOINT_COUNT; i++) {
        f32 dist = rideDist * (i + 1) / MC_INTRO_WAYPOINT_COUNT;
        Vec3f* waypoint = &this->waypoints[i];

        waypoint->x = start->x + Math_SinS(yaw) * dist;
        waypoint->y = start->y;
        waypoint->z = start->z + Math_CosS(yaw) * dist;
        waypoint->y = McIntro_FloorY(play, waypoint, 1000.0f, start->y);
    }
    this->camYaw = yaw;
}

static void McIntro_SetCue(McIntro* this, u16 cueId, Vec3f* target) {
    this->cue.id = cueId;
    this->cue.startFrame = 0;
    this->cue.endFrame = 0xFFFF;
    this->cue.rot.x = 0;
    this->cue.rot.y = this->horse->shape.rot.y;
    this->cue.rot.z = 0;
    // The start position is only used when the horse first enters a cue; keep it where it is.
    this->cue.startPos.x = this->horse->world.pos.x;
    this->cue.startPos.y = this->horse->world.pos.y;
    this->cue.startPos.z = this->horse->world.pos.z;
    this->cue.endPos.x = target->x;
    this->cue.endPos.y = target->y;
    this->cue.endPos.z = target->z;
    this->cue.normal.x = this->cue.normal.y = this->cue.normal.z = 0.0f;
}

void McIntro_Init(Actor* thisx, PlayState* play) {
    McIntro* this = (McIntro*)thisx;
    Player* player = GET_PLAYER(play);
    f32 floorY;

    this->actor.room = -1;
    this->subCamId = SUB_CAM_ID_DONE;
    this->subCamFov = 60.0f;
    this->state = MC_INTRO_STATE_WAIT;

    // Our own title card comes later; skip the scene's "Termina Field" card for this entrance.
    gSaveContext.showTitleCard = false;

    if (!McCore_FindCityCenter(play, &this->cityCenter)) {
        McIntro_Offset(&this->cityCenter, &player->actor.world.pos, player->actor.shape.rot.y,
                       MC_INTRO_FALLBACK_RIDE + MC_INTRO_GATE_RADIUS, 0.0f, 0.0f);
    }

    // Epona, in cutscene mode, under Link: the same setup vanilla uses when Link enters a field mounted.
    floorY = McIntro_FloorY(play, &player->actor.world.pos, 5.0f, player->actor.world.pos.y);
    this->horse = Actor_Spawn(&play->actorCtx, play, ACTOR_EN_HORSE, player->actor.world.pos.x, floorY,
                              player->actor.world.pos.z, 0, player->actor.shape.rot.y, 0,
                              ENHORSE_PARAMS(ENHORSE_PARAM_4000, ENHORSE_9));
    if (this->horse == NULL) {
        // Without Epona there is no ride; go straight to the hand-off.
        this->state = MC_INTRO_STATE_EXIT;
        return;
    }

    Player_MountHorse(play, player, this->horse);
    Player_SetCameraHorseSetting(play, player);

    McIntro_BuildWaypoints(this, play, &player->actor.world.pos);
}

void McIntro_Destroy(Actor* thisx, PlayState* play) {
}

static void McIntro_StartRide(McIntro* this, PlayState* play) {
    Cutscene_StartManual(play, &play->csCtx);

    this->subCamId = Play_CreateSubCamera(play);
    Play_ChangeCameraStatus(play, CAM_ID_MAIN, CAM_STATUS_WAIT);
    Play_ChangeCameraStatus(play, this->subCamId, CAM_STATUS_ACTIVE);

    this->waypointIndex = 0;
    McIntro_SetCue(this, MC_INTRO_CUE_GALLOP, &this->waypoints[0]);
    this->bestDist = Math_Vec3f_DistXZ(&this->horse->world.pos, &this->waypoints[0]);
    this->stuckTimer = 0;
    this->noProgressTimer = 0;
    this->timer = 0;
    this->shot = MC_INTRO_SHOT_HORIZON;
    this->state = MC_INTRO_STATE_RIDE;
}

static void McIntro_StartArrival(McIntro* this) {
    McIntro_SetCue(this, MC_INTRO_CUE_REAR, &this->horse->world.pos);
    this->camYaw = this->horse->shape.rot.y;
    this->shot = MC_INTRO_SHOT_ARRIVAL;
    this->timer = 0;
    this->state = MC_INTRO_STATE_ARRIVE;
}

static void McIntro_HandOff(McIntro* this, PlayState* play) {
    MC_SET_STORY(MC_STORY_INTRO_DONE);
    gHorseIsMounted = false;

#if MC_INTRO_HANDOFF == MC_HANDOFF_SOUTH_GATE
    MC_SET_STORY(MC_STORY_EPONA_IMPOUNDED);
    play->nextEntrance = ENTRANCE(SOUTH_CLOCK_TOWN, 0);
    gSaveContext.nextCutsceneIndex = 0;
    gSaveContext.nextDayTime = CLOCK_TIME(6, 0);
    gSaveContext.nextTransitionType = TRANS_TYPE_FADE_WHITE;
    Sram_IncrementDay();
#else
    // Same entrance and cutscene index a fresh vanilla file starts with (see Sram_OpenSave).
    play->nextEntrance = ENTRANCE(CUTSCENE, 0);
    gSaveContext.nextCutsceneIndex = 0;
#endif

    play->transitionTrigger = TRANS_TRIGGER_START;
    play->transitionType = TRANS_TYPE_FADE_WHITE;
}

static void McIntro_UpdateText(McIntro* this, PlayState* play) {
    if (Message_GetState(&play->msgCtx) != TEXT_STATE_NONE) {
        return;
    }

    if (this->state == MC_INTRO_STATE_RIDE) {
        if ((this->narrationIndex == 0) && (this->timer >= MC_INTRO_NARRATION_1_FRAME)) {
            Message_StartTextbox(play, MC_TEXT_INTRO_NARRATION_1, NULL);
            this->narrationIndex++;
            return;
        }
        if ((this->narrationIndex == 1) && (this->timer >= MC_INTRO_NARRATION_2_FRAME)) {
            Message_StartTextbox(play, MC_TEXT_INTRO_NARRATION_2, NULL);
            this->narrationIndex++;
            return;
        }
    }

    // Narration only plays during the ride; the title card is guaranteed by the arrival at the latest.
    if (!this->titleShown && ((this->timer >= MC_INTRO_TITLE_FRAME) || (this->state == MC_INTRO_STATE_ARRIVE))) {
        Message_DisplaySceneTitleCard(play, MC_TEXT_TITLE_MAJORA_CITY);
        this->titleShown = true;
        MC_SET_CYCLE(MC_CYCLE_SKYLINE_SEEN);
    }
}

static void McIntro_Ride(McIntro* this, PlayState* play) {
    Vec3f* target = &this->waypoints[this->waypointIndex];
    f32 dist = Math_Vec3f_DistXZ(&this->horse->world.pos, target);

    if (dist < MC_INTRO_WAYPOINT_REACHED) {
        this->waypointIndex++;
        if (this->waypointIndex >= MC_INTRO_WAYPOINT_COUNT) {
            McIntro_StartArrival(this);
            return;
        }
        target = &this->waypoints[this->waypointIndex];
        McIntro_SetCue(this, MC_INTRO_CUE_GALLOP, target);
        dist = Math_Vec3f_DistXZ(&this->horse->world.pos, target);
        this->bestDist = dist;
        this->noProgressTimer = 0;
    }

    // Epona ran into a rock, a fence or a tree: end the ride here rather than galloping in place.
    // (The horse updates before this actor, so prevPos -> world.pos is this frame's movement.)
    if (Math_Vec3f_DistXZ(&this->horse->world.pos, &this->horse->prevPos) < MC_INTRO_STUCK_MOVE) {
        this->stuckTimer++;
    } else {
        this->stuckTimer = 0;
    }
    if (dist < this->bestDist - 1.0f) {
        this->bestDist = dist;
        this->noProgressTimer = 0;
    } else {
        this->noProgressTimer++;
    }

    if ((this->stuckTimer > MC_INTRO_STUCK_FRAMES) || (this->noProgressTimer > MC_INTRO_NO_PROGRESS_FRAMES) ||
        (this->timer > MC_INTRO_RIDE_MAX_FRAMES)) {
        McIntro_StartArrival(this);
        return;
    }

    // Advance through the shot list by time.
    while (((this->shot + 1) < MC_INTRO_SHOT_ARRIVAL) && (this->timer >= sShots[this->shot + 1].startFrame)) {
        this->shot++;
    }
}

static void McIntro_UpdateCamera(McIntro* this, PlayState* play) {
    McIntroShotDef* shot = &sShots[this->shot];
    Vec3f* horsePos = &this->horse->world.pos;
    Vec3f skyline;
    f32 fov = shot->fov;
    f32 minEyeY;

    if (this->state == MC_INTRO_STATE_RIDE) {
        // Follow Epona's heading smoothly; she sways a little while steering toward each waypoint.
        Math_ApproachS(&this->camYaw, this->horse->shape.rot.y, 4, 0x300);
    }

    McIntro_Offset(&this->subCamEye, horsePos, this->camYaw, shot->eye.x, shot->eye.y, shot->eye.z);
    McIntro_Offset(&this->subCamAt, horsePos, this->camYaw, shot->at.x, shot->at.y, shot->at.z);

    if (this->shot == MC_INTRO_SHOT_HORIZON) {
        skyline = this->cityCenter;
        skyline.y += MC_INTRO_SKYLINE_FOCUS_Y;
        this->subCamAt = skyline;
    } else if (this->shot == MC_INTRO_SHOT_CRANE) {
        Vec3f endEye;
        f32 t = (f32)(this->timer - shot->startFrame) / MC_INTRO_CRANE_FRAMES;

        t = CLAMP(t, 0.0f, 1.0f);
        t = t * t * (3.0f - 2.0f * t); // smoothstep

        McIntro_Offset(&endEye, horsePos, this->camYaw, sCraneEndEye.x, sCraneEndEye.y, sCraneEndEye.z);
        skyline = this->cityCenter;
        skyline.y += MC_INTRO_CRANE_FOCUS_Y;

        McIntro_Lerp(&this->subCamEye, &this->subCamEye, &endEye, t);
        McIntro_Lerp(&this->subCamAt, &this->subCamAt, &skyline, t);
        fov = shot->fov + (MC_INTRO_CRANE_END_FOV - shot->fov) * t;
    }

    minEyeY = McIntro_FloorY(play, &this->subCamEye, 300.0f, BGCHECK_Y_MIN) + MC_INTRO_CAM_MIN_HEIGHT;
    this->subCamEye.y = CLAMP_MIN(this->subCamEye.y, minEyeY);
    Math_ApproachF(&this->subCamFov, fov, 0.2f, 2.0f);

    Play_SetCameraAtEye(play, this->subCamId, &this->subCamAt, &this->subCamEye);
    Play_SetCameraFov(play, this->subCamId, this->subCamFov);
}

void McIntro_Update(Actor* thisx, PlayState* play) {
    McIntro* this = (McIntro*)thisx;

    if ((this->horse != NULL) && (this->horse->update == NULL)) {
        // Epona was unloaded under us; bail out to the hand-off.
        this->horse = NULL;
        this->state = MC_INTRO_STATE_EXIT;
        this->timer = 0;
    }

    if ((this->state == MC_INTRO_STATE_RIDE) || (this->state == MC_INTRO_STATE_ARRIVE) ||
        (this->state == MC_INTRO_STATE_EXIT)) {
        // Link holds the reins but the director steers: feed Player a neutral controller, through the fade too.
        play->actorCtx.isOverrideInputOn = true;
        bzero(&play->actorCtx.overrideInput, sizeof(Input));
    }

    if ((this->state == MC_INTRO_STATE_RIDE) || (this->state == MC_INTRO_STATE_ARRIVE)) {
        // Feed Epona her cue, as a scripted cutscene would.
        play->csCtx.playerCue = &this->cue;

        if ((this->timer > MC_INTRO_SKIP_FRAMES) && CHECK_BTN_ALL(play->state.input[0].press.button, BTN_START)) {
            this->state = MC_INTRO_STATE_EXIT;
            this->timer = 0;
        }
    }

    switch (this->state) {
        case MC_INTRO_STATE_WAIT:
            // Let the scene's own entrance cutscene (if any) finish, and wait for Epona to finish loading.
            if ((CutsceneManager_GetCurrentCsId() == CS_ID_NONE) && (this->horse->update != NULL) &&
                (this->timer > 1)) {
                McIntro_StartRide(this, play);
                return;
            }
            break;

        case MC_INTRO_STATE_RIDE:
            McIntro_UpdateText(this, play);
            McIntro_Ride(this, play);
            break;

        case MC_INTRO_STATE_ARRIVE:
            McIntro_UpdateText(this, play);
            if (this->timer == 0) {
                Rumble_Request(0.0f, 180, 20, 10);
            }
            if (this->timer >= MC_INTRO_ARRIVE_FRAMES) {
                this->state = MC_INTRO_STATE_EXIT;
                this->timer = 0;
                return;
            }
            break;

        case MC_INTRO_STATE_EXIT:
            if (this->timer == 0) {
                McIntro_HandOff(this, play);
            }
            if (this->timer >= MC_INTRO_EXIT_FRAMES) {
                this->state = MC_INTRO_STATE_DONE;
            }
            break;

        default:
            break;
    }

    if ((this->subCamId != SUB_CAM_ID_DONE) && (this->horse != NULL) &&
        ((this->state == MC_INTRO_STATE_RIDE) || (this->state == MC_INTRO_STATE_ARRIVE))) {
        McIntro_UpdateCamera(this, play);
    }

    this->timer++;
}
