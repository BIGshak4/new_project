#include "prep_212_linked_list_adt.h"

#include <stdint.h>
#include <stdlib.h>

#ifndef LIST_MALLOC
#define LIST_MALLOC malloc
#endif
#ifndef LIST_FREE
#define LIST_FREE free
#endif

struct Node {
    int value;
    struct Node *next;
    struct List *owner;
};

struct List {
    Node *head;
    size_t length;
};

List *listInit(void) {
    List *list = LIST_MALLOC(sizeof *list);
    if (list == NULL) return NULL;
    list->head = NULL;
    list->length = 0;
    return list;
}

Node *createNode(int value) {
    Node *node = LIST_MALLOC(sizeof *node);
    if (node == NULL) return NULL;
    node->value = value;
    node->next = NULL;
    node->owner = NULL;
    return node;
}

bool destroyDetachedNode(Node *node) {
    if (node == NULL) return true;
    if (node->owner != NULL) return false;
    LIST_FREE(node);
    return true;
}

bool listContains(const List *list, int value) {
    if (list == NULL) return false;
    for (const Node *node = list->head; node != NULL; node = node->next) {
        if (node->value == value) return true;
    }
    return false;
}

bool insertNode(List *list, Node *node, size_t position) {
    if (list == NULL || node == NULL || node->owner != NULL ||
        node->next != NULL || position > list->length || list->length == SIZE_MAX) {
        return false;
    }
    Node **link = &list->head;
    for (size_t i = 0; i < position; ++i) link = &(*link)->next;
    node->next = *link;
    node->owner = list;
    *link = node;
    ++list->length;
    return true;
}

size_t listLength(const List *list) {
    return list == NULL ? 0 : list->length;
}

bool listGet(const List *list, size_t position, int *out_value) {
    if (list == NULL || out_value == NULL || position >= list->length) return false;
    const Node *node = list->head;
    for (size_t i = 0; i < position; ++i) node = node->next;
    *out_value = node->value;
    return true;
}

void listDestroy(List *list) {
    if (list == NULL) return;
    Node *node = list->head;
    while (node != NULL) {
        Node *next = node->next;
        LIST_FREE(node);
        node = next;
    }
    LIST_FREE(list);
}
