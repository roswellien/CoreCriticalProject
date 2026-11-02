static void polygon_require(bool good, const char *message) {
    if (!good)
        throw std::runtime_error(message);
}
// Exercise the native polygon adapter, including the expensive reconstruction
// branch. Original guest memory is replaced by authored words and TL vertices.
struct WorldPolygonCaptureFixture {
    static constexpr unsigned D3DPT_TRIANGLEFAN = 6, WideWorld = 1;
    static constexpr unsigned D3DRENDERSTATE_ALPHATESTENABLE = 15;
    static constexpr unsigned D3DRENDERSTATE_ALPHABLENDENABLE = 27;
    using OverrideMatrix = std::array<double, 16>;
    struct Corner {
        ModelVertex vertex{};
    };
    struct Polygon {
        std::vector<Corner> corners;
        unsigned material{}, flags{}, source{0x5000};
        std::shared_ptr<const ModelGeometry> resident;
    };
    struct WorldScope {
        unsigned node{9}, mesh{10}, frame_base{0x2000}, polygon_base{0x5000};
        bool temporal_only{true};
        std::shared_ptr<std::vector<Polygon>> polygons;
        std::shared_ptr<std::vector<int>> polygon_lookup;
    };
    struct D3DCmd {
        unsigned flags{D3DPT_TRIANGLEFAN}, hud_role{WideWorld};
        unsigned fixture_node{}, fixture_polygon{};
        std::vector<unsigned short> indices;
        std::vector<unsigned char> vertices;
        std::shared_ptr<const std::vector<unsigned>> state_snapshot;
        std::shared_ptr<const ModelInstance> model;
    };
    struct WorldTicks {
        explicit WorldTicks(std::uint64_t &) {}
    };
    std::shared_ptr<WorldScope> world_scope;
    unsigned world_cell_depth{1}, edge_calls{}, lighting_calls{};
    std::uint64_t world_binding_ticks{}, world_misses{}, world_draws{};
    std::uint64_t world_fast_corners{}, world_audited_corners{};
    std::map<unsigned, unsigned> words{
        {0x1fc8, 10}, {0x1fcc, 0x5000}, {0x5eda90, 0x3000}, {0x3000, 0x4000}};
    bool readable(unsigned, unsigned) const { return true; }
    unsigned load(unsigned address) const { return words.at(address); }
    bool override_suppress_draw() const { return false; }
    bool frontend_on() const { return false; }
    bool world_fast_enabled() const { return false; }
    float world_float(unsigned address) const {
        switch (address) {
        case 0x73fb80:
            return 1;
        case 0x73fc30:
        case 0x73fb98:
        case 0x73fb88:
        case 0x73fb8c:
            return 32;
        case 0x740304:
            return .1f;
        default:
            throw std::runtime_error("Unexpected polygon projection read");
        }
    }
    OverrideMatrix override_matrix(unsigned address) const {
        polygon_require(address == 0x4000, "Polygon capture read another matrix");
        return {1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1};
    }
    void sun_capture_world(ModelInstance &, unsigned) { ++lighting_calls; }
    bool world_edge_admit(D3DCmd &command, const Polygon &, const OverrideMatrix &, double, double,
                          double, double, double, double) {
        ++edge_calls;
        // An authoritative draw may reconstruct a polygon; a temporal-only
        // candidate must not reach this work and then discard its result.
        command.vertices = original().vertices;
        return true;
    }
#include "world_polygon_capture_stage.inc"
    WorldPolygonCaptureFixture() {
        world_scope = std::make_shared<WorldScope>();
        Polygon polygon;
        polygon.corners = {{{-1, -1, 2, 0, 0, 1, 0, 0}},
                           {{1, -1, 2, 0, 0, 1, 1, 0}},
                           {{0, 1, 2, 0, 0, 1, .5f, 1}}};
        auto geometry = std::make_shared<ModelGeometry>();
        for (auto i = polygon.corners.rbegin(); i != polygon.corners.rend(); ++i)
            geometry->vertices.push_back(i->vertex);
        polygon.resident = geometry;
        world_scope->polygons = std::make_shared<std::vector<Polygon>>(1, polygon);
        world_scope->polygon_lookup = std::make_shared<std::vector<int>>(1, 0);
    }
    D3DCmd original() const {
        D3DCmd command;
        command.state_snapshot = std::make_shared<const std::vector<unsigned>>(256, 0);
        for (auto i = world_scope->polygons->front().corners.rbegin();
             i != world_scope->polygons->front().corners.rend(); ++i) {
            const auto &v = i->vertex;
            const TlVertex tl{v.x * 16 + 32, v.y * 16 + 32, .5f, .5f,
                              0xff123456,    0xff000000,    v.u, v.v};
            const auto *bytes = reinterpret_cast<const unsigned char *>(&tl);
            command.vertices.insert(command.vertices.end(), bytes, bytes + sizeof(tl));
        }
        return command;
    }
};
static void world_polygon_capture_checks() {
    WorldPolygonCaptureFixture exact;
    auto command = exact.original();
    const auto original = command.vertices;
    exact.world_capture(command);
    polygon_require(command.model && command.model->world && command.vertices == original,
                    "Exact temporal polygon lost its original attributes or raw geometry");
    polygon_require(command.fixture_node == 9 && command.fixture_polygon == 0x5000,
                    "Exact temporal polygon lost source identity");
    polygon_require(exact.edge_calls == 0 && exact.world_draws == 1,
                    "Exact temporal polygon unnecessarily reconstructed");
    for (unsigned mutation = 0; mutation < 5; ++mutation) {
        WorldPolygonCaptureFixture fixture;
        auto changed = fixture.original();
        TlVertex first;
        std::memcpy(&first, changed.vertices.data(), sizeof(first));
        if (mutation == 0)
            first.x += .1f;
        if (mutation == 1)
            first.u += .01f;
        if (mutation == 2)
            first.z = first.rhw = .4f;
        if (mutation == 3)
            first.x = std::numeric_limits<float>::quiet_NaN();
        std::memcpy(changed.vertices.data(), &first, sizeof(first));
        if (mutation == 4)
            changed.vertices.resize(changed.vertices.size() + sizeof(first));
        const auto unchanged = changed.vertices;
        fixture.world_capture(changed);
        polygon_require(!changed.model && changed.vertices == unchanged,
                        "Rejected temporal polygon changed authoritative TL attributes");
        polygon_require(fixture.edge_calls == 0 && fixture.lighting_calls == 0 &&
                            fixture.world_misses == 1,
                        "Rejected temporal polygon performed reconstruction or lighting");
        fixture.world_scope->temporal_only = false;
        fixture.world_capture(changed);
        polygon_require(changed.model && fixture.edge_calls == 1 && fixture.lighting_calls == 1,
                        "Authoritative polygon lost its existing reconstruction route");
    }
    std::cout << "Native polygon adapter: exact temporal identity, rejected attributes and "
                 "unchanged authoritative reconstruction pass\n";
}
