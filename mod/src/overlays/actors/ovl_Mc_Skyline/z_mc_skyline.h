#ifndef Z_MC_SKYLINE_H
#define Z_MC_SKYLINE_H

#include "global.h"
#include "mc/mc.h"

struct McSkyline;

#define MC_SKYLINE_GET_LAYOUT(thisx) ((thisx)->params & 0xF)

#define MC_SKYLINE_MAX_TOWERS 32

typedef struct McSkylineTower {
    /* 0x0 */ u16 angle;    // Around the city centre (binary angle, 0 = +Z / south)
    /* 0x2 */ s16 radius;   // Distance from the city centre
    /* 0x4 */ u16 yaw;      // Tower rotation
    /* 0x6 */ u8 archetype; // Index into sMcSkylineArchetypeDLs
    /* 0x7 */ u8 tone;      // Index into sMcSkylineTones
    /* 0x8 */ u8 scaleXZ;   // Percent
    /* 0x9 */ u8 scaleY;    // Percent
} McSkylineTower;           // size = 0xA

typedef enum McSkylineState {
    /* 0 */ MC_SKYLINE_STATE_FIND_CENTER, // Waiting for the Clock Tower actor to appear in the actor list
    /* 1 */ MC_SKYLINE_STATE_READY
} McSkylineState;

typedef struct McSkyline {
    /* 0x000 */ Actor actor;
    /* 0x144 */ Vec3f center;
    /* 0x150 */ McSkylineTower* towers;
    /* 0x154 */ s16 towerCount;
    /* 0x156 */ s16 searchTimer;
    /* 0x158 */ u8 state;
    /* 0x15C */ Vec3f towerPos[MC_SKYLINE_MAX_TOWERS];
} McSkyline;

#endif
