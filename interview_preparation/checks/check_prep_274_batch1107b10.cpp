#include "prep_274_constructor_batch1107b10.hpp"
#include <cassert>
#include <cstdint>
#include <iostream>
#include <limits>
#include <stdexcept>

int main() {
    Range initial;
    assert(initial.low() == 0 && initial.high() == 0 && initial.span() == 0);
    unsigned cases = 1;
    for (std::int32_t lo = -12; lo <= 12; ++lo) {
        for (std::int32_t hi = -12; hi <= 12; ++hi) {
            bool threw = false;
            try {
                Range value(lo, hi);
                assert(lo <= hi);
                assert(value.low() == lo && value.high() == hi);
                assert(value.span() == static_cast<std::int64_t>(hi) - lo);
                Range copied(value); // Initialization of a new object.
                assert(copied.low() == lo && copied.high() == hi);
                Range assigned;
                assigned = copied; // Assignment of an already existing object.
                assert(assigned.span() == copied.span());
            } catch (const std::invalid_argument&) {
                threw = true;
            }
            assert(threw == (lo > hi));
            ++cases;
        }
    }
    Range bounds(std::numeric_limits<std::int32_t>::min(),
                 std::numeric_limits<std::int32_t>::max());
    assert(bounds.span() == INT64_C(4294967295));
    std::cout << "PREP-274: " << cases + 1
              << " constructor/copy/assignment/boundary cases passed\n";
}
