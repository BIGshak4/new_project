/* Include beside staged solutions as laid out in the repository. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include "../solutions/prep_094_reverse32_batch1103.c"
static size_t live_blocks, frees, assertions;
static void tracked_free(void *p) { assert(p != NULL && live_blocks > 0); --live_blocks; ++frees; free(p); }
#define NODE_FREE tracked_free
#include "../solutions/prep_238_delete_batch1103.c"
#define CHECK(c) do { ++assertions; assert(c); } while (0)

static uint32_t oracle(uint32_t value, unsigned width) {
    uint32_t result = 0;
    unsigned i;
    for (i = 0; i < width; ++i) { result = (result << 1) | (value & 1U); value >>= 1; }
    return result;
}
static DeleteNode *make_list(size_t n, DeleteNode **nodes) {
    size_t i;
    for (i = 0; i < n; ++i) {
        nodes[i] = malloc(sizeof *nodes[i]); CHECK(nodes[i] != NULL); ++live_blocks;
        nodes[i]->value = (int)i; nodes[i]->next = NULL;
        if (i) nodes[i-1]->next = nodes[i];
    }
    return n ? nodes[0] : NULL;
}
static void destroy(DeleteNode *head) {
    while (head) { DeleteNode *next = head->next; tracked_free(head); head = next; }
}
int main(void) {
    uint32_t x = UINT32_C(0x12345678);
    unsigned i;
    size_t n, index, list_cases = 0, word_cases = 0;
    for (i = 0; i < 256; ++i) { CHECK(reverse8_masks((uint8_t)i) == oracle(i, 8)); ++word_cases; }
    for (i = 0; i < 65536; ++i) {
        uint32_t v = (uint32_t)i | ((uint32_t)(i ^ 0xA55AU) << 16);
        CHECK(reverse32_masks(v) == oracle(v, 32));
        CHECK(reverse32_masks(reverse32_masks(v)) == v); ++word_cases;
    }
    for (i = 0; i < 100000; ++i) {
        x = x * UINT32_C(1664525) + UINT32_C(1013904223);
        CHECK(reverse32_masks(x) == oracle(x, 32)); ++word_cases;
    }
    CHECK(reverse32_masks(0) == 0); CHECK(reverse32_masks(UINT32_MAX) == UINT32_MAX);
    for (i = 0; i < 32; ++i) CHECK(reverse32_masks(UINT32_C(1) << i) == (UINT32_C(1) << (31-i)));
    for (n = 1; n <= 12; ++n) for (index = 0; index < n; ++index) {
        DeleteNode *nodes[12], *head = make_list(n, nodes), *cur;
        size_t j, old_frees = frees;
        CHECK(remove_node(&head, nodes[index])); CHECK(frees == old_frees + 1);
        cur = head;
        for (j = 0; j < n; ++j) if (j != index) { CHECK(cur == nodes[j]); CHECK(cur->value == (int)j); cur = cur->next; }
        CHECK(cur == NULL); destroy(head); CHECK(live_blocks == 0); ++list_cases;
        head = make_list(n, nodes); old_frees = frees;
        if (index == n - 1) { CHECK(!remove_value_at_non_tail(nodes[index])); CHECK(frees == old_frees); }
        else {
            CHECK(remove_value_at_non_tail(nodes[index])); CHECK(frees == old_frees + 1);
            CHECK(nodes[index]->value == (int)index + 1);
            CHECK(nodes[index]->next == (index + 2 < n ? nodes[index+2] : NULL));
        }
        destroy(head); CHECK(live_blocks == 0); ++list_cases;
    }
    {
        DeleteNode *head = NULL, foreign = {99, NULL};
        CHECK(!remove_node(NULL, &foreign)); CHECK(!remove_node(&head, &foreign));
        CHECK(!remove_node(&head, NULL)); CHECK(!remove_value_at_non_tail(NULL));
    }
    CHECK(live_blocks == 0);
    printf("{\"passed\":true,\"word_cases\":%zu,\"list_cases\":%zu,\"assertions\":%zu,\"live_blocks\":%zu}\n", word_cases, list_cases, assertions, live_blocks);
    return 0;
}
