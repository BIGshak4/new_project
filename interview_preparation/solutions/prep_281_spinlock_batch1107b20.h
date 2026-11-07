#ifndef JOBRUN_PREP281_SPINLOCK_H
#define JOBRUN_PREP281_SPINLOCK_H
#include <stdatomic.h>

typedef struct { atomic_flag flag; } prep281_lock;
#define PREP281_LOCK_INITIALIZER { ATOMIC_FLAG_INIT }

static inline void prep281_lock_acquire(prep281_lock *lock) {
    /* TestAndSet is atomic and returns the previous value. */
    while (atomic_flag_test_and_set_explicit(&lock->flag, memory_order_acquire)) {
        /* Busy wait; no fairness or bounded waiting is promised. */
    }
}

static inline void prep281_lock_release(prep281_lock *lock) {
    atomic_flag_clear_explicit(&lock->flag, memory_order_release);
}
#endif
