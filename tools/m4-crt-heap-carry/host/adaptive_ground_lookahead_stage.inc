// Included inside Stage after the shared numeric capture. All guest observation,
// lifetime checks, waits and ordered consumption stay on the original thread.
unsigned adaptive_ground_worker_count() {
    static const unsigned count = [] {
        SunCaptureFp preserve;
        const char *value = std::getenv("MW34_ADAPTIVE_WORKERS");
        if (!value || !*value || !std::strcmp(value, "2"))
            return 2U;
        if (!std::strcmp(value, "inline"))
            return 0U;
        if (!std::strcmp(value, "1"))
            return 1U;
        if (!std::strcmp(value, "4"))
            return 4U;
        throw std::runtime_error("MW34_ADAPTIVE_WORKERS must be inline, 1, 2 or 4");
    }();
    static const unsigned actual = [] {
        SunCaptureFp preserve;
        return count ? mw34::adaptive_ground::bounded_worker_count(
                           count, std::thread::hardware_concurrency())
                     : 0;
    }();
    return actual;
}

struct AdaptiveGroundWorkers {
    std::unique_ptr<mw34::adaptive_ground::JobPool> pool;
    std::uint64_t queued{}, matched{}, discarded{}, waits{}, meshes{};
    ~AdaptiveGroundWorkers() {
        if (!pool)
            return;
        SunCaptureFp preserve;
        // Mesh scopes have already drained their owned handles. Joining also
        // covers shutdown after a guest fault or a nonlocal return.
        const auto peak = pool->peak_active();
        for (const auto &span : pool->spans())
            std::fprintf(stderr,
                         "Adaptive ground span: frame=%llu node=%u polygon=%u worker=%u "
                         "begin=%llu end=%llu refined=%u\n",
                         static_cast<unsigned long long>(span.frame), span.node, span.polygon,
                         span.worker, static_cast<unsigned long long>(span.begin),
                         static_cast<unsigned long long>(span.end), unsigned(span.refined));
        if (pool->span_overflow())
            std::fprintf(stderr, "Adaptive ground span capacity exceeded\n");
        pool.reset();
        std::fprintf(
            stderr,
            "Adaptive ground workers: %llu meshes, %llu queued, %llu matched, "
            "%llu discarded, %llu boundary waits, peak %u active jobs\n",
            static_cast<unsigned long long>(meshes), static_cast<unsigned long long>(queued),
            static_cast<unsigned long long>(matched), static_cast<unsigned long long>(discarded),
            static_cast<unsigned long long>(waits), peak);
    }
} adaptive_ground_workers;

struct AdaptiveGroundMesh {
    struct SourceRange {
        unsigned address{};
        std::vector<unsigned char> bytes;
    };
    struct Pending {
        mw34::adaptive_ground::Input input;
        std::vector<SourceRange> source;
        std::future<mw34::adaptive_ground::Result> completion;
        bool used{};
    };
    Stage &stage;
    unsigned node{};
    bool attempted{}, allow_lookahead{};
    std::vector<Pending> pending;

    AdaptiveGroundMesh(Stage &owner, unsigned source)
        : stage(owner), node(source), allow_lookahead(!owner.adaptive_ground_mesh) {}
    ~AdaptiveGroundMesh() noexcept(false) {
        SunCaptureFp preserve;
        // Work never crosses a mesh invocation or retains any guest/GPU owner.
        // Drain obsolete work as well as unused candidates before destruction.
        std::exception_ptr first_error;
        for (auto &item : pending)
            if (item.completion.valid()) {
                mw34::adaptive_ground::drain_completion(item.completion, first_error);
                if (!item.used)
                    ++stage.adaptive_ground_workers.discarded;
            }
        std::vector<Pending>().swap(pending);
        if (first_error) {
            if (!std::uncaught_exceptions())
                std::rethrow_exception(first_error);
            // Preserve an already propagating guest fault; a second exception
            // from this destructor would terminate before the original report.
            std::fprintf(stderr, "Adaptive ground worker failed while unwinding a guest fault\n");
        }
    }

