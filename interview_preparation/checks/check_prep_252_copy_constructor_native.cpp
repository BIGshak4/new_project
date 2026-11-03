// Self-contained compile input: append this file after prep_252_copy_constructor.cpp.
#include <cassert>
#include <iostream>
#include <type_traits>

int main() {
    static_assert(std::is_copy_constructible<OwnedInts>::value, "copy required");
    static_assert(std::is_nothrow_move_constructible<OwnedInts>::value, "move required");
    std::size_t cases = 0;
    for (std::size_t n = 0; n <= 64; ++n) {
        OwnedInts original(n);
        for (std::size_t i = 0; i < n; ++i) original.at(i) = static_cast<int>(3 * i + n);
        OwnedInts copied(original);  // no temporary/elision ambiguity
        for (std::size_t i = 0; i < n; ++i) {
            assert(copied.at(i) == original.at(i));
            assert(&copied.at(i) != &original.at(i));
            copied.at(i) = -9;
            assert(original.at(i) == static_cast<int>(3 * i + n));
        }
        OwnedInts assigned(3);
        assigned = original;
        assert(assigned.size() == n);
        assigned = assigned;
        for (std::size_t i = 0; i < n; ++i) assert(assigned.at(i) == original.at(i));
        OwnedInts moved(std::move(copied));
        assert(moved.size() == n && copied.size() == 0);
        copied = original;
        assert(copied.size() == n);
        moved = std::move(assigned);
        assert(moved.size() == n && assigned.size() == 0);
        bool caught = false;
        try { original.at(n); } catch (const std::out_of_range&) { caught = true; }
        assert(caught);
        ++cases;
    }
    Scores first{{1, 2, 3}};
    Scores second = first;
    second.values[0] = 8;
    assert(first.values[0] == 1);
    std::cout << "PASS " << cases << " OwnedInts sizes; Rule of Zero independence\n";
}
