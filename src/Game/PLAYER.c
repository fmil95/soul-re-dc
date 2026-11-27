#include "Game/PLAYER.h"

void PLAYER_TurnHead(Instance *instance, short *rotx, short *rotz, GameTracker *gameTracker)
{
    if (INSTANCE_Query(instance, queryWhatAmI) & 0x1)
    {
        RAZIEL_TurnHead(instance, rotx, rotz, gameTracker);
    }
    else
    {
        MONAPI_TurnHead(instance, rotx, rotz, gameTracker);
    }
}

INCLUDE_ASM("asm/nonmatchings/Game/PLAYER", PLAYER_OkToLookAround);
INCLUDE_ASM("asm/nonmatchings/Game/PLAYER", PLAYER_SetLookAround);
INCLUDE_ASM("asm/nonmatchings/Game/PLAYER", PLAYER_ReSetLookAround);
INCLUDE_ASM("asm/nonmatchings/Game/PLAYER", func_8C09F6A0);
INCLUDE_ASM("asm/nonmatchings/Game/PLAYER", func_8C09F6C0);
INCLUDE_ASM("asm/nonmatchings/Game/PLAYER", func_8C09F6E0);
