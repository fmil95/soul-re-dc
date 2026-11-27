#include "Game/LIST.h"

void LIST_InsertFunc(NodeType *list, NodeType *node)
{
    node->prev = list;
    node->next = list->next;

    if (list->next != NULL)
    {
        list->next->prev = node;
    }

    list->next = node;
}

INCLUDE_ASM("asm/nonmatchings/Game/LIST", LIST_DeleteFunc);

NodeType *LIST_GetFunc(NodeType *list)
{
    NodeType *next; // not from PS1 SYM

    next = list->next;

    if (next != NULL)
    {
        LIST_DeleteFunc(next);

        return next;
    }

    return NULL;
}

INCLUDE_ASM("asm/nonmatchings/Game/LIST", func_8C08F5E0);
INCLUDE_ASM("asm/nonmatchings/Game/LIST", func_8C08F620);
INCLUDE_ASM("asm/nonmatchings/Game/LIST", func_8C08F6A0);
INCLUDE_ASM("asm/nonmatchings/Game/LIST", func_8C08F6C0);
INCLUDE_ASM("asm/nonmatchings/Game/LIST", func_8C08F720);
INCLUDE_ASM("asm/nonmatchings/Game/LIST", func_8C08F740);
