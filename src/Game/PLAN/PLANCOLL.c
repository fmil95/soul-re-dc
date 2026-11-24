/* DC 8C0ECD00, 5 functions. PSX: src/Game/PLAN/PLANCOLL.c */
#include "Game/PLAN/PLANCOLL.h"

INCLUDE_ASM("asm/nonmatchings/Game/PLAN/PLANCOLL", PLANCOLL_DoesLOSExistFinal);
INCLUDE_ASM("asm/nonmatchings/Game/PLAN/PLANCOLL", PLANCOLL_CheckUnderwaterPoint);
INCLUDE_ASM("asm/nonmatchings/Game/PLAN/PLANCOLL", PLANCOLL_FindTerrainHitFinal);
INCLUDE_ASM("asm/nonmatchings/Game/PLAN/PLANCOLL", PLANCOLL_DoesStraightLinePathExist);
INCLUDE_ASM("asm/nonmatchings/Game/PLAN/PLANCOLL", PLANCOLL_DoesWaterPathUpExist);
