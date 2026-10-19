// Offline asset-tool acceleration; the native renderer needs no extra DLL.
#include "material_normals.hpp"
#ifdef _WIN32
#define MW34_HASH_EXPORT __declspec(dllexport)
#else
#define MW34_HASH_EXPORT __attribute__((visibility("default")))
#endif
extern "C" MW34_HASH_EXPORT std::uint64_t mw34_normal_hash(const void *bytes,
                                                           std::size_t count) noexcept {
    return mw34::materials::normal_hash(bytes, count);
}
