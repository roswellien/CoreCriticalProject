// Authored geometry and boundary cases; no original executable, assets or captures.
#include "adaptive_ground_capture.hpp"
#include "adaptive_ground_commit.hpp"
#include "adaptive_ground_jobs.hpp"
#include "adaptive_ground_math.hpp"
#include "render_target_dimensions.hpp"
#include <bit>
#include <cfenv>
#include <iostream>
#include <limits>
#include <string>

using namespace mw34::adaptive_ground;

namespace {
void require(bool condition, const char *message) {
    if (!condition)
        throw std::runtime_error(message);
}

template <class Action> void rejects(Action action, const char *message) {
    bool rejected = false;
    try {
        action();
    } catch (const std::runtime_error &) {
        rejected = true;
    }
    require(rejected, message);
}

Input triangle() {
    Input input;
    input.identity.camera.frame = 7;
    input.identity.camera.reset_epoch = 2;
    input.identity.source_epoch = 3;
    input.projection = {1, 0, 0, 1, 1, 1, 1};
    for (const Point &position : {Point{0, 0, 1}, Point{3, 0, 1}, Point{0, 3, 1}}) {
        SourceVertex vertex;
        vertex.screen = position;
        vertex.uv[0] = {position[0], position[1]};
        vertex.ambient = 0.25f;
        vertex.fog = 0.5f;
        vertex.modulation = {255, 128, 64};
        input.vertices.push_back(vertex);
    }
    Light light;
    light.active = true;
    light.flags = 0x50;
    light.position = {0, 0, 1};
    light.color = {0.5f, 0.25f, 0.125f};
    light.diffuse = 0.5f;
    light.ambient = 0.25f;
    light.inner_radius = 1000;
    light.outer_radius = 2000;
    light.inner_squared = 1000000;
    light.outer_squared = 4000000;
    light.inverse_span = 0.001f;
    input.lights.push_back(light);
    return input;
}

void no_light_and_filtered_light() {
    auto input = triangle();
    input.lights[0].flags = 0;
    input.lights[0].outer_radius = std::numeric_limits<float>::quiet_NaN();
    auto result = prepare(input);
    require(!result.prepared && result.vertices.empty() && result.triangles.empty(),
            "Unselected lights must not start preparation or inspect unused radius values");
    input = triangle();
    auto &light = input.lights[0];
    light.position = {100, 100, 100};
    light.inner_radius = light.inner_squared = 0;
    light.outer_radius = light.outer_squared = light.inverse_span = 1;
    result = prepare(input);
    require(!result.prepared && result.vertices.size() == 3 && result.triangles.empty(),
            "Filtered light must retain the explicit partial preparation boundary");
    require(result.centroid == Point{1, 1, 1}, "Filtered-light centroid was lost");
    require(result.distance_written && result.distance_delta == Point{99, 99, 99},
            "Filtered-light shared distance scratch was lost or reversed");
}

void constant_and_varying_attributes() {
    auto input = triangle();
    input.vertices[0].fog = 0.25f;
    input.vertices[2].fog = 0.75f;
    input.extra_uv_layers = 7;
    for (auto &vertex : input.vertices)
        vertex.uv[7] = {16, 32};
    const auto result = prepare(input);
    require(result.prepared && result.vertices.size() == 4 && result.triangles.size() == 3,
            "A small polygon fully inside the inner sphere must keep its centroid fan");
    require(result.identity == input.identity, "Preparation dropped frame/source identity");
    input.identity.camera.reset_epoch++;
    require(!(result.identity == input.identity), "Prepared identity aliases its caller");
    for (const auto &vertex : result.vertices) {
        require(vertex.base == Point{0.75f, 0.75f, 0.75f}, "Constant ambient changed");
        require(vertex.lit == Point{1.125f, 0.9375f, 0.84375f},
                "Lighting was reordered or clamped before original color packing");
        require(vertex.uv[7] == std::array<float, 2>{16, 32}, "Last UV layer was lost");
        require(vertex.modulation == Point{255, 128, 64}, "RGB modulation was treated as a normal");
    }
    require(result.vertices[3].fog == 0.5f &&
                result.vertices[3].uv[0] == std::array<float, 2>{1, 1},
            "Centroid fog or UV averaging changed");
    input = triangle();
    input.varying_ambient = true;
    input.vertices[0].ambient = 0;
    input.vertices[1].ambient = 0.5f;
    input.vertices[2].ambient = 1;
    const auto varying = prepare(input);
    require(varying.vertices[0].base[0] == 1 && varying.vertices[1].base[0] == 0.5f &&
                varying.vertices[2].base[0] == 0,
            "Varying ambient reused the first vertex");
    input = triangle();
    input.colored_ambient = true;
    input.colored_rgb = {0.25f, 0.5f, 0.75f};
    for (auto &vertex : input.vertices) {
        vertex.ambient = 1;
        vertex.colored_ambient = 255;
    }
    require(prepare(input).vertices[0].base ==
                Point{0.25f, 0.5f, std::bit_cast<float>(0x3f400001U)},
            "Colored ambient lost its unrounded common scale");
}

void far_boundary() {
    auto input = triangle();
    input.vertices[1].screen[0] = 2;
    input.vertices[2].screen[1] = 2;
    for (auto &vertex : input.vertices)
        vertex.ambient = 1;
    auto &light = input.lights[0];
    light.inner_radius = light.inner_squared = 0;
    light.outer_radius = 2;
    light.outer_squared = 4;
    light.inverse_span = 0.5f;
    light.diffuse = 1;
    light.ambient = 0;
    light.color = {1, 1, 1};
    const auto result = prepare(input);
    require(result.vertices[0].lit == Point{1, 1, 1}, "Light center lost its full intensity");
    require(result.vertices[1].lit == Point{0, 0, 0} && result.vertices[2].lit == Point{0, 0, 0},
            "Far-squared comparison must exclude the exact boundary");
}

void centroid_precision() {
    auto input = triangle();
    input.vertices[0].screen = {0.0390625f, 0, 1};
    input.vertices[1].screen = {0.0390625f, 3, 1};
    input.vertices[2].screen = {0, 0, 1};
    // The exact average is 5/192. Rounding its reciprocal before the first
    // multiply moves this result up one float bit.
    const auto result = prepare(input);
    require(std::bit_cast<std::uint32_t>(result.centroid[0]) == 0x3cd55555U,
            "Centroid X rounded the reciprocal before its first multiply");
}

void distance_precision() {
    // Each small square is below half a double ULP at 1, but their sum is
    // above it. The recovered X+Y, then Z order rounds each addition at 53 bits.
    const float small = 5.0f / 536870912.0f;
    require(detail::squared_distance(Point{1, small, small}, Point{}) == 1.0,
            "Squared distance changed the original addition order");
    const auto center =
        detail::triangle_centroid(Point{1, 0, 1}, Point{0x1p-24f, 3, 1}, Point{-1, 0, 1});
    require(center[0] == 0, "Refinement centroid lost its intermediate float stores");
}

void refinement_and_capacity() {
    auto input = triangle();
    const std::array<Point, 3> positions{{{-8, -8, 1}, {8, -8, 1}, {0, 8, 1}}};
    for (unsigned index = 0; index < 3; ++index) {
        input.vertices[index].screen = positions[index];
        input.vertices[index].uv[0] = {positions[index][0], positions[index][1]};
    }
    auto &light = input.lights[0];
    light.inner_radius = light.inner_squared = 0;
    light.outer_radius = 20;
    light.outer_squared = 400;
    light.inverse_span = 0.05f;
    const auto result = prepare(input);
    require(result.vertices.size() > 4 && result.triangles.size() > 3,
            "Boundary-crossing light did not refine the polygon");
    double area = 0;
    for (unsigned index = 0; index < result.triangles.size(); ++index) {
        const auto &face = result.triangles[index];
        const auto &a = result.vertices.at(face.vertices[0]).camera;
        const auto &b = result.vertices.at(face.vertices[1]).camera;
        const auto &c = result.vertices.at(face.vertices[2]).camera;
        const double triangle_area = ((double(b[0]) - a[0]) * (double(c[1]) - a[1]) -
                                      (double(b[1]) - a[1]) * (double(c[0]) - a[0])) *
                                     0.5;
        require(triangle_area > 0, "Refinement reversed or collapsed a triangle");
        area += triangle_area;
        for (unsigned edge = 0; edge < 3; ++edge) {
            const int neighbor_index = face.neighbors[edge];
            if (neighbor_index < 0)
                continue;
            const auto &neighbor = result.triangles.at(unsigned(neighbor_index));
            bool reciprocal = false;
            for (unsigned other = 0; other < 3; ++other)
                if (neighbor.neighbors[other] == int(index) &&
                    neighbor.vertices[other] == face.vertices[(edge + 1) % 3] &&
                    neighbor.vertices[(other + 1) % 3] == face.vertices[edge])
                    reciprocal = true;
            require(reciprocal, "Refinement adjacency is not reciprocal along the same edge");
        }
    }
    require(std::abs(area - 128.0) < 0.0001, "Refinement changed the polygon's covered area");
    for (const auto &vertex : result.vertices)
        require(vertex.camera[0] == vertex.uv[0][0] && vertex.camera[1] == vertex.uv[0][1],
                "Midpoint UV does not follow the original surface");
    rejects([&] { (void)prepare(input, {4, 3}); }, "Scratch overflow was silently accepted");
}

void source_admission() {
    auto input = triangle();
    const std::array<SourceCorner, 3> source{SourceCorner{{0, 7, 3}, {0, 0}},
                                             SourceCorner{{3, 0, 3}, {1, 0}},
                                             SourceCorner{{0, 3, 3}, {0, 1}}};
    const ClipBounds bounds{1, 100, -10, -10, 10, 10};
    // Explicit initial-projection result: using the stored reciprocal for Y
    // would produce 0x40155556 instead of 0x40155555 here.
    input.vertices[0].screen = {0, std::bit_cast<float>(0x40155555U), 1.0f / 3.0f};
    input.vertices[1].screen = {1, 0, 1.0f / 3.0f};
    input.vertices[2].screen = {0, 1, 1.0f / 3.0f};
    for (unsigned index = 0; index < 3; ++index)
        input.vertices[index].uv[0] = source[index].uv;
    require(matches_unclipped_source(source, input, bounds), "Unclipped source was rejected");
    input.vertices[0].screen[1] = std::bit_cast<float>(0x40155556U);
    require(!matches_unclipped_source(source, input, bounds),
            "Same-count changed screen position was admitted");
    input.vertices[0].screen[1] = std::bit_cast<float>(0x40155555U);
    input.vertices[1].uv[0][0] = 0;
    require(!matches_unclipped_source(source, input, bounds), "Changed source UV was admitted");
    input.vertices[1].uv[0] = source[1].uv;
    auto changed = source;
    changed[1].camera[2] = bounds.near_plane;
    require(!matches_unclipped_source(changed, input, bounds), "Near-plane source was admitted");
    auto clipped = bounds;
    clipped.right = 0.5f;
    require(!matches_unclipped_source(source, input, clipped), "Clipped source was admitted");
    clipped = bounds;
    clipped.far_plane = std::numeric_limits<float>::quiet_NaN();
    require(!matches_unclipped_source(source, input, clipped), "Unknown clip bounds were admitted");
}

void owned_jobs() {
    auto input = triangle();
    const auto expected = prepare(input);
    std::optional<std::future<Result>> completion;
    {
        JobPool workers(2);
        completion = workers.submit(input);
        require(completion.has_value(), "First owned job was not accepted");
        // Retiring the source must not change a worker's retained request.
        input.vertices.clear();
        input.lights.clear();
        require(workers.submitted() == 1, "Owned job was not accounted for");
    }
    // Closing a scope drains before releasing storage; completed handles remain
    // valid without keeping either a pool or the original source alive.
    const auto actual = completion->get();
    require(actual.identity == expected.identity && actual.triangles == expected.triangles &&
                actual.vertices.size() == expected.vertices.size(),
            "Owned job lifetime changed its result");
    for (unsigned index = 0; index < expected.vertices.size(); ++index)
        require(actual.vertices[index].lit == expected.vertices[index].lit &&
                    actual.vertices[index].camera == expected.vertices[index].camera &&
                    actual.vertices[index].screen == expected.vertices[index].screen,
                "Worker did not retain its own vertex/light inputs");
    JobPool workers(1);
    input = triangle();
    input.guest_control_word = 0x027f;
    auto invalid = workers.submit(std::move(input));
    require(invalid.has_value(), "Invalid-domain job could not be tested");
    rejects([&] { (void)invalid->get(); }, "Worker swallowed a numerical contract failure");
    auto recovered = workers.submit(triangle());
    require(recovered.has_value() && recovered->get().triangles == expected.triangles,
            "Worker did not recover after delivering an exception");
    rejects([] { JobPool unsupported(0); }, "A zero actual worker count was accepted");
    rejects([] { JobPool unsupported(5); }, "An excessive actual worker count was accepted");

    std::vector<std::future<Result>> retiring;
    {
        JobPool draining(2);
        for (unsigned index = 0; index < JobPool::capacity; ++index) {
            auto request = triangle();
            request.identity.polygon = index + 1;
            auto queued = draining.submit(std::move(request));
            require(queued.has_value(), "Bounded retirement batch was rejected early");
            retiring.push_back(std::move(*queued));
        }
    }
    // Consume in a different order after all owners are retired. Neither
    // completion order nor closing the pool may substitute another polygon.
    for (unsigned index = unsigned(retiring.size()); index-- > 0;)
        require(retiring[index].get().identity.polygon == index + 1,
                "Shutdown or completion ordering changed a polygon's ownership");
    struct RestoreRounding {
        int previous = std::fegetround();
        ~RestoreRounding() { std::fesetround(previous); }
    } restore;
    require(std::fesetround(FE_DOWNWARD) == 0, "Cannot establish worker FP isolation case");
    JobPool isolated(1);
    auto nearest = isolated.submit(triangle());
    require(nearest.has_value() && nearest->get().triangles == expected.triangles,
            "Worker inherited an unaudited main-thread rounding mode");
    require(std::fegetround() == FE_DOWNWARD, "Worker changed the main thread's FP domain");
}

void worker_budget_and_unused_errors() {
    for (unsigned requested : {1U, 2U, 4U})
        for (unsigned hardware : {0U, 1U, 2U, 3U, 8U}) {
            const unsigned expected = hardware == 0 ? 1 : std::min(requested, hardware);
            require(bounded_worker_count(requested, hardware) == expected,
                    "Worker budget did not cap the requested count to available hardware");
        }
    JobPool three_workers(3);
    require(three_workers.worker_count() == 3,
            "A hardware-capped count of three workers was rejected");

    JobPool workers(2);
    std::vector<std::future<Result>> unused;
    auto invalid = triangle();
    invalid.guest_control_word = 0x027f;
    unused.push_back(std::move(*workers.submit(std::move(invalid))));
    unused.push_back(std::move(*workers.submit(triangle())));
    invalid = triangle();
    invalid.vertices.clear();
    unused.push_back(std::move(*workers.submit(std::move(invalid))));
    std::exception_ptr first_error;
    for (auto &completion : unused)
        drain_completion(completion, first_error);
    require(bool(first_error), "Discarding an unused worker result swallowed its failure");
    for (const auto &completion : unused)
        require(!completion.valid(), "A failed unused result prevented draining later jobs");
    try {
        std::rethrow_exception(first_error);
    } catch (const std::runtime_error &error) {
        require(std::string(error.what()).find("nearest/53-bit") != std::string::npos,
                "Draining unused results replaced the first typed worker failure");
    }
    auto consumed = workers.submit(triangle());
    (void)consumed->get();
    std::exception_ptr no_error;
    drain_completion(*consumed, no_error);
    require(!no_error, "An already consumed result became a drain failure");
}

void worker_environment_restoration() {
    WorkerEnvironment restore_original;
    require(std::fesetround(FE_DOWNWARD) == 0, "Cannot establish saved worker rounding");
    require(std::feraiseexcept(FE_INVALID) == 0, "Cannot establish saved worker status");
    const int saved_status = std::fetestexcept(FE_ALL_EXCEPT);
#if defined(__SSE__) || defined(_M_X64)
    const unsigned saved_mxcsr = _mm_getcsr();
#endif
#if defined(_WIN32)
    ::SetLastError(0x183);
#endif
    const auto check_restored = [&] {
        require(std::fegetround() == FE_DOWNWARD &&
                    std::fetestexcept(FE_ALL_EXCEPT) == saved_status,
                "A job lost the worker's actual FP rounding or sticky status");
#if defined(__SSE__) || defined(_M_X64)
        require(_mm_getcsr() == saved_mxcsr, "A job lost the worker's actual SSE environment");
#endif
#if defined(_WIN32)
        require(::GetLastError() == 0x183, "A job lost the worker's actual LastError");
#endif
    };
    const auto run_job = [&] {
        WorkerEnvironment environment;
        require(std::fegetround() == FE_TONEAREST && !std::fetestexcept(FE_ALL_EXCEPT),
                "A job inherited earlier rounding or sticky status");
#if defined(__SSE__) || defined(_M_X64)
        require(_mm_getcsr() == 0x1f80, "A job inherited nondefault SSE underflow behavior");
#endif
        (void)prepare(triangle());
        std::feraiseexcept(FE_DIVBYZERO);
#if defined(_WIN32)
        ::SetLastError(0x547740);
#endif
    };
    run_job();
    check_restored();
    rejects(
        [&] {
            WorkerEnvironment environment;
            auto invalid = triangle();
            invalid.guest_control_word = 0x027f;
            (void)prepare(invalid);
        },
        "The failing-job environment control did not throw");
    check_restored();
}

void baked_reconstruction() {
    auto common = triangle();
    common.vertices.clear();
    const std::array<UnlitCorner, 3> source{
        UnlitCorner{{{0, 7, 3}, {0.25f, 0.5f}}, 0.25f, 0.125f, {255, 128, 64}},
        UnlitCorner{{{3, 0, 3}, {1, 0}}, -1, 0.25f, {64, 128, 255}},
        UnlitCorner{{{0, 3, 3}, {0, 1}}, 2, 0.5f, {1, 2, 3}}};
    const auto input = reconstruct_baked(common, source);
    require(input.varying_ambient && input.vertices.size() == 3,
            "Baked reconstruction lost its vertex/mode ownership");
    require(input.vertices[0].ambient == 0.75f && input.vertices[1].ambient == 1 &&
                input.vertices[2].ambient == 0,
            "Baked prelude did not subtract and clamp ambient");
    require(std::bit_cast<unsigned>(input.vertices[0].screen[1]) == 0x40155555U &&
                input.vertices[0].fog == 0.125f && input.vertices[0].uv[0] == source[0].source.uv &&
                input.vertices[0].modulation == source[0].modulation,
            "Baked reconstruction changed projection or copied attributes");
    auto changed = input;
    require(same_input(input, changed), "An owned exact input copy did not match");
    changed.vertices[1].screen[1] = -0.0f;
    require(!same_input(input, changed), "Input comparison ignored signed-zero position bits");
    changed = input;
    ++changed.identity.camera.reset_epoch;
    require(!same_input(input, changed), "Input comparison ignored a camera reset");
    changed = input;
    changed.identity.camera.projection[0] = -0.0f;
    require(!same_input(input, changed), "Input comparison ignored snapshot projection bits");
    changed = input;
    ++changed.identity.camera.sizes[2];
    require(!same_input(input, changed), "Old job survived an output-size change");
    changed = input;
    ++changed.identity.heap_release_serial;
    require(!same_input(input, changed), "Old job survived a source lifetime retirement");
    changed = input;
    ++changed.identity.memory_generation;
    require(!same_input(input, changed), "Old job survived a mapping/protection change");
    changed = input;
    ++changed.identity.clip_rectangle[0];
    require(!same_input(input, changed), "Old job survived a clip rectangle change");
    common.colored_ambient = true;
    rejects([&] { (void)reconstruct_baked(common, source); },
            "Unaudited colored prelude was reconstructed");
}

void target_identity() {
    using mw34::render_target::current_dimensions;
    const auto ready =
        current_dimensions({640, 480}, {640, 480}, {1280, 960, 640, 480}, 2, 2, true, false);
    require(ready && *ready == std::array<unsigned, 6>{640, 480, 1280, 960, 640, 480},
            "Target identity confused guest, output and internal dimensions");
    require(!current_dimensions({640, 480}, {800, 600}, {1280, 960, 640, 480}, 2, 2, true, false),
            "A changed guest target reused stale raster dimensions");
    require(!current_dimensions({640, 480}, {640, 480}, {1280, 960, 640, 480}, 2, 3, true, false),
            "A pending scale request reused stale raster dimensions");
    require(!current_dimensions({640, 480}, {640, 480}, {1280, 960, 640, 480}, 2, 2, false, false),
            "Uninitialized target was authenticated");
    require(!current_dimensions({640, 480}, {640, 480}, {1280, 960, 0, 0}, 2, 2, true, false),
            "Unknown internal dimensions were authenticated");
    require(!current_dimensions({640, 480}, {640, 480}, {1280, 960, 640, 480}, 2, 2, true, true),
            "Frontend target was authenticated for world jobs");
}

void masked_transfer() {
    auto result = prepare(triangle());
    result.vertices[0].camera[1] = -0.0f;
    result.triangles[0].active = true;
    constexpr std::uint32_t untouched = 0xa5c3f017U;
    std::vector<GuestVertexRecord> vertices(result.vertices.size());
    for (auto &record : vertices)
        record.fill(untouched);
    encode_preprojection_vertices(result, 3, vertices);
    require(vertices[0][1] == 0x80000000U && vertices[0][22] == 0x3f000000U,
            "Typed transfer changed signed zero or the fog attribute");
    for (unsigned index = 0; index < vertices.size(); ++index) {
        const auto &record = vertices[index];
        for (unsigned axis = 3; axis < 6; ++axis)
            require(record[axis] == untouched, "Transfer preempted original screen projection");
        for (unsigned word = 8; word < 22; ++word)
            require(record[word] == untouched, "Transfer overwrote an unused UV slot");
        if (index < 3)
            require(record[32] == untouched, "Transfer overwrote an initial boundary flag");
    }
    require(vertices[3][32] == 0, "Generated centroid boundary flag was not supplied");
    const auto before = vertices;
    rejects([&] { encode_preprojection_vertices(result, 3, std::span(vertices).first(1)); },
            "Undersized vertex transfer was accepted");
    require(vertices == before, "Invalid transfer changed staged records");
    std::vector<GuestTriangleRecord> faces(result.triangles.size());
    encode_triangles(result, faces, false);
    for (const auto &face : faces)
        require(face[6] == 0, "Completed refinement remained active in the original loop");
    encode_triangles(result, faces, true);
    require(faces[0][6] == 1 && faces[0][3] == 0xffffffffU,
            "Transfer did not restore computed activity or a boundary neighbor");
}

void invalid_domains() {
    auto input = triangle();
    input.vertices.resize(maximum_source_vertices, input.vertices.front());
    input.lights.clear();
    require(!prepare(input).prepared, "Native input capacity boundary was rejected");
    input.vertices.push_back(input.vertices.front());
    rejects([&] { (void)prepare(input); }, "Native prelude attribute capacity was exceeded");
    input = triangle();
    input.lights.resize(maximum_lights + 1);
    rejects([&] { (void)prepare(input); }, "Native selected-light pointer capacity was exceeded");
    input = triangle();
    input.vertices[0].screen[2] = 0;
    rejects([&] { (void)prepare(input); }, "Zero inverse depth was accepted");
    input = triangle();
    input.extra_uv_layers = 8;
    rejects([&] { (void)prepare(input); }, "Ninth UV layer was accepted");
    input = triangle();
    input.guest_control_word = 0x027f;
    rejects([&] { (void)prepare(input); }, "An unaudited guest precision mode was accepted");
    input = triangle();
    input.projection.inverse_x = std::numeric_limits<float>::max();
    rejects([&] { (void)prepare(input); }, "Unprojection overflow was accepted");
    input = triangle();
    const int rounding = std::fegetround();
    require(std::fesetround(FE_DOWNWARD) == 0, "Cannot establish rounding negative control");
    bool rejected = false;
    try {
        (void)prepare(input);
    } catch (const std::runtime_error &) {
        rejected = true;
    }
    require(std::fesetround(rounding) == 0, "Cannot restore test rounding mode");
    require(rejected, "A worker with the wrong rounding mode was accepted");
}
} // namespace

int main() {
    try {
        no_light_and_filtered_light();
        constant_and_varying_attributes();
        far_boundary();
        centroid_precision();
        distance_precision();
        refinement_and_capacity();
        invalid_domains();
        source_admission();
        owned_jobs();
        worker_budget_and_unused_errors();
        worker_environment_restoration();
        baked_reconstruction();
        target_identity();
        masked_transfer();
        std::cout << "Adaptive ground numerical and ownership boundaries pass\n";
    } catch (const std::exception &error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