    bool capture(std::vector<SourceRange> &ranges, unsigned address, unsigned bytes) {
        if (!address || !bytes || bytes > 128 * 12 || !stage.readable(address, bytes))
            return false;
        SourceRange range{address, std::vector<unsigned char>(bytes)};
        stage.get_bytes(address, range.bytes.data(), bytes);
        ranges.push_back(std::move(range));
        return true;
    }

    void schedule() {
        if (!allow_lookahead || attempted || !stage.adaptive_ground_enabled() ||
            !stage.adaptive_ground_worker_count())
            return;
        attempted = true;
        SunCaptureFp preserve;
        using namespace mw34::adaptive_ground;
        const unsigned sp = stage.state.gpr.rsp.dword, bp = stage.state.gpr.rbp.dword;
        if (!node || !stage.readable(node + 0x3c, 4) || !stage.readable(sp, 24) ||
            stage.load(sp) != 0x53ff3a || stage.load(sp + 16) != 1 || stage.load(sp + 20) != 3 ||
            stage.load(0x5ef860) || bp < 0x34 || !stage.readable(bp - 0x34, 4))
            return;
        const unsigned mesh = stage.load(node + 0x3c);
        if (!mesh || !stage.readable(mesh, 0x48) || stage.load(mesh) || stage.load(mesh + 12) > 1 ||
            stage.load(mesh + 0x1c) || stage.load(mesh + 0x20))
            return;
        const auto identity = stage.adaptive_ground_context(node, mesh, 0, 0);
        if (!identity)
            return;
        auto common = stage.adaptive_ground_shared_input();
        if (common.input.extra_uv_layers || common.input.guest_control_word != 0x023f)
            return;
        // The original baked prelude excludes sky/directional contributions
        // carrying 0x100, and excludes dynamic point lights through param6=1.
        // No other light/noise branch is owned by this reconstruction.
        bool point_lights = false;
        for (const auto &light : common.input.lights) {
            if (light.active && !(light.flags & 0x100) && !(light.flags & 0x40))
                return;
            point_lights |= light.active && (light.flags & 0x50) == 0x50;
        }
        if (!point_lights)
            return;
        const unsigned polygons = stage.load(mesh + 0x34), count = stage.load(mesh + 0x10);
        const unsigned positions = stage.load(0x74639c), vertices = stage.load(mesh + 0x14);
        const unsigned current = stage.load(bp - 0x34);
        if (!polygons || !count || count > 4096 || !positions || !vertices || vertices > 1024 ||
            !stage.readable(polygons, count * 36) || !stage.readable(positions, vertices * 12) ||
            !stage.readable(0x7463a4, vertices * 4) || current < polygons ||
            (current - polygons) % 36 || (current - polygons) / 36 >= count)
            return;
        const auto &camera = identity->camera;
        const ClipBounds bounds{camera.projection[5],
                                camera.far_clip,
                                stage.adaptive_ground_float(0x74031c),
                                stage.adaptive_ground_float(0x740320),
                                stage.adaptive_ground_float(0x740324),
                                stage.adaptive_ground_float(0x740328)};
        pending.reserve(JobPool::capacity);
        for (unsigned slot = (current - polygons) / 36;
             slot < count && pending.size() < JobPool::capacity; ++slot) {
            const unsigned polygon = polygons + slot * 36, flags = stage.load(polygon);
            const unsigned corners = flags & 255;
            if (corners < 3 || corners > maximum_source_vertices || (flags & ~0x2ffU))
                continue;
            const unsigned indices = stage.load(polygon + 8), uv = stage.load(polygon + 16);
            const unsigned rgb = stage.load(polygon + 20), baked = stage.load(polygon + 24);
            const unsigned material = stage.load(polygon + 28);
            std::vector<SourceRange> source;
            if (!capture(source, node + 0x3c, 4) || !capture(source, mesh, 0x48) ||
                !capture(source, polygon, 36) || !capture(source, indices, corners * 4) ||
                !capture(source, uv, corners * 8) || !capture(source, rgb, corners * 12) ||
                !capture(source, baked, corners * 4) || !capture(source, material, 32))
                continue;
            std::vector<UnlitCorner> owned;
            std::vector<SourceCorner> projected;
            bool finite = true;
            for (unsigned corner = corners; corner-- > 0;) {
                const unsigned index = stage.load(indices + corner * 4);
                if (index >= vertices) {
                    finite = false;
                    break;
                }
                UnlitCorner vertex;
                vertex.source.camera = stage.adaptive_ground_point(positions + index * 12);
                vertex.source.uv = {stage.adaptive_ground_float(uv + corner * 8),
                                    stage.adaptive_ground_float(uv + corner * 8 + 4)};
                vertex.baked_ambient = stage.adaptive_ground_float(baked + corner * 4);
                // This is an inline array, not a pointer to another allocation.
                vertex.fog = stage.adaptive_ground_float(0x7463a4 + index * 4);
                vertex.modulation = stage.adaptive_ground_point(rgb + corner * 12);
                for (float value : vertex.source.camera)
                    finite &= std::isfinite(value);
                for (float value : vertex.source.uv)
                    finite &= std::isfinite(value);
                for (float value : vertex.modulation)
                    finite &= std::isfinite(value);
                finite &= std::isfinite(vertex.baked_ambient) && std::isfinite(vertex.fog) &&
                          vertex.source.camera[2] > bounds.near_plane &&
                          vertex.source.camera[2] < bounds.far_plane;
                owned.push_back(vertex);
                projected.push_back(vertex.source);
            }
            if (!finite)
                continue;
            auto input = reconstruct_baked(common.input, owned);
            input.identity = *identity;
            input.identity.polygon = polygon;
            input.identity.material = material;
            input.depth_bias = std::bit_cast<std::int32_t>(stage.load(polygon + 4));
            if (!matches_unclipped_source(projected, input, bounds))
                continue;
            if (!stage.adaptive_ground_workers.pool) {
                stage.adaptive_ground_workers.pool = std::make_unique<JobPool>(
                    stage.adaptive_ground_worker_count(), stage.adaptive_ground_check_enabled());
                std::fprintf(stderr,
                             "Adaptive ground pool: actual_workers=%u main_tid=%lu worker_tids=",
                             stage.adaptive_ground_workers.pool->worker_count(),
                             static_cast<unsigned long>(::GetCurrentThreadId()));
                bool separator = false;
                for (auto handle : stage.adaptive_ground_workers.pool->native_threads()) {
                    const DWORD thread = ::GetThreadId(handle);
                    if (!thread)
                        stage.deny("Adaptive ground worker thread identity unavailable", 0x545720);
                    std::fprintf(stderr, "%s%lu", separator ? "," : "",
                                 static_cast<unsigned long>(thread));
                    separator = true;
                }
                std::fprintf(stderr, "\n");
            }
            auto completion = stage.adaptive_ground_workers.pool->submit(input);
            if (!completion)
                break;
            pending.push_back({std::move(input), std::move(source), std::move(*completion), false});
            ++stage.adaptive_ground_workers.queued;
        }
        if (!pending.empty())
            ++stage.adaptive_ground_workers.meshes;
    }

