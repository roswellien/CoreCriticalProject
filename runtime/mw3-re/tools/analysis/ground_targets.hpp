#pragma once
#include <cstdint>
#include <filesystem>
#include <string>
#include <vector>

namespace mw3::ground_targets {
struct TexturePin {
    std::string texture, member, sha256, entry;
    std::uint64_t bytes{};
    std::uint32_t mip{};
};
struct Request {
    std::filesystem::path data_root, bank_root;
    std::string member, sha256, region, asset_id, surface_materials;
    std::uint64_t bytes{};
    std::uint32_t model_slot{};
    std::vector<TexturePin> textures;
};
struct Result {
    std::string material_targets, receipt;
};
struct InspectionRequest {
    std::filesystem::path data_root;
    std::string member, sha256, region;
    std::uint64_t bytes{};
};
// Strict, bounded private input; never accepts renderer observations.
Request read_request(const std::string &json);
InspectionRequest read_inspection_request(const std::string &json);
// Discovery metadata is deliberately separate from receiver target metadata.
std::string inspect_source(const InspectionRequest &request);
// Isolated canonical CPU decode. Does not create a device or enter a game loop.
Result export_target(const Request &request);
// Writes only the two metadata documents into a fresh directory, atomically.
void write_result(const Result &result, const std::filesystem::path &fresh_output);
void write_inspection(const std::string &inspection, const std::filesystem::path &fresh_output);
} // namespace mw3::ground_targets
