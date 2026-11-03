// Included inside Stage. Serial consumption is opt-in until guest-state and
// callback equivalence have been established. No worker accesses this adapter.
bool adaptive_ground_enabled() {
    static const bool enabled = [] {
        SunCaptureFp preserve;
        const char *value = std::getenv("MW34_ADAPTIVE_GROUND");
        if (!value || !*value || !std::strcmp(value, "0"))
            return false;
        if (!std::strcmp(value, "1"))
            return true;
        throw std::runtime_error("MW34_ADAPTIVE_GROUND must be 0 or 1");
    }();
    return enabled;
}

bool adaptive_ground_check_enabled() {
    static const bool enabled = [] {
        SunCaptureFp preserve;
        const char *value = std::getenv("MW34_ADAPTIVE_CHECK");
        if (!value || !*value || !std::strcmp(value, "0"))
            return false;
        if (!std::strcmp(value, "1"))
            return true;
        throw std::runtime_error("MW34_ADAPTIVE_CHECK must be 0 or 1");
    }();
    return enabled;
}

bool adaptive_ground_any_enabled() {
    static const bool enabled = [this] {
        SunCaptureFp preserve;
        return adaptive_ground_enabled() || adaptive_ground_check_enabled();
    }();
    return enabled;
}

bool adaptive_ground_sample() const {
    const unsigned frame = host.frames + 1;
    return frame == 801 || frame == 849 || frame == 1801 || frame == 2101;
}

bool adaptive_ground_adapter(unsigned target) {
    if (!adaptive_ground_any_enabled() || (!adaptive_ground_mesh && !adaptive_ground_active) ||
        !mw34::body_dispatch::adaptive_target(target))
        return false;
    if (target == 0x547740)
        return adaptive_ground_enabled() ||
               (adaptive_ground_check_enabled() && adaptive_ground_sample());
    if (target == 0x545720)
        return adaptive_ground_enabled() && adaptive_ground_mesh && adaptive_ground_worker_count();
    if (target == 0x57ea20)
        return adaptive_ground_active && adaptive_ground_check_enabled() &&
               adaptive_ground_sample();
    if (target == 0x523540)
        return adaptive_ground_projection_pending();
    // The projection/split hooks matter only inside an owned adaptive call.
    // Keep the warmed fast route for all other original uses of those helpers.
    return adaptive_ground_split_pending() && adaptive_ground_enabled();
}

struct AdaptiveGroundMetrics {
    std::uint64_t calls{}, packets{}, vertices{}, skipped{}, consumed{}, contexts{},
        worker_consumed{};
    ~AdaptiveGroundMetrics() {
        if (!calls && !skipped && !consumed)
            return;
        SunCaptureFp preserve;
        std::fprintf(
            stderr,
            "Adaptive ground check: %llu calls, %llu packets, %llu vertices, %llu skipped; "
            "sample frames 801/849/1801/2101; %llu serial consumptions; %llu current contexts; "
            "%llu from workers\n",
            static_cast<unsigned long long>(calls), static_cast<unsigned long long>(packets),
            static_cast<unsigned long long>(vertices), static_cast<unsigned long long>(skipped),
            static_cast<unsigned long long>(consumed), static_cast<unsigned long long>(contexts),
            static_cast<unsigned long long>(worker_consumed));
    }
} adaptive_ground_metrics;

unsigned adaptive_ground_node{};
std::vector<mw34::adaptive_ground::GuestVertexRecord> adaptive_ground_vertex_staging;
std::vector<mw34::adaptive_ground::GuestTriangleRecord> adaptive_ground_triangle_staging;
struct AdaptiveGroundCheck;
AdaptiveGroundCheck *adaptive_ground_active{};

float adaptive_ground_float(unsigned address) { return std::bit_cast<float>(load(address)); }

mw34::adaptive_ground::Point adaptive_ground_point(unsigned address) {
    return {adaptive_ground_float(address), adaptive_ground_float(address + 4),
            adaptive_ground_float(address + 8)};
}

void adaptive_ground_word(unsigned address, unsigned expected) {
    if (load(address) != expected)
        deny("Adaptive ground numerical mismatch at guest address " + std::to_string(address),
             0x547740);
}

