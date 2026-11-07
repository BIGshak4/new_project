#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include "../solutions/prep_281_spinlock_batch1107b20.h"
#include "../solutions/prep_285_decimal_reverse_batch1107b20.c"

static prep281_lock lock = PREP281_LOCK_INITIALIZER;
static unsigned counter = 0;
static void *worker(void *unused) {
    (void)unused;
    for (unsigned i = 0; i < 25000; ++i) {
        prep281_lock_acquire(&lock);
        ++counter;
        prep281_lock_release(&lock);
    }
    return NULL;
}
int main(void) {
    pthread_t threads[4];
    for (unsigned i = 0; i < 4; ++i)
        if (pthread_create(&threads[i], NULL, worker, NULL) != 0) return 2;
    for (unsigned i = 0; i < 4; ++i)
        if (pthread_join(threads[i], NULL) != 0) return 3;
    if (counter != 100000) return 4;
    const int32_t input[] = {0, 120, -120, 12345, INT32_MIN, INT32_MAX, 1463847412, -1463847412};
    const int32_t expected[] = {0, 21, -21, 54321, 0, 0, 2147483641, -2147483641};
    for (unsigned i = 0; i < sizeof input / sizeof *input; ++i)
        if (reverse_int32_c(input[i]) != expected[i]) return 5;
    puts("PASS: 100000 protected increments across four pthreads; 8 int32 reversal boundary cases.");
    return 0;
}
