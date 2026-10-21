#include <cstdint>
#include <memory>

// Distinct references or a same-location no-op. No auxiliary value variable.
void xor_swap(std::uint8_t& a, std::uint8_t& b) {
    if (std::addressof(a) == std::addressof(b)) return;
    a ^= b;
    b ^= a;
    a ^= b;
}

// Integral promotions precede arithmetic; conversion back to uint8_t is modulo
// 256. Promoted addition is at most 510 and subtraction at least -255, so these
// intermediates fit even the minimum standard range of int.
void modular_swap(std::uint8_t& a, std::uint8_t& b) {
    if (std::addressof(a) == std::addressof(b)) return;
    a = static_cast<std::uint8_t>(a + b);
    b = static_cast<std::uint8_t>(a - b);
    a = static_cast<std::uint8_t>(a - b);
}
