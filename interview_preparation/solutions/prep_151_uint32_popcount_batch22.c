/* Proposed C99, not compiled in the local Python model checks. */
#include <stdint.h>

unsigned count_ones(uint32_t x) {
    unsigned count = 0;
    while (x != 0u) {
        x &= x - 1u;
        ++count;
    }
    return count;
}
