/* C11. count must equal the number of following double arguments.
   The output pointer must address live writable double storage. */
#include <stdbool.h>
#include <stddef.h>
#include <stdarg.h>

bool sum_doubles(double *out, size_t count, ...) {
    if (out == NULL) return false;
    va_list values;
    va_start(values, count);
    double sum = 0.0;
    for (size_t i = 0; i < count; ++i) sum += va_arg(values, double);
    va_end(values);
    *out = sum;
    return true;
}

bool sum_doubles_forwarded(double *out, size_t count, va_list values) {
    if (out == NULL) return false;
    va_list copy;
    va_copy(copy, values);
    double sum = 0.0;
    for (size_t i = 0; i < count; ++i) sum += va_arg(copy, double);
    va_end(copy);
    *out = sum;
    return true;
}
