#include "../native-overrides/exact_uniform_uploads.hpp"
#include <array>
#include <iostream>
#include <vector>

namespace {
unsigned checks{};
void require(bool value) {
    ++checks;
    if (!value) throw std::runtime_error("Uniform upload fixture failed");
}
using Block = std::array<std::uint32_t, 228>;
static_assert(sizeof(Block) == 912);
}

int main(int argc, char** argv) {
    try {
        if (argc > 1) {
            _putenv_s("MW34_UNIFORM_UPLOAD_REUSE", argv[1]);
            if (std::strcmp(argv[1], "0") && std::strcmp(argv[1], "1")) {
                bool rejected = false;
                try { mw34::submission::uniform_upload_reuse_enabled(); }
                catch (const std::runtime_error&) { rejected = true; }
                require(rejected);
            } else require(mw34::submission::uniform_upload_reuse_enabled() == (argv[1][0] == '1'));
        } else {
            constexpr std::size_t stride = 1024, capacity = 12;
            std::array<unsigned char, stride * capacity> before, after;
            before.fill(0xcd); after.fill(0xcd);
            mw34::submission::ExactUniformUploads<Block> original(false), compact(true);
            Block value{};
            std::vector<std::array<unsigned, 3>> draws;
            const std::array<unsigned, 8> indices{0, 1, 3, 4, 6, 7, 9, 11};
            for (unsigned n = 0; n < indices.size(); ++n) {
                // A,A,B,B,A,A,C,C; include signed-zero and distinct NaN payloads.
                value[0] = n < 2 || (n >= 4 && n < 6) ? 0 : n < 4 ? 0x80000000U : 0x7fc00001U;
                const auto a = original.capture(value, indices[n], stride, before.data());
                const auto b = compact.capture(value, indices[n], stride, after.data());
                require(a == b);
                draws.push_back({indices[n], a, b});
            }
            require(original.values == 8 && original.writes == 8);
            require(compact.values == 8 && compact.writes == 4);
            // Read draws in a different order, including revisits after other runs.
            for (unsigned n : {7U, 0U, 5U, 2U, 1U, 6U, 3U, 4U}) {
                const auto& draw = draws[n];
                auto a = original.offset(draw[1], draw[0], stride);
                auto b = compact.offset(draw[2], draw[0], stride);
                require(a % 256 == 0 && b % 256 == 0);
                require(b + sizeof(Block) <= after.size());
                require(!std::memcmp(before.data() + a, after.data() + b, sizeof(Block)));
            }
            for (std::size_t i = 0; i < after.size(); ++i)
                if (i >= 4 * stride || i % stride >= sizeof(Block)) require(after[i] == 0xcd);
            bool rejected = false;
            try { compact.offset(0, 0, stride); } catch (const std::runtime_error&) { rejected = true; }
            require(rejected);
            rejected = false;
            try { compact.offset(5, 0, stride); } catch (const std::runtime_error&) { rejected = true; }
            require(rejected);
            rejected = false;
            try { original.offset(1, std::numeric_limits<std::uint32_t>::max(), stride); }
            catch (const std::runtime_error&) { rejected = true; }
            require(rejected);
            // A fresh scene must upload again; no prior buffer contents qualify.
            mw34::submission::ExactUniformUploads<Block> next(true);
            require(next.capture(value, 0, stride, after.data()) == 1 && next.writes == 1);
            // Every bit in the complete shader block must start a new run.
            for (unsigned word = 0; word < value.size(); ++word)
                for (unsigned bit = 0; bit < 32; ++bit) {
                    mw34::submission::ExactUniformUploads<Block> pair(true);
                    const auto first = pair.capture(value, 0, stride, after.data());
                    Block changed = value; changed[word] ^= std::uint32_t(1) << bit;
                    const auto second = pair.capture(changed, 1, stride, after.data());
                    require(first == 1 && second == 2 && pair.writes == 2);
                    require(!std::memcmp(after.data() + stride, &changed, sizeof(changed)));
                    require(pair.capture(changed, 2, stride, after.data()) == 2 && pair.writes == 2);
                }
        }
        std::cout << "Lighting upload checks=" << checks << " failures=0\n";
    } catch (const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
