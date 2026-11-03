/* C99. Live caller-owned malloc nodes, int payload, serialized mutation.
 * Exact removal frees the supplied node; logical removal frees its successor.
 * NULL is accepted as a failure. Dangling pointers cannot be validated here. */
#include <stdbool.h>
#include <stddef.h>
#include <stdlib.h>
#ifndef NODE_FREE
#define NODE_FREE free
#endif

typedef struct DeleteNode { int value; struct DeleteNode *next; } DeleteNode;

bool remove_node(DeleteNode **head, DeleteNode *target) {
    DeleteNode **link;
    if (head == NULL || target == NULL) return false;
    link = head;
    while (*link != NULL && *link != target) link = &(*link)->next;
    if (*link == NULL) return false;
    *link = target->next;
    NODE_FREE(target);
    return true;
}

bool remove_value_at_non_tail(DeleteNode *target) {
    DeleteNode *successor;
    if (target == NULL || target->next == NULL) return false;
    successor = target->next;
    target->value = successor->value;
    target->next = successor->next;
    NODE_FREE(successor);
    return true;
}
