#pragma once

#include "frontend/core_critical/renderer/geometry/resource.hpp"

#include <cstddef>
#include <memory>
#include <vector>

namespace zcls {
struct Node;
}
namespace zmod {
struct Material;
struct Model;

struct RigidGeometryEligibility {
    bool overlay{};
    bool second_pass{};
    float opacity{1.f};
};

struct RegisteredRigidSource {
    std::shared_ptr<const cc::geometry::Resource> resource;
    std::vector<const Material *> original_materials;
};

bool rigid_source_supported(const Model &model, const RigidGeometryEligibility &eligibility);
std::size_t preflight_rigid_source_bytes(const Model &model);
RegisteredRigidSource register_rigid_source(const Model &model);
std::vector<cc::geometry::Material> copy_rigid_materials(
    const Model &model, const cc::geometry::Resource &resource);

// Synchronous rendering handoff. True only after an owned submission succeeds.
bool submit_geometry(zcls::Node &node);
} // namespace zmod
