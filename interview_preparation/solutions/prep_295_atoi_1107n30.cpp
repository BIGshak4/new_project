#include <cstdint>
#include <iostream>
#include <iterator>
#include <limits>
#include <string>
#include <string_view>

static bool ascii_space(char c) {
    return c == ' ' || c == '\t' || c == '\n' || c == '\r' || c == '\f' || c == '\v';
}

// Deliberately defined safe atoi-style behavior, including clamped overflow.
std::int32_t parse_int32(std::string_view text) {
    std::size_t index = 0;
    while (index < text.size() && ascii_space(text[index])) ++index;
    bool negative = false;
    if (index < text.size() && (text[index] == '+' || text[index] == '-')) {
        negative = text[index] == '-';
        ++index;
    }
    const std::int64_t limit = negative ? INT64_C(2147483648) : INT64_C(2147483647);
    std::int64_t value = 0;
    while (index < text.size() && text[index] >= '0' && text[index] <= '9') {
        const std::int64_t digit = text[index] - '0';
        if (value > (limit - digit) / 10) {
            return negative ? std::numeric_limits<std::int32_t>::min()
                            : std::numeric_limits<std::int32_t>::max();
        }
        value = value * 10 + digit;
        ++index;
    }
    return static_cast<std::int32_t>(negative ? -value : value);
}

#ifndef JOBRUN_PREP295_NO_MAIN
int main() {
    // Read all bytes, including leading newlines and embedded NUL bytes.
    const std::string input{std::istreambuf_iterator<char>(std::cin), std::istreambuf_iterator<char>()};
    std::cout << parse_int32(input) << '\n';
    return 0;
}
#endif
