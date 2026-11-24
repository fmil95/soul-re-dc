#ifndef _COMMON_H_
#define _COMMON_H_

/*
 * Dreamcast (SH4, KATANA gcc 2.9-SYSDEV) version of soul-re's include/common.h.
 * Differences from PSX: varargs come from the compiler's <stdarg.h> (the SH ABI passes them in registers),
 * and the MIPS GTE macros (Libs/GTE.h) are not included.
 */

typedef unsigned long uintptr_t;
typedef long intptr_t;
typedef unsigned int size_t; /* __SIZE_TYPE__ on sh-elf */
typedef unsigned long u_long;
typedef unsigned short u_short;
typedef unsigned char u_char;

#ifndef NULL
#define NULL (void *)0
#endif

#include <stdarg.h>
#include "Libs/STRING.h"

#include "include_asm.h"

#include "Game/TYPES.h"
#include "Game/EXTRA.h"
#include "Libs/SDK.h"

#define ARRAY_COUNT(arr) (sizeof(arr) / sizeof(arr[0]))

#define EXTERN extern
#define STATIC

#endif
