// Pure CPU contracts. Kept on the existing adapter core-check path so normal
// adapter runs cannot silently skip the fixture producer's math prerequisites.
void check_native_fixture_core() {
  using namespace mw34::native_fixtures;
  using mw34::materials::SurfaceKey;
  unsigned passed = 0;
  auto check = [&](bool condition, const char *message) {
    require(condition, message);
    ++passed;
  };
  auto rejects = [&](auto operation, const char *message) {
    bool rejected = false;
    try {
      operation();
    } catch (const std::invalid_argument &) {
      rejected = true;
    }
    check(rejected, message);
  };
  auto close = [](float actual, double expected) {
    return std::abs(double(actual) - expected) < 1e-5;
  };
  auto at_uv = [](float u, float v) -> UvPoint {
    return {{1.f + 4.f * u, 2.f + 6.f * v, 3.f}, u, v};
  };
  const std::vector<UvPoint> triangle{at_uv(0, 0), at_uv(1, 0), at_uv(0, 1)};
  const auto square = triangulate_polygon(
      {at_uv(0, 0), at_uv(1, 0), at_uv(1, 1), at_uv(0, 1)});

  check(catalog().size() == 32, "Fixture catalog lost an authenticated definition");
  std::size_t vehicle_definitions = 0;
  for (const auto &definition : catalog()) {
    validate_definition(definition);
    check(match(definition.key()) == &definition, "Exact fixture key did not bind uniquely");
    auto wrong = definition.key();
    wrong.hash ^= 1;
    check(!match(wrong), "Fixture admitted a one-bit content mismatch");
    wrong = definition.key();
    wrong.format = 0;
    check(!match(wrong), "Fixture accepted a wildcard packed format");
    wrong = definition.key();
    ++wrong.width;
    check(!match(wrong), "Fixture accepted different source dimensions");
    for (const auto &region : definition.emission_regions)
      check(region != Region{0, 0, 1, 1}, "Fixture catalog promoted the entire body atlas");
    vehicle_definitions += definition.classification == Classification::vehicle_headlamp;
  }
  check(vehicle_definitions == 6, "Vehicle fixture classification changed");
  check(!match({1024, 1024, 1, 0x947209e376d92d19ULL}),
        "Removed false lighthouse identity was re-admitted");
  check(!match({512, 512, 1, 0x5067582a24cf6701ULL}),
        "Removed static sprite identity was re-admitted");
  for (const auto& pair : std::vector<std::pair<SurfaceKey, SurfaceKey>>{
      {{64,64,1,0x5c23fe54ee2e937dULL},{1024,1024,1,0x7b21b87f1c592187ULL}},
      {{32,32,1,0xc71e4fe58b74e99fULL},{512,512,1,0x6002a710ed9a5078ULL}},
      {{32,64,1,0xd1e81e3ebc8310d6ULL},{512,1024,1,0xff2aeda64037f55eULL}}}) {
    const auto* original=match(pair.first);
    const auto* upgraded=match(pair.second);
    check(original && upgraded && original->emission_regions==upgraded->emission_regions &&
        original->radius==14 && original->intensity==1.6f &&
        original->normal_offset==.15f && original->color==upgraded->color &&
        original->emission_radii==upgraded->emission_radii &&
        original->emission_colors==upgraded->emission_colors &&
        original->classification==Classification::vehicle_headlamp,
        "Authenticated original APC alias lost its reviewed mask/physical parameters");
  }
  check(!match({512, 512, 1, 123}), "Unregistered bright body texture became a fixture");

  const auto *lamp = match({512, 512, 1, 0x60f6785ad44b57feULL});
  check(lamp && std::strcmp(lamp->name, "t1lite01") == 0,
        "Known Training lamp key selected the wrong definition");
  const auto lamp_projection = project_fixture(*lamp, square);
  check(lamp_projection.anchors.size() == 1 && lamp_projection.physical_lights.size() == 1,
        "Training lamp did not produce one UV-local light");
  const auto &lamp_light = lamp_projection.physical_lights.front().light;
  check(close(lamp_light.start[0], 3) && close(lamp_light.start[1], 5) &&
            close(lamp_light.start[2], 3.15) && lamp_light.start[3] == 14,
        "Training lamp did not use its analytic UV center and outward offset");
  check(lamp_light.end[3] == 0 && lamp_light.end[0] == lamp_light.start[0] &&
            lamp_light.color == std::array<float, 4>{1.f, .94f, .8f, 1.6f},
        "Training point light protocol or authored power/color changed");

  const auto *optics = match({512, 256, 1, 0xa7607277a3b5bc50ULL});
  check(optics && std::strcmp(optics->name, "c5strt09") == 0,
        "Stale c5strt10 label replaced the corrected three-optic definition");
  const auto optics_projection = project_fixture(*optics, square);
  check(optics_projection.physical_lights.size() == 3,
        "Three reviewed optic windows did not remain separate lights");
  for (std::size_t index = 0; index < 3; ++index) {
    const double centers[] = {.2125, .4875, .7575};
    const auto &position = optics_projection.physical_lights[index].light.start;
    check(close(position[0], 1 + 4 * centers[index]) && close(position[1], 2.915),
          "Optic anchor drifted from independently specified UV witness");
  }

  const auto *hallway = match({128, 512, 1, 0xed87dd01ce4f7305ULL});
  check(hallway != nullptr, "Mixed hallway material is missing");
  const auto mixed = project_fixture(*hallway, square);
  check(mixed.anchors.size() == 2 && mixed.physical_lights.size() == 1 &&
            mixed.physical_lights.front().region == 1,
        "Red glow-only hallway island emitted a physical light");
  check(mixed.physical_lights.front().light.color ==
            std::array<float, 4>{1.f, .95f, .85f, 1.6f},
        "Per-region hallway light color was discarded");
  const auto *indicator = match({256, 512, 1, 0x08da7b673422c96dULL});
  check(indicator && indicator->emission_only, "Known bay indicator lost glow-only status");
  const auto glow = project_fixture(*indicator, square);
  check(glow.anchors.size() == 2 && glow.physical_lights.empty(),
        "Glow-only indicator must retain its mask without casting illumination");

  auto analytic = *lamp;
  analytic.emission_regions = {{.2f, .2f, .3f, .3f}};
  auto projected = project_fixture(analytic, triangle);
  check(projected.anchors.size() == 1 && close(projected.anchors[0].position[0], 2) &&
            close(projected.anchors[0].position[1], 3.5) &&
            close(projected.anchors[0].position[2], 3.15),
        "Barycentric witness (one quarter, one quarter) failed");
  for (unsigned index = 0; index < 100; ++index) {
    const float clipped_u = float(index) * .0029f;
    const std::vector<UvPoint> clipped{
        at_uv(clipped_u, 0), at_uv(1, 0), at_uv(clipped_u, 1)};
    const auto stable = project_fixture(analytic, clipped);
    check(stable.anchors.size() == 1 && close(stable.anchors[0].position[0], 2) &&
              close(stable.anchors[0].position[1], 3.5),
          "Camera clipping moved or removed an overlapping authored UV center");
  }
  analytic.emission_regions = {{.7f, .1f, .9f, .5f}};
  projected = project_fixture(analytic, triangle);
  check(projected.anchors.size() == 1 && close(projected.anchors[0].position[0], 4.2) &&
            close(projected.anchors[0].position[1], 3.8),
        "Partially visible window used its fragment centroid instead of authored center");
  analytic.emission_regions = {{.8f, .8f, .9f, .9f}};
  check(project_fixture(analytic, triangle).anchors.empty(),
        "Nonoverlapping UV window produced a source");

  analytic.emission_regions = {{.2f, .2f, .3f, .3f}, {.25f, .2f, .35f, .3f}};
  auto duplicate_triangles = triangle;
  duplicate_triangles.insert(duplicate_triangles.end(), triangle.begin(), triangle.end());
  projected = project_fixture(analytic, duplicate_triangles);
  check(projected.anchors.size() == 2 && projected.physical_lights.size() == 2 &&
            projected.anchors[0].region == 0 && projected.anchors[1].region == 1 &&
            close(projected.anchors[0].position[0], 2) &&
            close(projected.anchors[1].position[0], 2.2),
        "Triangle overlap duplicated an island or collapsed distinct windows");
  analytic.emission_regions.resize(1);
  std::vector<UvPoint> unequal_overlap{at_uv(.25f, .2f), at_uv(.3f, .2f), at_uv(.25f, .3f)};
  for (auto &point : unequal_overlap)
    point.position[0] += 100;
  unequal_overlap.insert(unequal_overlap.end(), triangle.begin(), triangle.end());
  check(close(project_fixture(analytic, unequal_overlap).anchors[0].position[0], 2),
        "A smaller overlapping triangle replaced the original UV basis");

  auto reversed = triangle;
  std::swap(reversed[1], reversed[2]);
  check(close(project_fixture(analytic, reversed).anchors[0].position[2], 2.85),
        "Original winding did not determine the signed physical offset");
  check(close(project_fixture(analytic, reversed, Winding::reversed_submission)
                  .anchors[0].position[2], 3.15),
        "Reversed GPU submission winding put a light inside its mounting surface");
  std::vector<UvPoint> affine;
  for (const auto &point : triangle)
    affine.push_back({{10.f + 2.f * point.u, 20.f + 4.f * point.v,
                       30.f + point.u + 2.f * point.v}, point.u, point.v});
  projected = project_fixture(analytic, affine);
  const double root_six = std::sqrt(6.);
  check(close(projected.anchors[0].position[0], 10.5 - .15 / root_six) &&
            close(projected.anchors[0].position[1], 21 - .15 / root_six) &&
            close(projected.anchors[0].position[2], 30.75 + .30 / root_six),
        "Affine UV mapping lost translation, unequal scale or outward plane normal");

  const auto *vehicle = match({512, 512, 1, 0x6002a710ed9a5078ULL});
  check(vehicle && vehicle->classification == Classification::vehicle_headlamp &&
            vehicle->emission_regions.size() == 13 && !vehicle->is_spot,
        "APC base metadata or separate directional classification changed");
  rejects([&] { project_fixture(*vehicle, square); },
          "Vehicle without owned forward proof became an anonymous point light");
  const auto front = project_fixture(*vehicle, square, Winding::original, Point{0, 0, 1});
  check(front.physical_lights.size() == 13 &&
            front.physical_lights[0].light.end == std::array<float, 4>{0, 0, 1, 2},
        "Front-facing APC UV regions did not use forward spotlight protocol");
  check(project_fixture(*vehicle, square, Winding::original, Point{0, 0, -1})
            .physical_lights.empty(), "Rear-facing APC body cast a headlight");
  check(project_fixture(*vehicle, square, Winding::original, Point{1, 0, 0})
            .physical_lights.empty(), "Side-facing APC body cast a headlight");
  auto spot = analytic;
  spot.is_spot = true;
  check(project_fixture(spot, triangle).physical_lights[0].light.end ==
            std::array<float, 4>{0, 0, 1, 2}, "Scenery spotlight lost its surface direction");
  auto zero_radius = analytic;
  zero_radius.radius = 0;
  check(project_fixture(zero_radius, triangle).physical_lights.empty(),
        "Radius-zero definition emitted physical illumination");

  rejects([&] { project_fixture(analytic, {at_uv(0, 0), at_uv(1, 0), at_uv(.5f, 0)}); },
          "Degenerate UV mapping guessed a light position");
  auto world_degenerate = triangle;
  world_degenerate[2].position = world_degenerate[1].position;
  rejects([&] { project_fixture(analytic, world_degenerate); },
          "Degenerate world polygon supplied an arbitrary normal");
  auto invalid = triangle;
  invalid[1].u = std::numeric_limits<float>::quiet_NaN();
  rejects([&] { project_fixture(analytic, invalid); }, "Nonfinite source UV was admitted");
  invalid = triangle;
  invalid[2].position[1] = std::numeric_limits<float>::infinity();
  rejects([&] { project_fixture(analytic, invalid); }, "Nonfinite world position was admitted");
  invalid = triangle;
  invalid.push_back(at_uv(1, 1));
  rejects([&] { project_fixture(analytic, invalid); }, "Incomplete triangle list was admitted");
  rejects([&] { project_fixture(analytic, triangle, static_cast<Winding>(99)); },
          "Unknown winding silently changed source orientation");
  rejects([&] { project_fixture(analytic, triangle, Winding::original, Point{0, 0, 1}); },
          "Scenery was silently reclassified as a vehicle spotlight");
  rejects([&] { project_fixture(*vehicle, square, Winding::original, Point{0, 0, 0}); },
          "Vehicle accepted a degenerate forward direction");
  auto invalid_definition = analytic;
  invalid_definition.emission_regions.assign(33, Region{.2f, .2f, .3f, .3f});
  rejects([&] { project_fixture(invalid_definition, triangle); },
          "Fixture exceeded the shader's 32-region limit");
  invalid_definition = analytic;
  invalid_definition.emission_regions[0] = {.2f, .2f, .2f, .3f};
  rejects([&] { project_fixture(invalid_definition, triangle); },
          "Empty emission rectangle was accepted");
  invalid_definition = analytic;
  invalid_definition.emission_radii = {-1};
  rejects([&] { project_fixture(invalid_definition, triangle); },
          "Negative per-region light radius was accepted");
  invalid_definition = analytic;
  invalid_definition.emission_colors = {Point{1, std::numeric_limits<float>::quiet_NaN(), 1}};
  rejects([&] { project_fixture(invalid_definition, triangle); },
          "Nonfinite per-region color was accepted");
  rejects([&] { triangulate_polygon(std::vector<UvPoint>(65, at_uv(0, 0))); },
          "Unbounded original polygon was accepted");
  rejects([&] { triangulate_polygon(triangle, static_cast<Topology>(99)); },
          "Unknown polygon topology was accepted");
  std::vector<UvPoint> too_many_triangles((maximum_triangles + 1) * 3, at_uv(0, 0));
  rejects([&] { project_fixture(analytic, too_many_triangles); },
          "Unbounded fixture triangle list was accepted");
  const auto strip = triangulate_polygon(
      {at_uv(0, 0), at_uv(1, 0), at_uv(0, 1), at_uv(1, 1)}, Topology::strip);
  check(project_fixture(analytic, strip).physical_lights.size() == 1,
        "Alternating strip winding duplicated or inverted a source");
  check(project_fixture(analytic, {}).physical_lights.empty(),
        "Empty submitted geometry invented a physical source");
  std::fprintf(stderr, "[NATIVE_FIXTURE_CONTRACTS] cases=%u failures=0\n", passed);
}


