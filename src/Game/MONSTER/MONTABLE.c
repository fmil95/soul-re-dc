/* DC 8C107820, 7 functions. PSX: src/Game/MONSTER/MONTABLE.c */
#include "common.h"

INCLUDE_ASM("asm/nonmatchings/Game/MONSTER/MONTABLE", MONTABLE_SetupTablePointer);
INCLUDE_ASM("asm/nonmatchings/Game/MONSTER/MONTABLE", MONTABLE_GetStateFuncs);
INCLUDE_ASM("asm/nonmatchings/Game/MONSTER/MONTABLE", MONTABLE_GetDamageEffectFunc);
INCLUDE_ASM("asm/nonmatchings/Game/MONSTER/MONTABLE", MONTABLE_GetInitFunc);
INCLUDE_ASM("asm/nonmatchings/Game/MONSTER/MONTABLE", MONTABLE_GetCleanUpFunc);
INCLUDE_ASM("asm/nonmatchings/Game/MONSTER/MONTABLE", MONTABLE_SetQueryFunc);
INCLUDE_ASM("asm/nonmatchings/Game/MONSTER/MONTABLE", MONTABLE_SetMessageFunc);
