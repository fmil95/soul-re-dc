/* DC 8C088120, 6 functions. PSX: src/Game/GENERIC.c */
#include "common.h"

INCLUDE_ASM("asm/nonmatchings/Game/GENERIC", GenericInit);
INCLUDE_ASM("asm/nonmatchings/Game/GENERIC", GenericCollide);
INCLUDE_ASM("asm/nonmatchings/Game/GENERIC", GenericProcess);
INCLUDE_ASM("asm/nonmatchings/Game/GENERIC", GenericQuery);
INCLUDE_ASM("asm/nonmatchings/Game/GENERIC", GenericMessage);
INCLUDE_ASM("asm/nonmatchings/Game/GENERIC", GenericRelocateTune);
