#include <stdint.h>

/* Precondition: uint32_t is available. No signed arithmetic or overflow. */
uint32_t different_uint32(uint32_t a, uint32_t b) {
    return ((~a) & UINT32_C(1)) | ((~b) & UINT32_C(2));
}
