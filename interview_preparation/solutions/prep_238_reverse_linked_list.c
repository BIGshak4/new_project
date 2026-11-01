/* C99: valid acyclic chain, exclusive mutation, no node allocation/free. */
#include <stddef.h>
typedef struct ReverseNode { int value; struct ReverseNode *next; } ReverseNode;
ReverseNode *reverse_list(ReverseNode *head) {
    ReverseNode *previous = NULL;
    while (head) {
        ReverseNode *successor = head->next;
        head->next = previous;
        previous = head;
        head = successor;
    }
    return previous;
}
