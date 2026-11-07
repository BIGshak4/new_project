#define JOBRUN_PREP295_NO_MAIN
#include "../solutions/prep_295_atoi_1107n30.cpp"
#include <cassert>
#include <utility>
#include <vector>

int main() {
    const std::vector<std::pair<std::string, std::int32_t>> cases = {
        {"", 0}, {" \t\n", 0}, {"0", 0}, {"+0", 0}, {"-0", 0},
        {"12345", 12345}, {"   -42xyz", -42}, {"\n\t+17 rest", 17},
        {"+", 0}, {"-", 0}, {"+-12", 0}, {"words 42", 0}, {"0x10", 0},
        {"00120", 120}, {"2147483647", INT32_C(2147483647)},
        {"2147483648", INT32_C(2147483647)}, {"-2147483648", INT32_MIN},
        {"-2147483649", INT32_MIN}, {std::string(1000, '9'), INT32_C(2147483647)},
        {"-" + std::string(1000, '9'), INT32_MIN}, {std::string("12\0" "34", 5), 12},
        {"  + 5", 0}, {"\r\f\v-19", -19}, {"12.34", 12},
        {std::string("\xc2\xa0" "42"), 0}
    };
    for (const auto &test : cases) assert(parse_int32(test.first) == test.second);
    std::cout << "PASS: " << cases.size() << " native int32 parsing cases\n";
}
