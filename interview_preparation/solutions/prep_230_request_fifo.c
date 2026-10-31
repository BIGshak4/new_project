/* C99, single owner; caller supplies capacity valid int slots and distinct
 * control objects. Requests are snapshots passed by value. No allocation,
 * waiting or implicit ISR synchronization. Operations are WRITE then READ.
 */
#include <stdbool.h>
#include <stddef.h>

typedef struct {
    bool valid;
    bool wrote;
    bool read;
    int value; /* meaningful only when read is true */
} FifoResult;

FifoResult fifo_step(int *data, size_t capacity, size_t *read_head,
                     size_t *write_head, bool *is_full, bool *is_empty,
                     bool write_request, int write_value, bool read_request) {
    FifoResult result = {false, false, false, 0};
    if (!data || !read_head || !write_head || !is_full || !is_empty || capacity == 0)
        return result;
    if (*read_head >= capacity || *write_head >= capacity) return result;
    if (*read_head == *write_head ? (*is_full == *is_empty) : (*is_full || *is_empty))
        return result;
    result.valid = true;
    if (write_request && !*is_full) {
        data[*write_head] = write_value;
        *write_head = *write_head + 1 == capacity ? 0 : *write_head + 1;
        *is_empty = false;
        *is_full = *write_head == *read_head;
        result.wrote = true;
    }
    if (read_request && !*is_empty) {
        result.value = data[*read_head];
        *read_head = *read_head + 1 == capacity ? 0 : *read_head + 1;
        *is_full = false;
        *is_empty = *read_head == *write_head;
        result.read = true;
    }
    return result;
}
