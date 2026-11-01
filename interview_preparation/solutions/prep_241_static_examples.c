/* C17 illustrative source. No compiler execution is claimed by Python checks. */
static int file_private;

static int next_call(void) {
    static int calls;
    return ++calls;
}

int automatic_call(void) {
    int calls = 0;
    return ++calls;
}

int static_demonstration(void) {
    file_private = next_call();
    return next_call(); /* first invocation of this function returns 2 */
}
