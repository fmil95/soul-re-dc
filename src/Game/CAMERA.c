#include "Game/CAMERA.h"
#include "Game/MATH3D.h"

INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_CalculateViewVolumeNormals);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_CalcVVClipInfo);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_SetViewVolume);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_SetProjDistance);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_CreateNewFocuspoint);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_SaveMode);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_RestoreMode);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_Save);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_Restore);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", SplineGetNextPointDC);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_SetMode);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_Initialize);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_SetInstanceFocus);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_SetZRotation);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_LengthSVector);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_SetValue);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_AngleDifference);

short CAMERA_SignedAngleDifference(short angle0, short angle1)
{
    return AngleDiff(angle1, angle0);
}

INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_QueryMode);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_SetMaxVel);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_SetTarget);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_CalcPosition);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_SetFocus);

void CAMERA_Lock(Camera *camera, long lock)
{
    camera->lock |= lock;
}

void CAMERA_Unlock(Camera *camera, long unlock)
{
    camera->lock &= ~unlock;
}

INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_SetSmoothValue);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_SetTimer);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_Adjust_tilt);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_Adjust_distance);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_Adjust_rotation);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_Adjust_roll);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_Adjust);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_ChangeTo);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_SetShake);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", Decouple_AngleMoveToward);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CriticalDampValue);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CriticalDampPosition);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CriticalDampAngle);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_CalcZRotation);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_CalcRotation);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_CalcFSRotation);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_Relocate);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_SphereToSphereWithLines);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_CalcTilt);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_SetLookFocusAndBase);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_SetLookFocusAndDistance);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_LookProcess);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_Normalize);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_HandleTransitions);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_CalcFocusOffset);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_CalcFocusOffsetForSwim);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_CalcIntersectAngle);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_GetLineAngle);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_ACForcedMovement);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_update_dist_debounced);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_dampgetline);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_ACNoForcedMovement);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_AbsoluteCollision);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_update_z_damped);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_CombatCamDist);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_GenericCameraProcess);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_CinematicProcess);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_GetDistSq);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_NearestPointOnLineVec);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_CheckPoint);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_CheckIfPointOnLine);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_FindLinePoint);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_SplineGetNearestPoint2);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_SplineGetNearestPoint);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_SplineHelpMove);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", CAMERA_SplineProcess);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", func_8C0613C0);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", func_8C061480);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", func_8C061740);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", func_8C061860);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", func_8C061880);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", func_8C061940);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", func_8C0619A0);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", func_8C0619E0);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", func_8C061A20);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", func_8C061F00);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", func_8C062020);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", func_8C0620E0);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", func_8C062160);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", func_8C062180);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", func_8C062240);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", func_8C062320);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", func_8C062440);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", func_8C062540);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", func_8C062780);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", func_8C062980);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", func_8C062AA0);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", func_8C062AE0);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", func_8C062C80);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", func_8C062FA0);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", func_8C063060);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", func_8C063100);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", func_8C0632A0);
INCLUDE_ASM("asm/nonmatchings/Game/CAMERA", func_8C063860);