void adaptive_ground_float_word(unsigned address, float expected) {
    adaptive_ground_word(address, std::bit_cast<unsigned>(expected));
}

struct AdaptiveGroundShared {
    mw34::adaptive_ground::Input input;
    std::vector<unsigned> light_addresses;
};

AdaptiveGroundShared adaptive_ground_shared_input() {
    using namespace mw34::adaptive_ground;
    AdaptiveGroundShared snapshot;
    auto &input = snapshot.input;
    auto &light_addresses = snapshot.light_addresses;
    input.extra_uv_layers = load(0x7489a8);
    std::memcpy(&input.guest_control_word, reinterpret_cast<const unsigned char *>(&state) + 0xad0,
                2);
    input.depth_bias_scale = adaptive_ground_float(0x74a284);
    input.colored_rgb = adaptive_ground_point(0x72f40c);
    input.projection = {adaptive_ground_float(0x73fb80), adaptive_ground_float(0x73fb88),
                        adaptive_ground_float(0x73fb8c), adaptive_ground_float(0x73fc30),
                        adaptive_ground_float(0x73fb98), adaptive_ground_float(0x63d758),
                        adaptive_ground_float(0x63d75c)};
    const unsigned light_count = load(0x74981c);
    if (light_count > mw34::adaptive_ground::maximum_lights)
        deny("Adaptive ground selected-light table exceeds its contract", 0x547740);
    for (unsigned index = 0; index < light_count; ++index) {
        const unsigned address = load(0x749824 + index * 20);
        light_addresses.push_back(address);
        Light light;
        light.active = load(0x749830 + index * 20) != 0;
        if (light.active) {
            light.flags = load(address + 0xb0);
            if ((light.flags & 0x50) == 0x50) {
                light.position = adaptive_ground_point(address + 0x78);
                light.color = adaptive_ground_point(address + 0xa4);
                light.diffuse = adaptive_ground_float(address + 0x9c);
                light.ambient = adaptive_ground_float(address + 0xa0);
                light.inner_radius = adaptive_ground_float(address + 0xb4);
                light.outer_radius = adaptive_ground_float(address + 0xb8);
                light.inner_squared = adaptive_ground_float(address + 0xbc);
                light.outer_squared = adaptive_ground_float(address + 0xc0);
                light.inverse_span = adaptive_ground_float(address + 0xc4);
            }
        }
        input.lights.push_back(light);
    }
    return snapshot;
}

#include "adaptive_ground_lookahead_stage.inc"

struct AdaptiveGroundCheck {
    Stage &stage;
    AdaptiveGroundCheck *previous{};
    std::optional<mw34::adaptive_ground::Result> result;
    std::vector<unsigned> light_addresses;
    unsigned input_count{}, packet{};
    unsigned entry_sp{};
    bool check{}, admitted{}, consumed{}, restored{}, from_worker{};

