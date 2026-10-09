#pragma once
#include "protocol.hpp"

namespace mw34::m4_integer_startup {
class StageCleanup {
    std::filesystem::path path_;
    explicit StageCleanup(std::filesystem::path path) : path_(std::move(path)) {}
    friend StageCleanup own_new_stage(const std::filesystem::path &);
 public:
    StageCleanup(const StageCleanup &) = delete;
    StageCleanup &operator=(const StageCleanup &) = delete;
    ~StageCleanup() {
        std::error_code error;
        std::filesystem::remove(path_, error);
    }
};
inline StageCleanup own_new_stage(const std::filesystem::path &path) {
    // An existing file is never acquired by this cleanup owner.
    require(!std::filesystem::exists(path), "Output staging file already exists");
    return StageCleanup{path};
}
inline void stage_collision_control(const std::filesystem::path &destination,
                                    const std::filesystem::path &stage) {
    const auto destination_text = destination.string();
    admit_output(destination_text.c_str());
    auto cleanup = own_new_stage(stage);
    throw std::runtime_error("Stage collision control needs a pre-existing stage");
}
}  // namespace mw34::m4_integer_startup
