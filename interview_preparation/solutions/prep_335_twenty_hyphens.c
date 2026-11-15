/* C11. Each loop starts with fresh int i and n=20. */
#include <stdio.h>

int main(void) {
    int i, n = 20;
    for (i = 0; -i < n; --i) { printf("-"); }
    putchar('\n');
    n = 20;
    for (i = 0; i + n; --i) { printf("-"); }
    putchar('\n');
    n = 20;
    for (i = 0; i < n; --n) { printf("-"); }
    putchar('\n');
    return 0;
}
