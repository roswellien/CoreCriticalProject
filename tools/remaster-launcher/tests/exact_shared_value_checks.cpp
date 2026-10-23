#include "../native-overrides/exact_shared_value.hpp"
#include <array>
#include <bit>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <vector>

struct View {
    std::array<float, 12> camera{};
    std::array<float, 6> projection{};
};
static_assert(sizeof(View) == 72);

int main() {
    try {
        mw34::submission::ExactSharedValue<View> values;
        View first{};
        auto original = values.capture(first);
        static_assert(std::is_const_v<std::remove_reference_t<decltype(*original)>>);
        if (values.capture(first) != original)
            throw std::runtime_error("Identical view was not shared");
        std::vector<std::shared_ptr<const View>> retained{original};
        std::vector<View> expected{first};
        unsigned checks = 1;
        for (unsigned word = 0; word < 18; ++word) {
            std::array<std::uint32_t, 18> bits{};
            bits[word] = 0x80000000U; // +0 and -0 must stay distinct.
            const auto changed = std::bit_cast<View>(bits);
            auto next = values.capture(changed);
            if (next == original || std::memcmp(next.get(), &changed, sizeof(View)))
                throw std::runtime_error("Changed camera/projection bits were lost");
            if (values.capture(changed) != next)
                throw std::runtime_error("Repeated changed view was not shared");
            retained.push_back(next);
            expected.push_back(changed);
            ++checks;
        }
        values.capture(first);
        for (std::size_t i = 0; i < retained.size(); ++i) {
            if (std::memcmp(retained[i].get(), &expected[i], sizeof(View)))
                throw std::runtime_error("An earlier draw's immutable view changed");
            ++checks;
        }
        std::cout << "exact shared view checks=" << checks << " failures=0\n";
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
