/* Significant-bit reversal, not fixed-eight-bit reversal. C99 uint32_t. */
#include <stdint.h>
uint32_t reverse_significant(uint32_t n) {
    uint32_t out = 0;
    while (n != 0) {
        out = (out << 1) | (n & UINT32_C(1));
        n >>= 1;
    }
    return out;
}