    std::optional<mw34::adaptive_ground::Result> take(const mw34::adaptive_ground::Input &actual) {
        using namespace mw34::adaptive_ground;
        for (auto &item : pending) {
            if (item.used || item.input.identity.polygon != actual.identity.polygon)
                continue;
            item.used = true;
            bool equal = same_input(item.input, actual);
            std::array<unsigned char, 128 * 12> current;
            for (const auto &range : item.source) {
                if (!equal || !stage.readable(range.address, unsigned(range.bytes.size()))) {
                    equal = false;
                    break;
                }
                stage.get_bytes(range.address, current.data(), unsigned(range.bytes.size()));
                equal = !std::memcmp(current.data(), range.bytes.data(), range.bytes.size());
            }
            if (!equal) {
                ++stage.adaptive_ground_workers.discarded;
                return {};
            }
            if (item.completion.wait_for(std::chrono::seconds(0)) != std::future_status::ready)
                ++stage.adaptive_ground_workers.waits;
            auto result = item.completion.get();
            if (result.identity != actual.identity)
                stage.deny("Adaptive ground worker identity changed", 0x547740);
            ++stage.adaptive_ground_workers.matched;
            return result;
        }
        return {};
    }
};

AdaptiveGroundMesh *adaptive_ground_mesh{};
