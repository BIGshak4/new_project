/* C11 threads. A counting semaphore is described separately in the solution. */
#include <threads.h>

static mtx_t lock;
static unsigned counter;

int increment_counter(void *unused) {
    (void)unused;
    if (mtx_lock(&lock) != thrd_success) return -1;
    ++counter;
    if (mtx_unlock(&lock) != thrd_success) return -1;
    return 0;
}

int mutex_demo(void) {
    thrd_t worker;
    if (mtx_init(&lock, mtx_plain) != thrd_success) return -1;
    counter = 0;
    if (thrd_create(&worker, increment_counter, NULL) != thrd_success) {
        mtx_destroy(&lock);
        return -1;
    }
    int result;
    int status = thrd_join(worker, &result);
    if (status != thrd_success) return -1;
    mtx_destroy(&lock);
    return status == thrd_success && result == 0 && counter == 1 ? 0 : -1;
}