void check_native_fixture_sources_core() {
  using namespace mw34::native_fixtures;
  unsigned passed = 0;
  const auto check = [&](bool condition, const char *message) {
    require(condition, message);
    ++passed;
  };
  const mw34::materials::SurfaceKey lamp_key{512, 512, 1, 0x60f6785ad44b57feULL};
  const std::vector<UvPoint> square = triangulate_polygon(
      {{{0, 0, 2}, 0, 0}, {{2, 0, 2}, 1, 0}, {{2, 2, 2}, 1, 1}, {{0, 2, 2}, 0, 1}});
  auto result = observe_source(lamp_key, square);
  check(result.status == ObservationStatus::admitted && result.value &&
            result.value->regions == std::vector<Region>{{.25f, .25f, .75f, .75f}} &&
            result.value->physical_lights.size() == 1,
        "Owned fixture observation lost the exact admitted mask or physical source");
  check(result.value->physical_lights[0].light.start == std::array<float, 4>{1, 1, 2.15f, 14},
        "Owned fixture source changed the analytic square's light anchor");
  check(!observe_source({512, 512, 1, lamp_key.hash ^ 1}, square).value,
        "Owned source admitted unknown material contents");
  const auto vehicle = observe_source({512, 512, 1, 0x6002a710ed9a5078ULL}, square);
  check(vehicle.status == ObservationStatus::vehicle_pending && !vehicle.value,
        "Unowned vehicle source emitted without healthy branch and copied pose");
  const auto glow = observe_source({256, 512, 1, 0xc1eea6a84cfc28a3ULL}, square);
  check(glow.value && glow.value->intensity == .8f && glow.value->regions.size() == 1 &&
            glow.value->physical_lights.empty(),
        "Owned glow-only observation lost its emission or invented a physical light");
  auto repeat = square;
  repeat[0].u = -.01f;
  check(observe_source(lamp_key, repeat).status == ObservationStatus::unsupported_mapping &&
            !observe_source(lamp_key, repeat).value,
        "Repeated atlas tile silently reused a single physical UV window");
  repeat = square;
  repeat[0].v = std::numeric_limits<float>::quiet_NaN();
  check(observe_source(lamp_key, repeat).status == ObservationStatus::unsupported_mapping,
        "Nonfinite source mapping was not explicitly rejected");
  auto duplicates = square;
  duplicates.insert(duplicates.end(), square.begin(), square.end());
  VisibleSources sources;
  sources.observe(*observe_source(lamp_key, duplicates, Winding::original, true).value);
  check(sources.candidates().size() == 1,
        "Prepared triangle diagonal or duplicate submission duplicated a physical lamp");
  auto translated = square;
  for (auto &vertex : translated)
    vertex.position[0] += 4;
  duplicates.insert(duplicates.end(), translated.begin(), translated.end());
  const auto copied = observe_source(lamp_key, duplicates, Winding::original, true);
  sources.observe(*copied.value);
  auto candidates = sources.candidates();
  check(candidates.size() == 2 && candidates[0].light.start[0] == 1 &&
            candidates[1].light.start[0] == 5 && candidates[0].source != candidates[1].source &&
            !candidates[0].weapon && (candidates[0].source & (1ULL << 62)),
        "Separate prepared instances lost physical sources or disjoint fixture IDs");
  for (auto &vertex : duplicates)
    vertex.position = {1000, 1000, 1000};
  sources.observe(*copied.value);
  check(sources.candidates().size() == 2 && sources.candidates()[0].light.start ==
            candidates[0].light.start,
        "Native caller mutation escaped the owned fixture observation");
  sources.clear();
  check(sources.candidates().empty(), "Visible-only fixture cache retained the previous world view");
  mw34::vkscene::Scene first_scene, second_scene;
  mw34::sun::Uniform first_uniform{}, second_uniform{};
  const auto &observation = *result.value;
  const auto first_index = first_scene.emissions.capture(
      {float(observation.regions.size()), observation.intensity, 0, 0}, observation.regions);
  const auto second_index = second_scene.emissions.capture(
      {float(observation.regions.size()), observation.intensity, 0, 0}, observation.regions);
  first_scene.emissions.apply(first_index, first_uniform);
  second_scene.emissions.apply(second_index, second_uniform);
  check(first_index == 0 && second_index == 0 && first_uniform.emission_params ==
            second_uniform.emission_params && first_uniform.emission_regions ==
            second_uniform.emission_regions && second_uniform.emission_params[0] == 1,
        "Fresh scene emission payload failed its independent scene-local index contract");
  mw34::submission::DrawEmissions allocation;
  check(allocation.allocated_bytes() == 0, "Empty emission storage retained an allocation");
  allocation.capture({1, 1.6f, 0, 0}, observation.regions);
  const auto first_allocation = allocation.allocated_bytes();
  for (unsigned index = 1; index < 129; ++index)
    allocation.capture({1, 1.6f, 0, 0}, observation.regions);
  // One fixed payload is33 shader vec4 values, including unused mask slots.
  // Count allocated capacity after vector growth, rather than logical records.
  const auto payload_bytes = sizeof(std::array<float, 4>) * 33;
  check(first_allocation >= payload_bytes && allocation.allocated_bytes() >= 129 * payload_bytes &&
            allocation.allocated_bytes() > first_allocation,
        "Emission staging byte accessor omitted capacity growth or fixed mask storage");

  Matrix moved{0,0,-1,0,1,0,1,0,0,7,2,3};
  check(rigid_matrix(moved),"Rigid copied native pose was not recognized");
  auto scaled=moved;
  scaled[0]=2;
  check(!rigid_matrix(scaled),"Nonrigid vehicle pose could silently scale its physical offset");
  const auto inverse=inverse_matrix(moved);
  check(bool(inverse), "Analytic affine pose unexpectedly singular");
  const Point witness{2,5,-4};
  const auto transformed=transform_point(moved,witness);
  check(transformed==Point{3,7,1}, "Owned pose did not map the independent point witness");
  const auto recovered=transform_point(*inverse,transformed);
  check(recovered==witness, "Owned inverse pose did not recover the point witness");
  const auto unit=compose_matrix(moved,*inverse);
  check(unit==identity_matrix,"Owned affine composition lost row-vector translation order");
  auto singular=identity_matrix;
  singular[0]=0;
  check(!inverse_matrix(singular),"Singular owned pose was admitted");
  singular=identity_matrix;
  singular[11]=std::numeric_limits<float>::quiet_NaN();
  check(!inverse_matrix(singular),"Nonfinite owned pose was admitted");
  VisibleSources bounded;
  bounded.set_eye({0,0,0});
  for(unsigned index=0;index<800;++index) {
    Observation isolated=observation;
    auto& light=isolated.physical_lights.front().light;
    light.start[0]=float(800-index);
    light.end[0]=light.start[0];
    bounded.observe(isolated);
  }
  check(bounded.candidates().size()<=VisibleSources::maximum_sources,
        "Retained fixture expansion exceeded the existing candidate bound");
  const auto selected=mw34::effects::rank_frame_lights(bounded.candidates(),{0,0,0},64,16);
  check(selected.params[0]==48 && selected.lights[0].start[0]==1 &&
        selected.lights[47].start[0]==48,
        "Bounded streaming selection dropped a nearer late physical lamp");

  std::fprintf(stderr, "[NATIVE_FIXTURE_SOURCE_CONTRACTS] cases=%u failures=0\n", passed);
}
