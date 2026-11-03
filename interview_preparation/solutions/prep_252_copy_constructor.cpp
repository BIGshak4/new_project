// C++17. A value type needing no custom special members (Rule of Zero).
#include <algorithm>
#include <cstddef>
#include <memory>
#include <stdexcept>
#include <utility>
#include <vector>

struct Scores {
    std::vector<int> values;
};

// Explicit ownership example: copies allocate independent element storage.
class OwnedInts {
    std::size_t size_ = 0;
    std::unique_ptr<int[]> values_;

public:
    explicit OwnedInts(std::size_t size = 0)
        : size_(size), values_(size ? new int[size]{} : nullptr) {}

    OwnedInts(const OwnedInts& other) : OwnedInts(other.size_) {
        for (std::size_t i = 0; i < size_; ++i) values_[i] = other.values_[i];
    }

    OwnedInts(OwnedInts&& other) noexcept
        : size_(std::exchange(other.size_, 0)), values_(std::move(other.values_)) {}

    // By-value assignment covers copy and move assignment; swap cannot throw.
    OwnedInts& operator=(OwnedInts other) noexcept {
        swap(other);
        return *this;
    }

    ~OwnedInts() = default;

    void swap(OwnedInts& other) noexcept {
        std::swap(size_, other.size_);
        values_.swap(other.values_);
    }

    std::size_t size() const noexcept { return size_; }
    int& at(std::size_t i) {
        if (i >= size_) throw std::out_of_range("OwnedInts");
        return values_[i];
    }
    const int& at(std::size_t i) const {
        if (i >= size_) throw std::out_of_range("OwnedInts");
        return values_[i];
    }
};
