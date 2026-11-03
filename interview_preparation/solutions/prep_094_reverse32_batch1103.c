/* C99, unsigned exact-width patterns; no arrays or lookup tables. */
#include <stdint.h>

uint8_t reverse8_masks(uint8_t value) {
    uint32_t x = value;
    x = ((x >> 1) & UINT32_C(0x55)) | ((x & UINT32_C(0x55)) << 1);
    x = ((x >> 2) & UINT32_C(0x33)) | ((x & UINT32_C(0x33)) << 2);
    x = ((x >> 4) & UINT32_C(0x0F)) | ((x & UINT32_C(0x0F)) << 4);
    return (uint8_t)x;
}

uint32_t reverse32_masks(uint32_t x) {
    x = ((x >> 1) & UINT32_C(0x55555555)) | ((x & UINT32_C(0x55555555)) << 1);
    x = ((x >> 2) & UINT32_C(0x33333333)) | ((x & UINT32_C(0x33333333)) << 2);
    x = ((x >> 4) & UINT32_C(0x0F0F0F0F)) | ((x & UINT32_C(0x0F0F0F0F)) << 4);
    x = ((x >> 8) & UINT32_C(0x00FF00FF)) | ((x & UINT32_C(0x00FF00FF)) << 8);
    return (x >> 16) | (x << 16);
}
