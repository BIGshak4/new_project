/* Compile as C99. References are included without modifying their sources. */
#include "../solutions/prep_230_request_fifo.c"
#include "../solutions/prep_094_significant_bits_batch22.c"
#include "../solutions/prep_160_uppercase_counting_batch22.c"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

static unsigned long assertions = 0, fifo_traces = 0;
#define CHECK(x) do { ++assertions; if (!(x)) { fprintf(stderr,"failed:%d\n",__LINE__); exit(1); } } while (0)

static void check_fifo(void) {
    for (size_t capacity = 1; capacity <= 4; ++capacity) {
        unsigned histories = 1;
        for (unsigned length = 0; length <= 6; ++length, histories *= 4) {
            for (unsigned encoding = 0; encoding < histories; ++encoding) {
                int data[4] = {0}, oracle[4] = {0};
                size_t read_head = 0, write_head = 0, count = 0, writes = 0, reads = 0;
                bool full = false, empty = true;
                unsigned digits = encoding;
                for (unsigned step = 0; step < length; ++step) {
                    unsigned code = digits % 4; digits /= 4;
                    bool wr = (code & 1) != 0, rr = (code & 2) != 0;
                    int value = (int)(step % 3) - 1, expected_value = 0;
                    bool wrote = wr && count < capacity;
                    if (wrote) { oracle[count++] = value; ++writes; }
                    bool read = rr && count != 0;
                    if (read) {
                        expected_value = oracle[0];
                        for (size_t i = 1; i < count; ++i) oracle[i - 1] = oracle[i];
                        --count; ++reads;
                    }
                    FifoResult result = fifo_step(data, capacity, &read_head, &write_head,
                                                 &full, &empty, wr, value, rr);
                    CHECK(result.valid && result.wrote == wrote && result.read == read);
                    if (read) CHECK(result.value == expected_value);
                    CHECK(read_head == reads % capacity && write_head == writes % capacity);
                    CHECK(full == (count == capacity) && empty == (count == 0));
                    for (size_t i = 0; i < count; ++i)
                        CHECK(data[(read_head + i) % capacity] == oracle[i]);
                }
                ++fifo_traces;
            }
        }
    }
    int data[2] = {7, 8}; size_t r = 0, w = 0; bool full = false, empty = true;
    CHECK(!fifo_step(data, 0, &r, &w, &full, &empty, true, 9, true).valid);
    CHECK(data[0] == 7 && data[1] == 8 && r == 0 && w == 0 && !full && empty);
    empty = false;
    CHECK(!fifo_step(data, 2, &r, &w, &full, &empty, true, 9, true).valid);
    empty = true; r = 2;
    CHECK(!fifo_step(data, 2, &r, &w, &full, &empty, true, 9, true).valid);
}

static uint32_t reversal_oracle(uint32_t value) {
    unsigned width = 0;
    for (uint32_t copy = value; copy; copy /= 2) ++width;
    uint32_t result = 0;
    for (unsigned i = 0; i < width; ++i)
        if (value & (UINT32_C(1) << i)) result |= UINT32_C(1) << (width - 1 - i);
    return result;
}

static int compare_char(const void *a, const void *b) {
    return (int)*(const unsigned char *)a - (int)*(const unsigned char *)b;
}

int main(void) {
    check_fifo();
    for (uint32_t value = 0; value < UINT32_C(65536); ++value)
        CHECK(reverse_significant(value) == reversal_oracle(value));
    const uint32_t wide[] = {UINT32_C(0x80000000), UINT32_C(0xffffffff), UINT32_C(0x80000001)};
    for (size_t i = 0; i < sizeof wide / sizeof wide[0]; ++i)
        CHECK(reverse_significant(wide[i]) == reversal_oracle(wide[i]));
    unsigned strings = 1, sort_cases = 0;
    const char alphabet[] = "AMZ";
    for (size_t length = 0; length <= 8; ++length, strings *= 3) {
        for (unsigned encoding = 0; encoding < strings; ++encoding) {
            char actual[8], expected[8]; unsigned digits = encoding;
            for (size_t i = 0; i < length; ++i) { actual[i] = alphabet[digits % 3]; digits /= 3; }
            memcpy(expected, actual, length); qsort(expected, length, 1, compare_char);
            CHECK(sort_uppercase(actual, length));
            CHECK(memcmp(actual, expected, length) == 0); ++sort_cases;
        }
    }
    char thousand[1000], expected[1000];
    for (size_t i = 0; i < 1000; ++i) thousand[i] = (char)('A' + (i * 19 + 7) % 26);
    memcpy(expected, thousand, 1000); qsort(expected, 1000, 1, compare_char);
    CHECK(sort_uppercase(thousand, 1000) && memcmp(thousand, expected, 1000) == 0); ++sort_cases;
    char invalid[] = "ZAaM"; CHECK(!sort_uppercase(invalid, 4) && strcmp(invalid, "ZAaM") == 0); ++sort_cases;
    CHECK(sort_uppercase(NULL, 0)); CHECK(!sort_uppercase(NULL, 1));
    printf("{\"passed\":true,\"fifo_traces\":%lu,\"reversal_cases\":65539,\"sort_cases\":%u,\"assertions\":%lu}\n",
           fifo_traces, sort_cases, assertions);
    return 0;
}