    explicit AdaptiveGroundCheck(Stage &owner)
        : stage(owner), previous(owner.adaptive_ground_active) {
        SunCaptureFp preserve;
        stage.adaptive_ground_active = nullptr;
        const unsigned sp = stage.state.gpr.rsp.dword;
        entry_sp = sp;
        check = stage.adaptive_ground_check_enabled() && stage.adaptive_ground_sample();
        const unsigned node = stage.adaptive_ground_node;
        auto skip = [&] { ++stage.adaptive_ground_metrics.skipped; };
        if (!node || !stage.readable(node + 0x3c, 4) || !stage.readable(sp, 16) ||
            stage.load(sp) != 0x540a70) {
            skip();
            return;
        }
        const unsigned mesh = stage.load(node + 0x3c);
        if (!mesh || !stage.readable(mesh, 0x48) || stage.load(mesh) != 0 ||
            stage.load(mesh + 12) > 1 || stage.load(mesh + 0x1c) || stage.load(mesh + 0x20)) {
            skip();
            return;
        }
        using namespace mw34::adaptive_ground;
        Input input;
        input_count = stage.state.gpr.rcx.dword;
        input.extra_uv_layers = stage.load(0x7489a8);
        std::memcpy(&input.guest_control_word,
                    reinterpret_cast<const unsigned char *>(&stage.state) + 0xad0, 2);
        if (input_count < 3 || input_count > maximum_source_vertices || input.extra_uv_layers ||
            input.guest_control_word != 0x023f) {
            skip();
            return;
        }
        auto common = stage.adaptive_ground_shared_input();
        input = std::move(common.input);
        light_addresses = std::move(common.light_addresses);
        // An already authenticated current snapshot may be copied. Missing
        // history is not manufactured or published to run a numerical check.
        if (stage.camera_last_snapshot &&
            stage.camera_last_snapshot->frame == stage.camera_flip_serial + 1)
            input.identity.camera = *stage.camera_last_snapshot;
        input.identity.source_node = node;
        input.identity.mesh = mesh;
        const unsigned bp = stage.state.gpr.rbp.dword;
        if (bp >= 0x34 && stage.readable(bp - 0x34, 4))
            input.identity.polygon = stage.load(bp - 0x34);
        input.identity.material = stage.load(sp + 8);
        // A read-only current observation never creates a history epoch. Inline
        // preparation can still use actual entry values if async provenance is
        // unavailable; only a complete context may later authorize a worker.
        if (stage.adaptive_ground_enabled() && stage.adaptive_ground_worker_count()) {
            const auto context = stage.adaptive_ground_context(node, mesh, input.identity.polygon,
                                                               input.identity.material);
            if (context) {
                input.identity = *context;
                ++stage.adaptive_ground_metrics.contexts;
            }
        }
        input.varying_ambient = stage.state.gpr.rdx.dword != 0;
        input.colored_ambient = (stage.load(sp + 4) & 4) != 0;
        input.depth_bias = std::bit_cast<std::int32_t>(stage.load(sp + 12));
        for (unsigned index = 0; index < input_count; ++index) {
            SourceVertex vertex;
            vertex.screen = stage.adaptive_ground_point(0x72f41c + index * 32);
            vertex.uv[0] = {stage.adaptive_ground_float(0x72f434 + index * 32),
                            stage.adaptive_ground_float(0x72f438 + index * 32)};
            vertex.ambient = stage.adaptive_ground_float(0x7481a8 + index * 32);
            vertex.fog = stage.adaptive_ground_float(0x7481b0 + index * 32);
            vertex.colored_ambient = stage.adaptive_ground_float(0x7481ac + index * 32);
            vertex.modulation = stage.adaptive_ground_point(0x7481b4 + index * 32);
            input.vertices.push_back(vertex);
        }
        if (stage.adaptive_ground_enabled())
            admitted = source_matches(input, mesh);
        // A rejected serial candidate can still participate in the independent
        // numerical comparison; ordinary execution remains authoritative.
        if (!check && !admitted)
            return;
        if (admitted && stage.adaptive_ground_mesh)
            result = stage.adaptive_ground_mesh->take(input);
        from_worker = result.has_value();
        if (!result)
            result = mw34::adaptive_ground::prepare(input);
        stage.adaptive_ground_active = this;
    }

    bool source_matches(const mw34::adaptive_ground::Input &input, unsigned mesh) {
        using namespace mw34::adaptive_ground;
        const unsigned polygon = input.identity.polygon;
        const unsigned count = stage.load(mesh + 0x10);
        const unsigned polygons = stage.load(mesh + 0x34);
        if (!polygon || !count || count > 4096 || polygon < polygons || (polygon - polygons) % 36 ||
            (polygon - polygons) / 36 >= count || !stage.readable(polygon, 36) ||
            (stage.load(polygon) & 255) != input_count)
            return false;
        const unsigned positions = stage.load(0x74639c);
        const unsigned position_count = stage.load(mesh + 0x14);
        const unsigned indices = stage.load(polygon + 8), uv = stage.load(polygon + 16);
        const unsigned camera = stage.load(0x7402f4);
        if (!positions || !position_count || position_count > 65535 || !indices || !uv || !camera ||
            !stage.readable(camera, 0xb8) || !stage.readable(positions, position_count * 12) ||
            !stage.readable(indices, input_count * 4) || !stage.readable(uv, input_count * 8))
            return false;
        std::vector<SourceCorner> source;
        source.reserve(input_count);
        for (unsigned index = input_count; index-- > 0;) {
            const unsigned vertex = stage.load(indices + index * 4);
            if (vertex >= position_count)
                return false;
            source.push_back({stage.adaptive_ground_point(positions + vertex * 12),
                              {stage.adaptive_ground_float(uv + index * 8),
                               stage.adaptive_ground_float(uv + index * 8 + 4)}});
        }
        const ClipBounds bounds{
            stage.adaptive_ground_float(0x740304), stage.adaptive_ground_float(camera + 0xb4),
            stage.adaptive_ground_float(0x74031c), stage.adaptive_ground_float(0x740320),
            stage.adaptive_ground_float(0x740324), stage.adaptive_ground_float(0x740328)};
        return matches_unclipped_source(source, input, bounds);
    }

