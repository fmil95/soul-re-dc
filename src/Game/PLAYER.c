#include "Game/PLAYER.h"
#include "Game/INSTANCE.h"
#include "Game/MONSTER/MONAPI.h"
#include "Game/RAZIEL/RAZIEL.h"

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

long PLAYER_OkToLookAround(Instance *instance)
{
    if (INSTANCE_Query(instance, queryWhatAmI) & 0x1)
    {
        return RAZIEL_OkToLookAround(instance);
    }
    else
    {
        return MONAPI_OkToLookAround(instance);
    }
}

INCLUDE_ASM("asm/nonmatchings/Game/PLAYER", PLAYER_SetLookAround);
INCLUDE_ASM("asm/nonmatchings/Game/PLAYER", PLAYER_ReSetLookAround);
INCLUDE_ASM("asm/nonmatchings/Game/PLAYER", func_8C09F6A0);
INCLUDE_ASM("asm/nonmatchings/Game/PLAYER", func_8C09F6C0);
INCLUDE_ASM("asm/nonmatchings/Game/PLAYER", func_8C09F6E0);
