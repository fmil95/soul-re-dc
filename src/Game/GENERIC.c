#include "Game/GENERIC.h"

INCLUDE_ASM("asm/nonmatchings/Game/GENERIC", GenericInit);

void GenericCollide(Instance instance, GameTracker gameTracker)
{
    (void)instance;
    (void)gameTracker;
}

INCLUDE_ASM("asm/nonmatchings/Game/GENERIC", GenericProcess);
INCLUDE_ASM("asm/nonmatchings/Game/GENERIC", GenericQuery);
INCLUDE_ASM("asm/nonmatchings/Game/GENERIC", GenericMessage);
INCLUDE_ASM("asm/nonmatchings/Game/GENERIC", GenericRelocateTune);
