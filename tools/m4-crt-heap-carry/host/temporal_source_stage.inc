// Capture the original node/parent ownership ranges once, independently of lighting.
bool capture_node_ranges(unsigned node,
                         std::vector<std::pair<unsigned, std::vector<unsigned char>>> &ranges,
                         unsigned root = 0) {
    const bool temporal_capture = root != 0;
    auto failure = [&](unsigned at, const char *reason) {
        temporal_range_failure_node = at;
        temporal_range_failure = reason;
        return false;
    };
    auto snapshot = [&](unsigned address, unsigned bytes) {
        if (!readable(address, bytes))
            return failure(node, "unreadable-range");
        std::vector<unsigned char> data(bytes);
        get_bytes(address, data.data(), bytes);
        ranges.push_back({address, std::move(data)});
        if (temporal_capture)
            temporal_track_source(address);
        return true;
    };
    if (!root) {
        const unsigned context = load(0x5f4c8c);
        root = context && readable(context, 4) ? load(context) : 0;
    }
    if (!root)
        return failure(node, "no-root");
    for (unsigned depth = 0; node != root && depth < 32; ++depth) {
        // Names, type/data/mesh identity and child ownership are stable.
        // +0x24 visibility/render flags are deliberately not source lifetime.
        if (!snapshot(node, 36) || !snapshot(node + 0x34, 12) || !snapshot(node + 0x5c, 8))
            return failure(node, "node-ranges");
        if (load(node + 0x34) == 5 && !snapshot(load(node + 0x38), 96))
            return failure(node, "pose-range");
        if (temporal_capture &&
            (!snapshot(node + 0x54, 8) || load(node + 0x54) != 1 ||
             !snapshot(load(node + 0x58), 4)))
            return failure(node, "parent-storage");
        const unsigned parent = override_parent(node);
        if (!parent || !readable(parent, 100))
            return failure(node, "parent-edge");
        const unsigned count = load(parent + 0x5c), children = load(parent + 0x60);
        if (count > 65536 || !count || !readable(children, count * 4))
            return failure(node, "child-array");
        bool member = false;
        for (unsigned i = 0; i < count; ++i)
            if (load(children + i * 4) == node) {
                member = snapshot(parent + 0x5c, 8) && snapshot(children + i * 4, 4);
                break;
            }
        if (!member)
            return failure(node, "not-reciprocal");
        node = parent;
    }
    if (node != root)
        return failure(node, "wrong-root");
    return true;
}

std::map<unsigned, std::shared_ptr<const mw34::world::SourceBytes>> temporal_node_bytes;
std::set<unsigned> temporal_tracked_nodes;
std::vector<std::shared_ptr<const mw34::world::SourceCharge>> temporal_tracked_charges;
void temporal_track_source(unsigned address) {
    // Include the lookup ownership records as well as mesh/pose bytes. A free
    // followed by identical bytes at the same address is still a new lifetime.
    if (!temporal_tracked_nodes.contains(address) && temporal_tracked_nodes.size() >= 131072)
        throw std::runtime_error("Temporal tracked source address capacity exceeded");
    if (!temporal_tracked_nodes.contains(address)) {
        // Charge lookup ownership too, in bounded blocks rather than spending
        // one snapshot entry for every address in a captured range list.
        if (temporal_tracked_nodes.size() % 1024 == 0)
            temporal_tracked_charges.push_back(world_meshes.charge(1024 * 64));
        temporal_tracked_nodes.insert(address);
    }
}
std::uint64_t temporal_source_epoch{}, temporal_source_draws{}, temporal_source_admitted{},
    temporal_source_pairs{};
unsigned temporal_source_types{};
const char *temporal_source_rejection = "none";
std::array<char, 240> temporal_source_diagnostic{};
unsigned temporal_range_failure_node{};
const char *temporal_range_failure = "none";
std::uint64_t temporal_source_diagnostic_frame{~std::uint64_t{}};
std::map<std::pair<unsigned, unsigned>, std::shared_ptr<const mw34::temporal::StaticSource>>
    temporal_source_previous, temporal_source_current;
std::uint64_t temporal_source_frame{~std::uint64_t{}};
std::uint64_t temporal_source_load_epoch{~std::uint64_t{}};

void temporal_source_load() {
    const auto epoch = mw34::campaign::CampaignManager::instance().reader_epoch();
    if (epoch == temporal_source_load_epoch)
        return;
    temporal_source_load_epoch = epoch;
    camera_advance(temporal_source_epoch);
    temporal_node_bytes.clear();
    temporal_tracked_nodes.clear();
    temporal_tracked_charges.clear();
    temporal_source_previous.clear();
    temporal_source_current.clear();
    world_meshes.clear();
    temporal_source_frame = ~std::uint64_t{};
}


