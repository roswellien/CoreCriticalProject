// Authored PE import edge for staging tests; this is never a native game fixture.
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>

extern "C" __declspec(dllimport) std::uint64_t mw34_normal_hash(const void *bytes,
                                                                std::size_t count) noexcept;

int main(int argc, char **argv) {
    // The later selected-tool lookup control copies this fixture as git.exe.
    const char *name = std::strrchr(argv[0], '\\');
    name = name == nullptr ? argv[0] : name + 1;
    if (std::strcmp(name, "git.exe") == 0) {
        std::puts("MW34_AUTHORED_SHADOW_GIT");
    }
    const char bytes[] = "authored staging dependency";
    return mw34_normal_hash(bytes, sizeof(bytes)) == 0 || argc < 1 ? 1 : 0;
}
