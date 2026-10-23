#define NOMINMAX
#include "../native-overrides/pipeline_warmup.hpp"
#include <cassert>

int main() {
    using namespace mw34::pipeline_warmup;
    const std::uint64_t key = (1ULL << 48) | (1ULL << 32) | (2ULL << 16) | (5ULL << 8);
    assert(valid(key));
    for (auto bad : {key | (1ULL << 60), key | 2, key | (12ULL << 8),
                     key & ~(255ULL << 32), key | (1ULL << 58)}) assert(!valid(bad));
    std::set<std::uint64_t> keys{key};
    std::ostringstream text;
    text << "MW34PIPE1\n" << std::hex << key << '\n';
    std::istringstream input(text.str());
    assert(parse(input, keys) && keys.size() == 1 && keys.contains(key));
    for (const auto &bad : {"BAD\n", "MW34PIPE1\nxyz\n", "MW34PIPE1\n0\n",
                            "MW34PIPE1\n1000000000000000\n", "MW34PIPE1\n\n"}) {
        std::istringstream corrupt(bad);
        assert(!parse(corrupt, keys) && keys.size() == 1 && keys.contains(key));
    }
    std::istringstream duplicate(text.str() + text.str().substr(10));
    assert(!parse(duplicate, keys));
    const auto directory = std::filesystem::temp_directory_path() /
        ("mw3-pipeline-recipe-" + std::to_string(GetCurrentProcessId()));
    _putenv_s("MW34_PIPELINE_WARMUP_DIR", directory.string().c_str());
    _putenv_s("MW34_PIPELINE_WARMUP", "1");
    Recipe recipe;
    recipe.load("scene"); recipe.record(key);
    assert(!std::filesystem::exists(directory)); // No writes in the frame loop.
    recipe.save();
    Recipe loaded; loaded.load("scene");
    assert(loaded.states().contains(key));
    _putenv_s("MW34_PIPELINE_WARMUP", "0");
    Recipe off; off.load("scene"); off.record(key); off.save();
    assert(off.states().empty());
    _putenv_s("MW34_PIPELINE_WARMUP", "bad");
    try { Recipe invalid; invalid.load("scene"); assert(false); } catch (const std::runtime_error &) {}
    std::filesystem::remove_all(directory);
    _putenv_s("MW34_PIPELINE_WARMUP_DIR", "");
    _putenv_s("MW34_PIPELINE_WARMUP", "");
}
