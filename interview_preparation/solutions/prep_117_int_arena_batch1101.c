/* C99: fixed ONE-int allocations. Existing int array; only persistent
 * external management state is int *free_head. Constant temporary locals and
 * known arena base/length are permitted. Free cells store next INDICES, never
 * truncated pointers; allocated cells may contain any int.
 */
#include <limits.h>
#include <stdbool.h>
#include <stddef.h>

bool arena_init(int *base, size_t cells, int **free_head) {
    if (!free_head || (cells && !base) || cells > (size_t)INT_MAX) return false;
    for (size_t i = 0; i < cells; ++i) base[i] = i + 1 < cells ? (int)(i + 1) : -1;
    *free_head = cells ? base : NULL;
    return true;
}

int *arena_alloc(int *base, int **free_head) {
    /* Valid descriptor/free-list assumed after init and valid frees. */
    if (!*free_head) return NULL;
    int *slot = *free_head;
    int next_index = *slot;
    *free_head = next_index == -1 ? NULL : base + next_index;
    return slot;
}

void arena_free(int *base, int **free_head, int *slot) {
    /* slot must be a currently allocated cell of this arena. No stale,
     * double or foreign free is accepted by the caller contract. */
    *slot = *free_head ? (int)(*free_head - base) : -1;
    *free_head = slot;
}
