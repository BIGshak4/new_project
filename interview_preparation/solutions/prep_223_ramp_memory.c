/* Proposed C99 reference; requires a platform contract for endian/alignment.
 * The supplied read() returns the bits of a 32-bit word in int32_t form.
 * This source was not compiled in the local Python verification run. */
#include <stdint.h>
#include <stdbool.h>

extern int32_t read(unsigned address);

bool check_ramp(bool little_endian, bool all_offsets) {
    const unsigned stride = all_offsets ? 1u : 4u;
    for (unsigned a = 0; a <= 252u; a += stride) {
        uint32_t expected = 0;
        for (unsigned j = 0; j < 4u; ++j) {
            unsigned shift = little_endian ? 8u * j : 8u * (3u - j);
            expected |= (uint32_t)(a + j) << shift;
        }
        if ((uint32_t)read(a) != expected) return false;
    }
    return true;
}
