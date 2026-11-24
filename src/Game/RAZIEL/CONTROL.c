/* DC 8C0E0840, 11 functions. PSX: src/Game/RAZIEL/CONTROL.c */
#include "Game/RAZIEL/CONTROL.h"

INCLUDE_ASM("asm/nonmatchings/Game/RAZIEL/CONTROL", SetPhysics);
INCLUDE_ASM("asm/nonmatchings/Game/RAZIEL/CONTROL", ResetPhysics);
INCLUDE_ASM("asm/nonmatchings/Game/RAZIEL/CONTROL", SetDampingPhysics);
INCLUDE_ASM("asm/nonmatchings/Game/RAZIEL/CONTROL", SetImpulsePhysics);
INCLUDE_ASM("asm/nonmatchings/Game/RAZIEL/CONTROL", SetDropPhysics);
INCLUDE_ASM("asm/nonmatchings/Game/RAZIEL/CONTROL", func_8C0E0B20);
INCLUDE_ASM("asm/nonmatchings/Game/RAZIEL/CONTROL", InitExternalForces);
INCLUDE_ASM("asm/nonmatchings/Game/RAZIEL/CONTROL", SetExternalForce);
INCLUDE_ASM("asm/nonmatchings/Game/RAZIEL/CONTROL", SetExternalTransitionForce);
INCLUDE_ASM("asm/nonmatchings/Game/RAZIEL/CONTROL", ProcessPhysics);
INCLUDE_ASM("asm/nonmatchings/Game/RAZIEL/CONTROL", ApplyExternalLocalForces);