    bool consume_split(void *memory) {
        SunCaptureFp preserve;
        if (!admitted || consumed || !result || !result->prepared ||
            result->vertices.size() <= input_count + 1)
            return false;
        const unsigned sp = stage.state.gpr.rsp.dword;
        if (stage.load(sp) != 0x547f96 || stage.state.gpr.rbp.dword != entry_sp - 4)
            return false;
        // Original initial setup has run, including its selected-light writes.
        // Reject before writing if this is not the first split of this fan.
        if (stage.load(0x64fbe8) != input_count + 1 || stage.load(0x64fbec) != input_count)
            stage.deny("Adaptive ground first-split boundary changed", 0x547160);
        for (unsigned index = 0; index <= input_count; ++index)
            for (unsigned axis = 0; axis < 3; ++axis)
                stage.adaptive_ground_float_word(0x65ddf8 + index * 132 + axis * 4,
                                                 result->vertices[index].camera[axis]);
        using namespace mw34::adaptive_ground;
        if (result->vertices.size() > 1024 || result->triangles.size() > 2048)
            stage.deny("Adaptive ground transfer capacity changed", 0x547160);
        const unsigned vertices = unsigned(result->vertices.size());
        const unsigned triangles = unsigned(result->triangles.size());
        const unsigned vertex_bytes = vertices * unsigned(sizeof(GuestVertexRecord));
        const unsigned triangle_bytes = triangles * unsigned(sizeof(GuestTriangleRecord));
        if (!stage.readable(0x65ddf8, vertex_bytes) || !stage.writable(0x65ddf8, vertex_bytes) ||
            !stage.writable(0x64fdf0, triangle_bytes))
            stage.deny("Adaptive ground transfer destination changed", 0x547160);
        // Allocate and stage BOTH complete transfers before any guest write.
        // The main-thread buffers are reused; workers never reference them.
        if (stage.adaptive_ground_vertex_staging.size() != 1024)
            stage.adaptive_ground_vertex_staging.resize(1024);
        if (stage.adaptive_ground_triangle_staging.size() != 2048)
            stage.adaptive_ground_triangle_staging.resize(2048);
        auto vertex_records = std::span(stage.adaptive_ground_vertex_staging).first(vertices);
        auto triangle_records = std::span(stage.adaptive_ground_triangle_staging).first(triangles);
        stage.get_bytes(0x65ddf8, vertex_records.data(), vertex_bytes);
        encode_preprojection_vertices(*result, input_count, vertex_records);
        // Temporarily inactive faces skip the already computed refinement.
        encode_triangles(*result, triangle_records, false);
        stage.write_bytes(0x65ddf8, vertex_records.data(), vertex_bytes);
        stage.write_bytes(0x64fdf0, triangle_records.data(), triangle_bytes);
        stage.store(0x64fbe8, unsigned(result->vertices.size()));
        stage.store(0x64fbec, unsigned(result->triangles.size()));
        consumed = true;
        ++stage.adaptive_ground_metrics.consumed;
        if (from_worker) {
            ++stage.adaptive_ground_metrics.worker_consumed;
            if (check)
                std::fprintf(stderr, "Adaptive ground consume: frame=%llu node=%u polygon=%u\n",
                             static_cast<unsigned long long>(result->identity.camera.frame),
                             result->identity.source_node, result->identity.polygon);
        }
        const unsigned continuation = stage.load(sp);
        stage.state.gpr.rsp.dword = sp + 4;
        stage.state.gpr.rip.dword = continuation;
        stage.returned(&stage.state, continuation, memory);
        return true;
    }

