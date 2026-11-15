/* C11. Readable int32_t array, count known. No arithmetic multiplication. */
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <limits.h>

static bool add_shift_product(uint64_t a, uint64_t b, uint64_t limit, uint64_t *out) {
    uint64_t sum = 0;
    while (b != 0) {
        if ((b & UINT64_C(1)) != 0) {
            if (a > limit - sum) return false;
            sum += a;
        }
        b >>= 1;
        if (b != 0) {
            if (a > limit - a) return false;
            a += a;
        }
    }
    *out = sum;
    return true;
}

bool array_product(const int32_t *values, size_t count, int64_t *out) {
    if (out == NULL || (count != 0 && values == NULL)) return false;
    bool negative = false;
    bool has_zero = false;
    for (size_t i = 0; i < count; ++i) {
        if (values[i] == 0) has_zero = true;
        if (values[i] < 0) negative = !negative;
    }
    if (has_zero) { *out = 0; return true; }
    uint64_t limit = negative ? (UINT64_C(1) << 63) : (uint64_t)INT64_MAX;
    uint64_t result = 1;
    for (size_t i = 0; i < count; ++i) {
        int64_t x = values[i];
        uint64_t magnitude = x < 0 ? (uint64_t)(-x) : (uint64_t)x;
        if (!add_shift_product(result, magnitude, limit, &result)) return false;
    }
    if (!negative) *out = (int64_t)result;
    else if (result == (UINT64_C(1) << 63)) *out = INT64_MIN;
    else *out = -(int64_t)result;
    return true;
}
