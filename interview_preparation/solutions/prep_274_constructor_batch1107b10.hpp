#ifndef PREP_274_CONSTRUCTOR_BATCH1107B10_HPP
#define PREP_274_CONSTRUCTOR_BATCH1107B10_HPP
#include <cstdint>
#include <stdexcept>

// Every successfully constructed Range has low() <= high(). No heap ownership.
class Range {
public:
    Range() : Range(0, 0) {}

    Range(std::int32_t low, std::int32_t high) : low_(low), high_(high) {
        if (low > high) {
            throw std::invalid_argument("low must not exceed high");
        }
    }

    std::int32_t low() const noexcept { return low_; }
    std::int32_t high() const noexcept { return high_; }
    std::int64_t span() const noexcept {
        return static_cast<std::int64_t>(high_) - static_cast<std::int64_t>(low_);
    }

private:
    std::int32_t low_;
    std::int32_t high_;
};
#endif
