#include "Game/BSP.h"

INCLUDE_ASM("asm/nonmatchings/Game/BSP", func_8C0638E0);
INCLUDE_ASM("asm/nonmatchings/Game/BSP", func_8C063DE0);
INCLUDE_ASM("asm/nonmatchings/Game/BSP", func_8C063EA0);
INCLUDE_ASM("asm/nonmatchings/Game/BSP", func_8C064000);
INCLUDE_ASM("asm/nonmatchings/Game/BSP", SBSP_IntroduceInstances);

void SBSP_IntroduceInstancesAndLights(Terrain *terrain, CameraCore *cameraCore, LightInfo *lightInfo, int unitID)
{
    (void)cameraCore;
    (void)lightInfo;

    SBSP_IntroduceInstances(terrain, unitID);
}
