// Shared by the native adapter and its authored polygon-capture fixture.
void world_capture(D3DCmd &draw) {
    if (!world_scope || !world_cell_depth || override_suppress_draw() ||
        draw.flags != D3DPT_TRIANGLEFAN || !draw.indices.empty() || draw.hud_role != WideWorld ||
        frontend_on())
        return;
    if (!draw.state_snapshot || draw.state_snapshot->size() < 256)
        throw std::runtime_error("World direct draw state unavailable");
    if ((*draw.state_snapshot)[D3DRENDERSTATE_ALPHATESTENABLE] ||
        (*draw.state_snapshot)[D3DRENDERSTATE_ALPHABLENDENABLE])
        return;
    WorldTicks timer(world_binding_ticks);
    const auto &scope = *world_scope;
    const unsigned count = unsigned(draw.vertices.size() / 32);
    const unsigned frame = scope.frame_base;
    if (frame < 0x120 || !readable(frame - 0x120, 0x124) || load(frame - 0x38) != scope.mesh)
        throw std::runtime_error("World direct original frame ownership mismatch");
    const unsigned address = load(frame - 0x34);
    const auto slot =
        mw34::world::polygon_slot(scope.polygon_base, scope.polygon_lookup->size(), address);
    if (!slot) {
        ++world_misses;
        return;
    }
    const int index = (*scope.polygon_lookup)[*slot];
    if (index < 0) {
        ++world_misses;
        return;
    }
    const auto &polygon = (*scope.polygons)[size_t(index)];
    if (polygon.source != address)
        throw std::runtime_error("World direct polygon identity mismatch");
    if (count < 3) {
        ++world_misses;
        return;
    }
    bool exact = polygon.corners.size() == count;
    mw34::vkscene::HostFpEnvironment fp;
    const auto matrix = override_matrix(load(load(0x5eda90)));
    const double near_scale = world_float(0x73fb80), sx = world_float(0x73fc30),
                 sy = world_float(0x73fb98), cx = world_float(0x73fb88), cy = world_float(0x73fb8c),
                 near_clip = world_float(0x740304);
    if (near_scale <= 0 || near_clip <= 0 || sx == 0 || sy == 0)
        throw std::runtime_error("World direct projection outside contract");
    struct Tl {
        float x, y, z, rhw;
        unsigned color, spec;
        float u, v;
    };
    static_assert(sizeof(Tl) == 32);
    const bool fast =
        world_fast_enabled() && !mw34::temporal::enabled() &&
        load(frame - 0x44) == polygon.material && readable(polygon.material, 4) &&
        (load(polygon.material) & 0x100) &&
        mw34::world::unchanged_polygon(load(frame - 0x74), polygon.flags, load(address + 4),
                                       load(0x7489a8), load(frame - 0x54));
    // The original producer reverses polygon corners before submission. No search
    // by projected position is used, so coincident normals keep their own corner.
    // Retain a linear projection audit until all downstream clipping is owned.
    if (exact)
        for (unsigned j = 0; j < count; ++j) {
            const auto &v = polygon.corners[count - 1 - j].vertex;
            Tl tl;
            std::memcpy(&tl, draw.vertices.data() + j * 32, 32);
            if (!std::isfinite(tl.u) || !std::isfinite(tl.v) || std::abs(v.u - tl.u) > 1e-5 ||
                std::abs(v.v - tl.v) > 1e-5) {
                exact = false;
                break;
            }
            if (fast) {
                ++world_fast_corners;
                continue;
            }
            ++world_audited_corners;
            const double z = matrix[8] * v.x + matrix[9] * v.y + matrix[10] * v.z + matrix[11];
            if (z <= near_clip) {
                exact = false;
                break;
            }
            const double r = near_scale / z,
                         x = (matrix[0] * v.x + matrix[1] * v.y + matrix[2] * v.z + matrix[3]) *
                                 sx * r +
                             cx,
                         y = (matrix[4] * v.x + matrix[5] * v.y + matrix[6] * v.z + matrix[7]) *
                                 sy * r +
                             cy;
            if (!std::isfinite(tl.x) || !std::isfinite(tl.y) || !std::isfinite(tl.z) ||
                !std::isfinite(tl.rhw) || !std::isfinite(tl.u) || !std::isfinite(tl.v) ||
                std::abs(x - tl.x) > .02 || std::abs(y - tl.y) > .02 ||
                std::abs(r - tl.rhw) > std::max(1e-7, std::abs(r) * 1e-5) ||
                std::abs(r - tl.z) > std::max(1e-7, std::abs(r) * 1e-5) ||
                std::abs(v.u - tl.u) > 1e-5 || std::abs(v.v - tl.v) > 1e-5) {
                exact = false;
                break;
            }
        }
    // Temporal-only capture retains the original TL draw and requires byte-identical
    // attributes. Rebuilding a rejected polygon cannot satisfy that contract:
    // reconstruction changes the rejected UV/projection values or corner count.
    // Leave its original TL coverage available as an unproved occluder instead.
    if (!exact && scope.temporal_only) {
        ++world_misses;
        return;
    }
    if (!exact && !world_edge_admit(draw, polygon, matrix, near_scale, sx, sy, cx, cy, near_clip)) {
        ++world_misses;
        return;
    }
    auto instance = std::make_shared<mw34::vkscene::ModelInstance>();
    instance->geometry = polygon.resident;
    instance->world = true;
    for (unsigned i = 0; i < 12; ++i)
        instance->camera[i] = float(matrix[i]);
    instance->projection = {float(near_scale), float(sx), float(sy),
                            float(cx),         float(cy), float(near_clip)};
    sun_capture_world(*instance, scope.node);
    draw.fixture_node = scope.node;
    draw.fixture_polygon = polygon.source;
    draw.model = std::move(instance);
    ++world_draws;
}
