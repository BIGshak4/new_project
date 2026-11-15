/* C11. node and its successor are live heap-owned nodes. No aliases to removed node.
   The copied payload is int, so value assignment has constant cost. */
#include <stdbool.h>
#include <stdlib.h>

struct Node {
    int value;
    struct Node *next;
};

bool delete_given(struct Node *node) {
    if (node == NULL || node->next == NULL) return false;
    struct Node *removed = node->next;
    node->value = removed->value;
    node->next = removed->next;
    free(removed);
    return true;
}
