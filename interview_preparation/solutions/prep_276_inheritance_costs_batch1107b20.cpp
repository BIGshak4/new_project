// C++17 educational example. score has type-specific semantics, not a sum contract.
#include <cassert>
#include <cstdint>
#include <iostream>
#include <memory>
#include <string_view>
#include <vector>

class Score {
public:
    virtual ~Score() = default;
    // Precondition: the mathematical sum fits int64_t.
    virtual std::int64_t score(const std::vector<std::int32_t>& xs) const {
        std::int64_t result = 0;
        for (const auto value : xs) result += value;
        return result;
    }
    std::string_view kind() const noexcept { return "Score"; }
};

class FixedScore final : public Score {
public:
    std::int64_t score(const std::vector<std::int32_t>&) const override {
        return 7;
    }
    // This hides a nonvirtual function; it does not override it.
    std::string_view kind() const noexcept { return "FixedScore"; }
};

class LifetimeProbe final : public Score {
public:
    explicit LifetimeProbe(bool& destroyed) : destroyed_(destroyed) {}
    ~LifetimeProbe() override { destroyed_ = true; }
private:
    bool& destroyed_;
};

int main() {
    unsigned checks = 0;
    const Score ordinary;
    const FixedScore fixed;
    const Score& through_base = fixed;
    const Score sliced = fixed;
    for (std::size_t n = 0; n <= 128; ++n) {
        const std::vector<std::int32_t> ones(n, 1);
        assert(ordinary.score(ones) == static_cast<std::int64_t>(n)); ++checks;
        assert(through_base.score(ones) == 7); ++checks;
        assert(sliced.score(ones) == static_cast<std::int64_t>(n)); ++checks;
        assert(fixed.Score::score(ones) == static_cast<std::int64_t>(n)); ++checks;
    }
    assert(fixed.kind() == "FixedScore"); ++checks;
    assert(through_base.kind() == "Score"); ++checks;
    assert(ordinary.score({-3, 0, 8, -2}) == 3); ++checks;
    bool destroyed = false;
    {
        std::unique_ptr<Score> owned = std::make_unique<LifetimeProbe>(destroyed);
        assert(!destroyed); ++checks;
    }
    assert(destroyed); ++checks;
    std::cout << "PREP-276: " << checks << " semantic assertions passed\n";
}
