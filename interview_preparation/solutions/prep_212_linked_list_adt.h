#ifndef PREP_212_LINKED_LIST_ADT_H
#define PREP_212_LINKED_LIST_ADT_H

#include <stdbool.h>
#include <stddef.h>

/* Opaque handles. Only this module changes links or ownership. */
typedef struct List List;
typedef struct Node Node;

/* Support API: a successful init returns an empty list; NULL = allocation failure. */
List *listInit(void);
void listDestroy(List *list); /* frees every owned node and the list; NULL is fine */
Node *createNode(int value);  /* detached on success; NULL = allocation failure */
bool destroyDetachedNode(Node *node); /* rejects owned nodes; NULL is harmless */

bool listContains(const List *list, int value); /* NULL list => false */
/* Valid positions are 0..length inclusive. Ownership transfers only on true.
   Failure never changes the list or the node. Insertion itself allocates nothing. */
bool insertNode(List *list, Node *node, size_t position);

/* Read-only support API, also used by the independent C test harness. */
size_t listLength(const List *list); /* NULL => 0 */
bool listGet(const List *list, size_t position, int *out_value);

#endif
