/* Independent C99 harness for the batch22 proposed C references.
 * Link with prep_223_ramp_memory.c and prep_151_uint32_popcount_batch22.c.
 * The RAM oracle constructs words by byte concatenation, and popcount by
 * testing all 32 bit positions rather than clearing the least set bit. */
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

extern bool check_ramp(bool little_endian, bool all_offsets);
extern unsigned count_ones(uint32_t x);

static bool device_little;
static bool device_all_offsets;
static int damaged_byte = -1;
static uint32_t damage_mask;
static unsigned read_calls;

int32_t read(unsigned address) {
    uint32_t bytes[4], word = 0;
    int32_t result;
    assert(address <= 252u);
    assert(device_all_offsets || address % 4u == 0u);
    for (unsigned j = 0; j < 4u; ++j) {
        bytes[j] = address + j;
        if ((int)(address + j) == damaged_byte) bytes[j] ^= damage_mask;
    }
    for (unsigned j = 0; j < 4u; ++j) {
        const unsigned index = device_little ? 3u - j : j;
        word = word * UINT32_C(256) + bytes[index];
    }
    memcpy(&result, &word, sizeof result);
    ++read_calls;
    return result;
}

static unsigned oracle_popcount(uint32_t x) {
    unsigned result = 0;
    for (unsigned bit = 0; bit < 32u; ++bit) result += (x >> bit) & 1u;
    return result;
}

int main(void) {
    unsigned memory_cases = 0, popcount_cases = 0;
    for (unsigned le = 0; le < 2u; ++le) {
        for (unsigned offsets = 0; offsets < 2u; ++offsets) {
            device_little = le != 0u;
            device_all_offsets = offsets != 0u;
            damaged_byte = -1;
            read_calls = 0;
            assert(check_ramp(device_little, device_all_offsets));
            assert(read_calls == (offsets ? 253u : 64u));
            ++memory_cases;
            for (unsigned byte = 0; byte < 256u; ++byte) {
                for (unsigned bit = 0; bit < 8u; ++bit) {
                    damaged_byte = (int)byte;
                    damage_mask = UINT32_C(1) << bit;
                    assert(!check_ramp(device_little, device_all_offsets));
                    ++memory_cases;
                }
            }
        }
    }
    for (uint32_t x = 0; x < UINT32_C(65536); ++x) {
        assert(count_ones(x) == oracle_popcount(x));
        ++popcount_cases;
    }
    for (unsigned bit = 0; bit < 32u; ++bit) {
        const uint32_t x = UINT32_C(1) << bit;
        assert(count_ones(x) == 1u);
        assert(count_ones(~x) == 31u);
        popcount_cases += 2u;
    }
    assert(count_ones(UINT32_MAX) == 32u);
    ++popcount_cases;
    uint32_t random_state = UINT32_C(0xBADC0FFE);
    for (unsigned i = 0; i < 20000u; ++i) {
        random_state = random_state * UINT32_C(1664525) + UINT32_C(1013904223);
        assert(count_ones(random_state) == oracle_popcount(random_state));
        ++popcount_cases;
    }
    printf("{\"passed\":true,\"memory_cases\":%u,\"popcount_cases\":%u}\n",
           memory_cases, popcount_cases);
    return 0;
}
