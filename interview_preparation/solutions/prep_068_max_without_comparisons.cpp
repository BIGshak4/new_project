// C++11 or later; requires exact-width int32_t/uint32_t and int64_t.
// Materialize modulo-2^32 subtraction before shifting. Integer promotions are
// safe even when int is wider than 32 bits: no signed overflow, negative signed
// right shift, or out-of-range unsigned-to-signed conversion is required.
// This artifact is supplied, but was not compiled in the current environment.
#include <cstdint>

std::int32_t max_i32(std::int32_t a, std::int32_t b) {
    const std::uint32_t ua = static_cast<std::uint32_t>(a);
    const std::uint32_t ub = static_cast<std::uint32_t>(b);
    const std::uint32_t sa = ua >> 31;
    const std::uint32_t sb = ub >> 31;
    const std::uint32_t different = sa ^ sb;
    // Store first: integer promotion may otherwise perform subtraction in a
    // wider signed int. Conversion here restores modulo-2^32 before shifting.
    const std::uint32_t difference = ua - ub;
    const std::uint32_t difference_sign = difference >> 31;
    const std::uint32_t choose_b =
        (different & sa) | ((different ^ 1u) & difference_sign);
    const std::uint32_t mask = 0u - choose_b;
    // XOR avoids applying ~ to a value that might promote to signed int.
    const std::uint32_t keep_a = mask ^ UINT32_C(0xffffffff);
    const std::uint32_t bits = (ua & keep_a) | (ub & mask);
    const std::int64_t signed_value =
        static_cast<std::int64_t>(bits & UINT32_C(0x7fffffff)) -
        static_cast<std::int64_t>(bits >> 31) * INT64_C(2147483648);
    return static_cast<std::int32_t>(signed_value);
}
