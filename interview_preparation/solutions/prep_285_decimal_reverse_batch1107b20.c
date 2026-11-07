#include <stdint.h>

/* int64_t can represent the magnitude of every int32_t, including INT32_MIN. */
int32_t reverse_int32_c(int32_t input) {
    int64_t n = input;
    const int negative = n < 0;
    if (negative) n = -n;
    const int64_t limit = negative ? INT64_C(2147483648) : INT64_C(2147483647);
    int64_t result = 0;
    while (n != 0) {
        const int64_t digit = n % 10;
        n /= 10;
        if (result > (limit - digit) / 10) return 0;
        result = result * 10 + digit;
    }
    return (int32_t)(negative ? -result : result);
}
