/* C11 shuffle bag. Initialize once, then call next at most 100 times. */
#include <stdbool.h>
#include <stdlib.h>

typedef struct {
    int values[100];
    unsigned remaining;
} Shuffle100;

typedef int (*ShuffleDraw)(void);

void shuffle100_init(Shuffle100 *bag) {
    for (unsigned i = 0; i < 100; ++i) bag->values[i] = (int)i + 1;
    bag->remaining = 100;
}

/* draw has the rand() range 0..RAND_MAX; uniformity is a stated assumption,
   not a guarantee that the C standard's pseudorandom sequence is independent. */
static unsigned shuffle100_below(unsigned bound, ShuffleDraw draw) {
    if (bound == 1) return 0;
    const unsigned limit = (unsigned)RAND_MAX - (unsigned)RAND_MAX % bound;
    unsigned value;
    do {
        value = (unsigned)draw();
    } while (value >= limit);
    return value % bound;
}

bool shuffle100_next_with(Shuffle100 *bag, int *out, ShuffleDraw draw) {
    if (bag == NULL || out == NULL || draw == NULL || bag->remaining > 100
            || bag->remaining == 0) return false;
    const unsigned index = shuffle100_below(bag->remaining, draw);
    *out = bag->values[index];
    bag->values[index] = bag->values[--bag->remaining];
    return true;
}

bool shuffle100_next(Shuffle100 *bag, int *out) {
    return shuffle100_next_with(bag, out, rand);
}
