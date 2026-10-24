// C++17: cast BEFORE subtraction, avoiding signed overflow at INT32_MIN.
#include <cstdint>

bool is_one_bit_active(std::int32_t n) {
    const std::uint32_t u = static_cast<std::uint32_t>(n);
    return u != 0 && (u & (u - std::uint32_t{1})) == 0;
}
