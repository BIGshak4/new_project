/* C99 or later. A binary text representation, not decimal digits in an int.
 * out must designate at least capacity writable bytes when non-NULL.
 * Returns false without writing if out is NULL or capacity is too small.
 * On success, writes the shortest representation plus a terminating NUL.
 */
#include <stdbool.h>
#include <stddef.h>

bool unsigned_to_binary(unsigned int value, char *out, size_t capacity)
{
    unsigned int probe = value;
    size_t digits = 1;
    size_t i;

    while ((probe >>= 1) != 0u) {
        ++digits;
    }
    if (out == NULL || capacity <= digits) {
        return false;
    }
    out[digits] = '\0';
    i = digits;
    do {
        out[--i] = (char)('0' + (value & 1u));
        value >>= 1;
    } while (i != 0);
    return true;
}
