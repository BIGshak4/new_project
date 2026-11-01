// C++17 illustrative source. Static is not a synchronization primitive.
struct Counter {
    inline static int total = 0;
    int local = 0;
    void add() { ++total; ++local; }
    static int shared() { return total; } // no this pointer
};

int call_count() {
    static int value = 0;
    return ++value;
}
