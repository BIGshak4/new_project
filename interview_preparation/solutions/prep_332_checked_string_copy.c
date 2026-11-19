/* C11. Capacities describe readable/writable live storage.
   Returns false without changing destination for invalid capacity or missing NUL. */
#include <stdbool.h>
#include <stddef.h>
#include <string.h>

bool checked_string_copy(char *target, size_t target_capacity,
                         const char *source, size_t source_capacity) {
    if (target == NULL || source == NULL) return false;
    size_t length = 0;
    while (length < source_capacity && source[length] != '\0') ++length;
    if (length == source_capacity || length >= target_capacity) return false;
    memmove(target, source, length + 1);
    return true;
}
