// C++17 implementation. Only used_ is persistent allocation-management state.
#include <cstdint>

class Pool32 {
    std::uint32_t used_ = 0;
public:
    int malloc_index() {
        const std::uint32_t free_bits = ~used_;
        if (free_bits == 0) return -1;
        for (unsigned index = 0; index < 32; ++index) {
            const std::uint32_t bit = std::uint32_t{1} << index;
            if (free_bits & bit) {
                used_ |= bit;
                return static_cast<int>(index);
            }
        }
        return -1;
    }

    bool free_index(int index) {
        if (index < 0 || index >= 32) return false;
        const std::uint32_t bit = std::uint32_t{1} << index;
        if ((used_ & bit) == 0) return false;
        used_ &= ~bit;
        return true;
    }
};
