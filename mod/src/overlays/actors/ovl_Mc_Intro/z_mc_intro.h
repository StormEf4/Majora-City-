#ifndef Z_MC_INTRO_H
#define Z_MC_INTRO_H

#include "global.h"
#include "mc/mc.h"

struct McIntro;

#define MC_INTRO_WAYPOINT_COUNT 4

typedef enum McIntroState {
    /* 0 */ MC_INTRO_STATE_WAIT,   // Wait for the cutscene manager to be free
    /* 1 */ MC_INTRO_STATE_RIDE,   // Shots 1-5: galloping toward the city
    /* 2 */ MC_INTRO_STATE_ARRIVE, // Shot 6: Epona rears at the gate
    /* 3 */ MC_INTRO_STATE_EXIT,   // Shot 7: fade out and hand off
    /* 4 */ MC_INTRO_STATE_DONE
} McIntroState;

typedef enum McIntroShot {
    /* 0 */ MC_INTRO_SHOT_HORIZON,
    /* 1 */ MC_INTRO_SHOT_TRACKING,
    /* 2 */ MC_INTRO_SHOT_HOOVES,
    /* 3 */ MC_INTRO_SHOT_CRANE,
    /* 4 */ MC_INTRO_SHOT_CHASE,
    /* 5 */ MC_INTRO_SHOT_ARRIVAL,
    /* 6 */ MC_INTRO_SHOT_MAX
} McIntroShot;

typedef struct McIntro {
    /* 0x000 */ Actor actor;
    /* 0x144 */ Actor* horse;
    /* 0x148 */ CsCmdActorCue cue; // Fed to Epona through play->csCtx.playerCue
    /* 0x178 */ Vec3f cityCenter;
    /* 0x184 */ Vec3f waypoints[MC_INTRO_WAYPOINT_COUNT];
    /* 0x1B4 */ Vec3f subCamEye;
    /* 0x1C0 */ Vec3f subCamAt;
    /* 0x1CC */ f32 subCamFov;
    /* 0x1D0 */ f32 bestDist;        // Closest Epona has come to the current waypoint
    /* 0x1D4 */ s16 subCamId;
    /* 0x1D6 */ s16 timer;
    /* 0x1D8 */ s16 stuckTimer;      // Frames Epona has barely moved
    /* 0x1DA */ s16 noProgressTimer; // Frames without getting closer to the waypoint
    /* 0x1DC */ s16 camYaw;
    /* 0x1DE */ u8 state;
    /* 0x1DF */ u8 shot;
    /* 0x1E0 */ u8 waypointIndex;
    /* 0x1E1 */ u8 narrationIndex;
    /* 0x1E2 */ u8 titleShown;
} McIntro;

#endif
