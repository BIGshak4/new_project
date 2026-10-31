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
#include "../solutions/prep_212_linked_list_adt.c"

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