    void before_projection() {
        if (!consumed || restored || stage.load(stage.state.gpr.rsp.dword) != 0x547fe4)
            return;
        SunCaptureFp preserve;
        const unsigned triangles = unsigned(result->triangles.size());
        auto records = std::span(stage.adaptive_ground_triangle_staging).first(triangles);
        mw34::adaptive_ground::encode_triangles(*result, records, true);
        stage.write_bytes(0x64fdf0, records.data(),
                          triangles * unsigned(sizeof(mw34::adaptive_ground::GuestTriangleRecord)));
        if (result->distance_written)
            for (unsigned axis = 0; axis < 3; ++axis)
                stage.store(0x63d328 + axis * 4,
                            std::bit_cast<unsigned>(result->distance_delta[axis]));
        restored = true;
    }

    void compare_packet() {
        SunCaptureFp preserve;
        if (!result || !result->prepared || packet >= result->triangles.size())
            stage.deny("Unexpected original adaptive triangle callback", 0x57ea20);
        const auto &face = result->triangles[packet];
        const unsigned sp = stage.state.gpr.rsp.dword;
        stage.adaptive_ground_word(sp + 4, 3);
        const unsigned rgb = stage.state.gpr.rcx.dword;
        for (unsigned corner = 0; corner < 3; ++corner) {
            const auto &vertex = result->vertices[face.vertices[corner]];
            for (unsigned axis = 0; axis < 3; ++axis) {
                stage.adaptive_ground_float_word(0x72f41c + corner * 32 + axis * 4,
                                                 vertex.screen[axis]);
                stage.adaptive_ground_float_word(0x7481b4 + corner * 32 + axis * 4,
                                                 vertex.modulation[axis]);
                stage.adaptive_ground_float_word(rgb + corner * 12 + axis * 4, vertex.lit[axis]);
            }
            for (unsigned axis = 0; axis < 2; ++axis)
                stage.adaptive_ground_float_word(0x72f434 + corner * 32 + axis * 4,
                                                 vertex.uv[0][axis]);
            stage.adaptive_ground_float_word(0x7481b0 + corner * 32, vertex.fog);
        }
        ++packet;
    }

    void compare_result() {
        const auto &expected = *result;
        stage.adaptive_ground_word(0x65ddf0, unsigned(expected.selected_lights.size()));
        for (unsigned index = 0; index < expected.selected_lights.size(); ++index)
            stage.adaptive_ground_word(0x64fbf0 + index * 4,
                                       light_addresses[expected.selected_lights[index]]);
        if (stage.state.gpr.rax.dword != unsigned(expected.prepared))
            stage.deny("Adaptive ground return-value mismatch", 0x547740);
        if (expected.distance_written)
            for (unsigned axis = 0; axis < 3; ++axis)
                stage.adaptive_ground_float_word(0x63d328 + axis * 4,
                                                 expected.distance_delta[axis]);
        if (!expected.vertices.empty()) {
            stage.adaptive_ground_word(0x64fbe8, unsigned(expected.vertices.size()));
            for (unsigned index = 0; index < expected.vertices.size(); ++index) {
                const auto &vertex = expected.vertices[index];
                const unsigned base = 0x65ddf8 + index * 132;
                for (unsigned axis = 0; axis < 3; ++axis)
                    stage.adaptive_ground_float_word(base + axis * 4, vertex.camera[axis]);
                if (!expected.prepared)
                    continue;
                for (unsigned axis = 0; axis < 3; ++axis) {
                    stage.adaptive_ground_float_word(base + 12 + axis * 4, vertex.screen[axis]);
                    stage.adaptive_ground_float_word(base + 0x5c + axis * 4, vertex.base[axis]);
                    stage.adaptive_ground_float_word(base + 0x68 + axis * 4,
                                                     vertex.modulation[axis]);
                    stage.adaptive_ground_float_word(base + 0x74 + axis * 4, vertex.lit[axis]);
                }
                for (unsigned axis = 0; axis < 2; ++axis)
                    stage.adaptive_ground_float_word(base + 0x18 + axis * 4, vertex.uv[0][axis]);
                stage.adaptive_ground_float_word(base + 0x58, vertex.fog);
                if (index >= input_count)
                    stage.adaptive_ground_word(base + 0x80, unsigned(vertex.boundary));
            }
            if (!expected.prepared)
                for (unsigned axis = 0; axis < 3; ++axis)
                    stage.adaptive_ground_float_word(0x65ddf8 + input_count * 132 + axis * 4,
                                                     expected.centroid[axis]);
        }
        if (expected.prepared) {
            stage.adaptive_ground_word(0x64fbec, unsigned(expected.triangles.size()));
            for (unsigned index = 0; index < expected.triangles.size(); ++index) {
                const auto &face = expected.triangles[index];
                const unsigned base = 0x64fdf0 + index * 28;
                for (unsigned edge = 0; edge < 3; ++edge) {
                    stage.adaptive_ground_word(base + edge * 4, face.vertices[edge]);
                    stage.adaptive_ground_word(base + 12 + edge * 4,
                                               unsigned(face.neighbors[edge]));
                }
                stage.adaptive_ground_word(base + 24, unsigned(face.active));
            }
        }
        if (packet != expected.triangles.size())
            stage.deny("Adaptive ground callback count/order mismatch", 0x547740);
        ++stage.adaptive_ground_metrics.calls;
        stage.adaptive_ground_metrics.vertices += expected.vertices.size();
        stage.adaptive_ground_metrics.packets += packet;
    }

