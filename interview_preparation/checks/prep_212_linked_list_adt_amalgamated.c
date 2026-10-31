/* Generated exact include expansion of public header, implementation and harness. */
/* Compile this translation unit alone. It includes the implementation with
   deterministic allocation failure injection. Observations use public APIs. */
#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>

static long live_blocks = 0;
static long allocations = 0;
static long fail_after = -1;

static void *checked_malloc(size_t size) {
    ++allocations;
    if (fail_after == 0) return NULL;
    if (fail_after > 0) --fail_after;
    void *result = malloc(size);
    if (result != NULL) ++live_blocks;
    return result;
}

static void checked_free(void *ptr) {
    if (ptr != NULL) --live_blocks;
    assert(live_blocks >= 0);
    free(ptr);
}

#define LIST_MALLOC checked_malloc
#define LIST_FREE checked_free
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


static unsigned checks = 0;
#define CHECK(condition) do { assert(condition); ++checks; } while (0)

static void check_sequence(const List *list, const int *values, size_t length) {
    CHECK(listLength(list) == length);
    for (size_t i = 0; i < length; ++i) {
        int value = 0;
        CHECK(listGet(list, i, &value));
        CHECK(value == values[i]);
        CHECK(listContains(list, values[i]));
    }
    int unchanged = 718;
    CHECK(!listGet(list, length, &unchanged));
    CHECK(unchanged == 718);
    CHECK(!listContains(list, INT_MIN));
}

int main(void) {
    CHECK(listLength(NULL) == 0);
    CHECK(!listContains(NULL, 0));
    CHECK(!listGet(NULL, 0, NULL));
    CHECK(destroyDetachedNode(NULL));
    listDestroy(NULL);

    /* Every insertion point for initial lengths 0..8, plus out-of-range. */
    unsigned scenarios = 0;
    for (size_t length = 0; length <= 8; ++length) {
        for (size_t position = 0; position <= length + 1; ++position) {
            List *list = listInit();
            List *other = listInit();
            CHECK(list != NULL && other != NULL);
            int original[10], expected[10];
            Node *tail = NULL;
            for (size_t i = 0; i < length; ++i) {
                original[i] = (int)i - 4;
                tail = createNode(original[i]);
                CHECK(tail != NULL && insertNode(list, tail, i));
            }
            Node *extra = createNode(99);
            CHECK(extra != NULL);
            CHECK(!insertNode(NULL, extra, 0));
            CHECK(!insertNode(list, NULL, 0));
            CHECK(!listGet(list, 0, NULL));
            if (tail != NULL) {
                /* Tail's next is NULL, but its owner must still reject aliasing. */
                CHECK(!insertNode(list, tail, 0));
                CHECK(!insertNode(other, tail, 0));
                CHECK(!destroyDetachedNode(tail));
            }
            const long allocation_snapshot = allocations;
            if (position <= length) {
                fail_after = 0; /* insert must not allocate at all */
                CHECK(insertNode(list, extra, position));
                fail_after = -1;
                CHECK(allocations == allocation_snapshot);
                for (size_t i = 0; i < position; ++i) expected[i] = original[i];
                expected[position] = 99;
                for (size_t i = position; i < length; ++i) expected[i + 1] = original[i];
                check_sequence(list, expected, length + 1);
                CHECK(!insertNode(other, extra, 0));
                CHECK(!insertNode(list, extra, 0));
                CHECK(!destroyDetachedNode(extra));
            } else {
                CHECK(!insertNode(list, extra, position));
                CHECK(allocations == allocation_snapshot);
                check_sequence(list, original, length);
                /* Rejected node stayed detached and can transfer elsewhere. */
                CHECK(insertNode(other, extra, 0));
                int one[] = {99};
                check_sequence(other, one, 1);
            }
            listDestroy(list);
            listDestroy(other);
            CHECK(live_blocks == 0);
            ++scenarios;
        }
    }

    /* Inject failures into both allocating public operations. */
    fail_after = 0;
    CHECK(listInit() == NULL);
    CHECK(createNode(7) == NULL);
    CHECK(live_blocks == 0);
    fail_after = -1;
    List *list = listInit();
    Node *node = createNode(INT_MIN);
    CHECK(list != NULL && node != NULL && insertNode(list, node, 0));
    fail_after = 0;
    Node *failed = createNode(9);
    CHECK(failed == NULL);
    CHECK(!insertNode(list, failed, 0));
    CHECK(listLength(list) == 1 && listContains(list, INT_MIN));
    int value = 0;
    CHECK(listGet(list, 0, &value) && value == INT_MIN);
    fail_after = -1;
    Node *detached = createNode(INT_MAX);
    CHECK(detached != NULL && destroyDetachedNode(detached));
    listDestroy(list);
    CHECK(live_blocks == 0);
    printf("{\"passed\":true,\"insertion_scenarios\":%u,\"assertions\":%u,"
           "\"allocation_failure_injected\":true,\"live_blocks_at_exit\":%ld}\n",
           scenarios, checks, live_blocks);
    return 0;
}