void temporal_source_retire(unsigned object) {
    if (!mw34::temporal::enabled() || !temporal_tracked_nodes.count(object))
        return;
    camera_advance(temporal_source_epoch);
    temporal_node_bytes.clear();
    temporal_tracked_nodes.clear();
    temporal_tracked_charges.clear();
    temporal_source_previous.clear();
    temporal_source_current.clear();
    if (host.sren)
        host.sren->invalidate_camera_history(mw34::temporal::Reset::transition);
}
void temporal_source_freed(unsigned address, unsigned bytes) {
    if (!mw34::temporal::enabled())
        return;
    SunCaptureFp preserve;
    const auto found = temporal_tracked_nodes.lower_bound(address);
    if (found != temporal_tracked_nodes.end() &&
        std::uint64_t(*found) < std::uint64_t(address) + bytes)
        temporal_source_retire(*found);
}
struct TemporalCellScope {
    unsigned owner{}, data{}, frame{}, camera{};
};
struct TemporalPlacement {
    unsigned owner{}, data{}, cell{}, record{}, root{}, route{};
    std::uint64_t epoch{};
    std::array<unsigned, 3> offset{};
    OverrideMatrix world{};
    std::vector<std::pair<unsigned, std::vector<unsigned char>>> ranges;
};
TemporalCellScope temporal_cell_scope;
std::shared_ptr<const TemporalPlacement> temporal_placement;
std::uint64_t temporal_cell_calls{}, temporal_placement_calls{}, temporal_record_matches{};

std::shared_ptr<const TemporalPlacement> temporal_cell_record(unsigned site, unsigned root) {
    const auto &scope = temporal_cell_scope;
    auto reject = [&](const char *reason) -> std::shared_ptr<const TemporalPlacement> {
        temporal_source_rejection = reason;
        return {};
    };
    if (!scope.owner || !readable(scope.owner, 0x64) || load(scope.owner + 0x38) != scope.data ||
        !readable(scope.data, 0xb0) || state.gpr.rbp.dword != scope.frame ||
        !readable(scope.frame - 0x5c, 0x60) || load(scope.frame - 0xc) != scope.data)
        return reject("cell-scope");
    const unsigned cell = load(scope.frame - 0x38), bank = load(0x5ea534),
                   index = load(scope.frame - 0x24);
    if (bank >= 50 || index >= 30 || load(scope.frame - 8) != index * 24 ||
        load(0x736910 + bank * 0x2d4) > 30 || index >= load(0x736910 + bank * 0x2d4))
        return reject("cell-selection");
    const unsigned selected = 0x736640 + bank * 0x2d4 + index * 24;
    const unsigned cell_index = load(selected), sector = load(selected + 4),
                   arrays = load(scope.data + 0x90);
    if (cell_index > 65535 || sector > 65535 || !arrays || !readable(arrays, (sector + 1) * 4))
        return reject("cell-array");
    const unsigned base = load(arrays + sector * 4);
    if (std::uint64_t(base) + std::uint64_t(cell_index) * 72 != cell || !readable(cell, 72))
        return reject("cell-record");
    if ((site == 0x4f6b59) != (load(selected + 8) != 0))
        return reject("cell-route-selection");
    auto result = std::make_shared<TemporalPlacement>();
    result->epoch = temporal_source_epoch;
    result->owner = scope.owner;
    result->data = scope.data;
    result->cell = cell;
    result->root = root;
    result->route = site;
    auto capture = [&](unsigned address, unsigned size) {
        if (!readable(address, size))
            throw std::runtime_error("Temporal cell source range is unavailable");
        std::vector<unsigned char> bytes(size);
        get_bytes(address, bytes.data(), size);
        result->ranges.emplace_back(address, std::move(bytes));
        temporal_track_source(address);
    };
    capture(scope.owner + 0x34, 12);
    capture(scope.data + 0x90, 4);
    capture(arrays + sector * 4, 4);
    capture(cell, 72);
    if (site == 0x4f6ae0) {
        const unsigned count = load(cell + 0x40), records = load(cell + 0x44),
                       record = state.gpr.rbx.dword;
        if (!count || count > 65536 || !records || !readable(records, count * 0x44) ||
            record < records || (record - records) % 0x44 || (record - records) / 0x44 >= count ||
            load(record) != root)
            return reject("placement-record");
        unsigned matches = 0;
        for (unsigned i = 0; i < count; ++i)
            matches += load(records + i * 0x44) == root;
        if (matches != 1 || !readable(root, 0x64) || load(root + 0x34) != 5)
            return reject("placement-root");
        const unsigned data = load(root + 0x38);
        if (!data || !readable(data, 0x90) || (load(data) & 8))
            return reject("placement-storage");
        for (unsigned i = 0; i < 12; ++i)
            if (load(record + 4 + i * 4) != load(data + 0x30 + i * 4) ||
                load(record + 4 + i * 4) != load(data + 0x60 + i * 4))
                return reject("placement-copy");
        result->record = record;
        result->world = override_matrix(record + 4);
        capture(record, 0x40);
    } else if (site == 0x4f6b59 || site == 0x4f69dc) {
        const unsigned count = load(cell + 0x38) >> 16, records = load(cell + 0x3c),
                       i = state.gpr.rsi.dword;
        if (!count || count > 32767 || i >= count || !records || !readable(records, count * 4) ||
            load(records + i * 4) != root || !readable(root, 0x64) || load(root + 0x34) != 5)
            return reject("object-list");
        unsigned matches = 0;
        for (unsigned j = 0; j < count; ++j)
            matches += load(records + j * 4) == root;
        if (matches != 1)
            return reject("object-alias");
        const unsigned data = load(root + 0x38);
        if (!data || !readable(data, 0x90))
            return reject("object-storage");
        // This route calls the type-5 subtree directly from the camera stack;
        // it does not copy a placement-record matrix into the node.
        result->record = records + i * 4;
        result->world = (load(data) & 8) ? override_identity() : override_matrix(data + 0x30);
        capture(result->record, 4);
    } else
        return reject("cell-callsite");
    const unsigned data = load(root + 0x38);
    capture(root, 36);
    capture(root + 0x34, 12);
    capture(root + 0x5c, 8);
    capture(data + 0x30, 48);
    // The render cache at data+60 is camera dependent (51E930/51FEE0).
    // It was checked at the placement producer, not used as a stable fingerprint.
    for (unsigned i = 0; i < 3; ++i)
        result->offset[i] = load(0x73fbb0 + i * 4);
    temporal_track_source(scope.owner);
    temporal_track_source(scope.data);
    temporal_track_source(root);
    temporal_track_source(data);
    temporal_track_source(arrays);
    ++temporal_record_matches;
    return result;
}

