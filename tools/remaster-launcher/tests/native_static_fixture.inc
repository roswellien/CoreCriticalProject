// Authored fog cases compare the new resident-only vertex path with the
// established world shader fed independently specified packed fog bytes.
static void native_static_gpu_checks() {
    _putenv_s("MW34_GPU_MODELS", "1");
    _putenv_s("MW34_GPU_STATIC_PRODUCER", "1");
    _putenv_s("MW34_SUN", "1");
    _putenv_s("MW34_SUN_SHADOWS", "0");
    _putenv_s("MW34_SUN_STRENGTH", "0");
    _putenv_s("MW34_SUN_AMBIENT", "0");
    _putenv_s("MW34_WEATHER", "0");
    _putenv_s("MW34_TEMPORAL_INPUTS", "0");
    _putenv_s("MW34_RENDER_SCALE", "100");
    _putenv_s("MW34_REMASTER_WIDTH", "");
    _putenv_s("MW34_REMASTER_HEIGHT", "");
    _putenv_s("MW34_REMASTER_AA", "");
    _putenv_s("MW34_REMASTER_AF", "");
    struct FogCase {
        const char *name;
        std::array<float, 4> distance;
        std::array<float, 4> height;
        float constant_height;
        unsigned expected_alpha;
        float z{4};
    };
    // Corners have x=+/-1. At z=4 the original approximate radius is4.125.
    // The z=3 case has radius squared10: the original yields3.25, not sqrt(10).
    const FogCase cases[]{
        {"inactive", {2, 4, 64, .25f}, {6, 2, .25f, 0}, 0, 255},
        {"before radial threshold", {5, 25, 64, .25f}, {6, 2, .25f, 1}, 0, 255},
        {"exponent radius and byte rounding", {2, 4, 64, .25f}, {6, 2, .25f, 1}, 0, 175, 3},
        {"height modulation", {2, 4, 64, .25f}, {6, 2, .25f, 1}, 4, 187},
        {"height upper boundary", {2, 4, 64, .25f}, {6, 2, .25f, 1}, 6, 255},
        {"far radial boundary", {2, 4, 17, .25f}, {6, 2, .25f, 1}, 0, 0},
        {"far height modulation", {2, 4, 17, .25f}, {6, 2, .25f, 1}, 4, 128},
        {"saturated distance ramp", {0, 0, 64, 1}, {6, 2, .25f, 1}, 0, 0},
    };
    auto geometry = std::make_shared<ModelGeometry>();
    geometry->key = geometry->hash = 0x574e415449564501ULL;
    geometry->vertices = {{-1, -1, 4, 0, 0, 1, 0, 0}, {1, -1, 4, 0, 0, 1, 1, 0},
                          {-1, 1, 4, 0, 0, 1, 0, 1}, {1, -1, 4, 0, 0, 1, 1, 0},
                          {1, 1, 4, 0, 0, 1, 1, 1}, {-1, 1, 4, 0, 0, 1, 0, 1}};
    const std::array<float, 12> identity{1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0};
    Renderer renderer;
    for (const auto &test : cases) {
        auto instance = std::make_shared<ModelInstance>();
        instance->geometry = geometry;
        if (test.z != 4) {
            auto changed = std::make_shared<ModelGeometry>(*geometry);
            changed->key = changed->hash = geometry->key + 1;
            for (auto &vertex : changed->vertices)
                vertex.z = test.z;
            instance->geometry = changed;
        }
        instance->world = instance->sun_eligible = true;
        instance->camera = instance->sun_normal = instance->sun_world = identity;
        instance->projection = {1, 32, 32, 32, 32, .1f};
        Scene reference{};
        reference.width = reference.height = 64;
        reference.has_depth = true;
        reference.color.assign(4096, 0);
        reference.depth.assign(4096, 0);
        for (const auto &v : instance->geometry->vertices)
            add(reference, {5000, 5000, .25f, .25f, 0xffffffff,
                            test.expected_alpha << 24, v.u, v.v});
        auto command = draw(0, 6);
        command.model = instance;
        command.push.mode[0] |= 16U; // Mix the produced specular-alpha fog coefficient.
        command.key.zenable = command.key.zwrite = 1;
        command.key.zfunc = 7; // Original reciprocal depth: greater-or-equal.
        command.push.fog[0] = 1;
        command.push.fog[1] = .25f;
        command.push.fog[2] = .5f;
        command.push.fog[3] = 1;
        reference.draws = {command};
        reference.order = {{false, 0}};
        renderer.render(reference);
        std::vector<std::uint8_t> expected_rgb;
        unsigned expected_width{}, expected_height{};
        renderer.capture_fullres_rgb(expected_rgb, expected_width, expected_height);
        Scene native = reference;
        native.color.assign(4096, 0);
        native.depth.assign(4096, 0);
        native.vertices.clear();
        auto fog = std::make_shared<mw34::native_static::Fog>();
        fog->distance = test.distance;
        fog->height = test.height;
        fog->height_row = {0, 0, 0, test.constant_height};
        auto candidate = std::make_shared<ModelInstance>(*instance);
        candidate->native_fog = fog;
        native.draws.front().model = candidate;
        renderer.render(native);
        std::vector<std::uint8_t> actual_rgb;
        unsigned actual_width{}, actual_height{};
        renderer.capture_fullres_rgb(actual_rgb, actual_width, actual_height);
        // RGB565 alone can hide a one-byte fog error. Compare the actual RGBA8
        // render target as well; black albedo and red fog expose each fog byte.
        if (native.color != reference.color || native.depth != reference.depth ||
            actual_rgb != expected_rgb || actual_width != expected_width ||
            actual_height != expected_height)
            throw std::runtime_error(std::string("Native static fog GPU mismatch: ") + test.name);
        if (std::none_of(native.depth.begin(), native.depth.end(), [](auto z) { return z != 0; }))
            throw std::runtime_error("Native static GPU fixture rendered no geometry");
    }
    if (renderer.model_uploads != 2)
        throw std::runtime_error("Native static GPU fixture reuploaded immutable geometry");
    std::cout << "Native static GPU: 8 fog/rounding cases exact, no TL stream, two geometry revisions on "
              << renderer.device_name << "\n";
}
