/* C99+; requires a target providing the exact-width uint8_t type.
 * Input is already an unsigned byte; integer-to-uint8_t caller conversion
 * is not rejection of an out-of-domain original integer.
 * No arrays, lookup tables, strings or signed shifts are used.
 */
#include <stdint.h>

uint8_t reverse_byte_loop(uint8_t value)
{
    uint8_t result = 0;
    for (unsigned i = 0; i < 8; ++i) {
        result = (uint8_t)(((unsigned)result << 1) | ((unsigned)value & 1u));
        value = (uint8_t)((unsigned)value >> 1);
    }
    return result;
}

uint8_t reverse_byte_masks(uint8_t value)
{
    unsigned x = value;
    x = ((x & 0x55u) << 1) | ((x >> 1) & 0x55u);
    x = ((x & 0x33u) << 2) | ((x >> 2) & 0x33u);
    x = ((x & 0x0Fu) << 4) | ((x >> 4) & 0x0Fu);
    return (uint8_t)x;
}