template <class Next> void *temporal_cell_body(unsigned target, Next &&next) {
    if ((target != 0x4f6720 && target != 0x4f5910) || !mw34::temporal::enabled())
        return next();
    using Owner = std::remove_reference_t<decltype(*this)>;
    struct Restore {
        Owner &stage;
        TemporalCellScope cell;
        std::shared_ptr<const TemporalPlacement> placement;
        ~Restore() {
            stage.temporal_cell_scope = cell;
            stage.temporal_placement = std::move(placement);
        }
    } restore{*this, temporal_cell_scope, temporal_placement};
    {
        SunCaptureFp preserve;
        mw34::vkscene::HostFpEnvironment fp;
        const unsigned stack = state.gpr.rsp.dword;
        if (target == 0x4f6720) {
            temporal_source_load();
            ++temporal_cell_calls;
            const unsigned owner = state.gpr.rcx.dword;
            temporal_cell_scope = {owner, owner && readable(owner, 0x3c) ? load(owner + 0x38) : 0,
                                   stack - 4, readable(stack + 4, 4) ? load(stack + 4) : 0};
            temporal_placement.reset();
        } else if (temporal_cell_scope.owner && readable(stack, 4)) {
            const unsigned site = load(stack);
            if (site == 0x4f6ae0 || site == 0x4f6b59 || site == 0x4f69dc) {
                ++temporal_placement_calls;
                temporal_placement = temporal_cell_record(site, state.gpr.rcx.dword);
            }
        }
    }
    return next();
}