    ~AdaptiveGroundCheck() noexcept(false) {
        SunCaptureFp preserve;
        stage.adaptive_ground_active = previous;
        // Release owned storage before restoring the guest's actual host FP
        // environment and LastError, including after an original guest fault.
        auto release = [&] {
            result.reset();
            std::vector<unsigned>().swap(light_addresses);
        };
        try {
            if (consumed && !restored && !std::uncaught_exceptions())
                stage.deny("Adaptive ground original projection was not reached", 0x547740);
            if (check && result && !std::uncaught_exceptions())
                compare_result();
        } catch (...) {
            release();
            throw;
        }
        release();
    }
};

bool adaptive_ground_projection_pending() const {
    return adaptive_ground_active && adaptive_ground_active->consumed &&
           !adaptive_ground_active->restored;
}

bool adaptive_ground_split_pending() const {
    return adaptive_ground_active && adaptive_ground_active->admitted &&
           !adaptive_ground_active->consumed;
}

template <class Action> void *adaptive_ground_body(unsigned target, void *memory, Action action) {
    if (!adaptive_ground_any_enabled() || (!adaptive_ground_enabled() && !adaptive_ground_sample()))
        return action();
    if (target == 0x53f2e0) {
        struct Restore {
            unsigned &destination;
            unsigned previous;
            ~Restore() { destination = previous; }
        } restore{adaptive_ground_node, adaptive_ground_node};
        adaptive_ground_node = state.gpr.rcx.dword;
        AdaptiveGroundMesh mesh(*this, adaptive_ground_node);
        struct RestoreMesh {
            AdaptiveGroundMesh *&destination;
            AdaptiveGroundMesh *previous;
            ~RestoreMesh() { destination = previous; }
        } restore_mesh{adaptive_ground_mesh, adaptive_ground_mesh};
        adaptive_ground_mesh = &mesh;
        return action();
    }
    if (target == 0x545720 && adaptive_ground_mesh)
        adaptive_ground_mesh->schedule();
    if (target == 0x547740) {
        AdaptiveGroundCheck check(*this);
        return action();
    }
    if (target == 0x547160 && adaptive_ground_active &&
        adaptive_ground_active->consume_split(memory))
        return memory;
    if (target == 0x523540 && adaptive_ground_active)
        adaptive_ground_active->before_projection();
    if (target == 0x57ea20 && adaptive_ground_active && adaptive_ground_active->check)
        adaptive_ground_active->compare_packet();
    return action();
}
