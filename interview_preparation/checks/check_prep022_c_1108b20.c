#include <assert.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include "../solutions/prep_022_c_shuffle_1108b20.c"

static uint64_t state;
static unsigned calls;
static int raw_random(void) {
    state = state * UINT64_C(6364136223846793005) + 1;
    ++calls;
    return (int)(state % ((uint64_t)RAND_MAX + 1));
}
static int zero_draw(void) { ++calls; return 0; }
static int reject_once(void) { return ++calls == 1 ? RAND_MAX : 0; }

int main(void) {
    unsigned checks = 0;
    for (unsigned seed = 0; seed < 64; ++seed) {
        Shuffle100 bag;
        bool seen[101] = {false};
        shuffle100_init(&bag);
        state = seed;
        for (unsigned i = 0; i < 100; ++i) {
            int out = 0;
            assert(shuffle100_next_with(&bag, &out, raw_random));
            assert(out >= 1 && out <= 100 && !seen[out]);
            seen[out] = true;
            assert(bag.remaining == 99 - i);
            ++checks;
        }
        int unchanged = 777;
        assert(!shuffle100_next_with(&bag, &unchanged, raw_random));
        assert(unchanged == 777);
        ++checks;
    }
    calls = 0;
    assert(shuffle100_below(100, reject_once) == 0 && calls == 2);
    calls = 0;
    assert(shuffle100_below(1, zero_draw) == 0 && calls == 0);
    for (unsigned bound = 2; bound <= 100; ++bound) {
        unsigned limit = (unsigned)RAND_MAX - (unsigned)RAND_MAX % bound;
        assert(limit > 0 && limit % bound == 0 && limit <= (unsigned)RAND_MAX);
        ++checks;
    }
    Shuffle100 a, b;
    shuffle100_init(&a); shuffle100_init(&b);
    for (unsigned i = 0; i < 100; ++i) {
        int x, y;
        assert(shuffle100_next_with(&a, &x, zero_draw));
        assert(shuffle100_next_with(&b, &y, zero_draw));
        assert(x == y);
        ++checks;
    }
    checks += 2;
    printf("PREP-022 C11: %u checks passed\n", checks);
    return 0;
}