void temporal_source_capture(D3DCmd &draw) {
    if (!mw34::temporal::enabled() || !draw.model || !draw.model->world || !draw.camera_view)
        return;
    SunCaptureFp preserve;
    mw34::vkscene::HostFpEnvironment fp;
    ++temporal_source_draws;
    auto reject = [&](const char *reason) { temporal_source_rejection = reason; };
    if (!world_scope || !world_scope->source_bytes || world_scope->node != draw.fixture_node) {
        reject("source-scope");
        return;
    }
    const auto frame = camera_flip_serial + 1;
    if (temporal_source_frame != frame) {
        if (temporal_source_frame + 1 == frame)
            temporal_source_previous = std::move(temporal_source_current);
        else
            temporal_source_previous.clear();
        temporal_source_current.clear();
        temporal_source_frame = frame;
    }
    if (!temporal_placement || temporal_placement->epoch != temporal_source_epoch) {
        reject("no-cell-placement");
        return;
    }
    const auto &placement = *temporal_placement;
    const unsigned root = placement.root;
    std::vector<std::pair<unsigned, std::vector<unsigned char>>> ranges = placement.ranges;
    if (!capture_node_ranges(draw.fixture_node, ranges, root)) {
        reject("cell-descendant");
        return;
    }
    OverrideMatrix local_world = override_identity();
    unsigned node = draw.fixture_node;
    for (unsigned depth = 0; node != root && depth < 32; ++depth) {
        const auto type = load(node + 0x34);
        temporal_source_types |= 1U << std::min(type, 31U);
        if (type != 5) {
            reject("cell-descendant-type");
            return;
        }
        const unsigned data = load(node + 0x38);
        if (!data || !readable(data, 0x90)) {
            reject("cell-descendant-storage");
            return;
        }
        auto local = (load(data) & 8) ? override_identity() : override_matrix(data + 0x30);
        local_world = override_product(local, local_world);
        temporal_track_source(node);
        temporal_track_source(data);
        node = override_parent(node);
    }
    if (node != root) {
        reject("cell-descendant-chain");
        return;
    }
    const OverrideMatrix world = override_product(placement.world, local_world);
    const auto camera_world = sun_view_binding.matrix();
    const auto expected = override_product(override_inverse(camera_world), world);
    for (unsigned i = 0; i < 12; ++i)
        if (!std::isfinite(world[i]) || !std::isfinite(expected[i]) ||
            !std::isfinite(draw.model->camera[i])) {
            reject("source-nonfinite");
            return;
        }
    // Compare in the producer's screen units, using original projection admission.
    const auto &projection = draw.model->projection;
    for (const auto &vertex : draw.model->geometry->vertices) {
        const double point[]{vertex.x, vertex.y, vertex.z, 1};
        double camera[3]{}, actual[3]{};
        for (unsigned row = 0; row < 3; ++row)
            for (unsigned col = 0; col < 4; ++col) {
                camera[row] += expected[row * 4 + col] * point[col];
                actual[row] += draw.model->camera[row * 4 + col] * point[col];
            }
        if (camera[2] <= projection[5] || actual[2] <= projection[5]) {
            reject("source-near");
            return;
        }
        for (unsigned axis = 0; axis < 2; ++axis)
            if (std::abs((camera[axis] / camera[2] - actual[axis] / actual[2]) * projection[0] *
                         projection[1 + axis]) > .02) {
                reject("source-transform");
                return;
            }
        if (std::abs(projection[0] / camera[2] - projection[0] / actual[2]) >
            std::max(1e-7, std::abs(projection[0] / actual[2]) * 1e-5)) {
            reject("source-depth");
            return;
        }
    }
    std::vector<unsigned char> bytes;
    for (const auto &[address, data] : ranges) {
        const unsigned size = unsigned(data.size());
        for (unsigned word : {address, size})
            for (unsigned shift = 0; shift < 32; shift += 8)
                bytes.push_back(static_cast<unsigned char>(word >> shift));
        bytes.insert(bytes.end(), data.begin(), data.end());
    }
    auto &owned = temporal_node_bytes[draw.fixture_node];
    if (!owned || owned->bytes != bytes)
        owned = world_meshes.retain(std::move(bytes));
    auto charge = world_meshes.charge(sizeof(mw34::temporal::StaticSource) + 64);
    auto source = std::make_shared<mw34::temporal::StaticSource>();
    source->charge = std::move(charge);
    source->frame = frame;
    source->load_epoch = draw.camera_view->load_epoch;
    source->cell_owner = placement.owner;
    source->cell = placement.cell;
    source->record = placement.record;
    source->route = placement.route;
    source->offset = placement.offset;
    source->node = draw.fixture_node;
    source->mesh = world_scope->mesh;
    source->polygon = draw.fixture_polygon;
    source->epoch = temporal_source_epoch;
    source->mesh_bytes = world_scope->source_bytes;
    source->node_bytes = owned;
    for (unsigned i = 0; i < 12; ++i)
        source->world[i] = float(world[i]);
    if (draw.texture) {
        const auto *surface = vsurface(draw.texture);
        if (!surface) {
            reject("source-texture");
            return;
        }
        source->texture = surface->guest;
        source->texture_version = surface->version;
    }
    const auto key = std::make_pair(source->node, source->polygon);
    const auto previous = temporal_source_previous.find(key);
    if (previous != temporal_source_previous.end() && source->unchanged(*previous->second))
        source->previous_static = true, ++temporal_source_pairs;
    temporal_source_current.insert_or_assign(key, source);
    draw.temporal_source = std::move(source);
    ++temporal_source_admitted;
}
