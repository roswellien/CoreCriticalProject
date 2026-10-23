#include "../native-overrides/exact_uniform_runs.hpp"
#include <array>
#include <cassert>

int main() {
    // The active lighting block is 912 bytes. Exercise every bit, including
    // floating-point encodings that numeric comparisons could conflate.
    using Block = std::array<std::uint32_t, 228>;
    mw34::submission::ExactUniformRuns<Block> runs;
    Block original{};
    auto last = runs.identify(original);
    assert(last == 1 && runs.identify(original) == last);
    for (unsigned word = 0; word < original.size(); ++word) {
        for (unsigned bit = 0; bit < 32; ++bit) {
            Block changed = original;
            changed[word] ^= std::uint32_t(1) << bit;
            const auto different = runs.identify(changed);
            assert(different > last);
            assert(runs.identify(changed) == different);
            last = runs.identify(original);
            assert(last > different);
        }
    }
    Block negativeZero{}; negativeZero[0] = 0x80000000;
    assert(runs.identify(negativeZero) > last);
    Block nan{}; nan[0] = 0x7fc00001;
    const auto nanId = runs.identify(nan);
    assert(runs.identify(nan) == nanId);
    nan[0] ^= 1;
    assert(runs.identify(nan) > nanId);
    mw34::submission::ExactUniformRuns<Block> nextScene;
    assert(nextScene.identify(nan) == 1);
}
