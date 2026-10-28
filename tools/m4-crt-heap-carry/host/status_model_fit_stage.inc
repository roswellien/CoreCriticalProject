void override_preview_record_rect(unsigned role, RECT box) {
    if (role == WideLeft || role == WideRight)
        override_state().preview_boxes[role] = box;
}
unsigned override_preview_role() const {
    for (unsigned i = depth; i > 0; --i) {
        if (returns[i - 1] == 0x441480)
            return WideLeft;
        if (returns[i - 1] == 0x442a87)
            return WideRight;
    }
    return WideWorld;
}
void override_preview_point(double x, double y) {
    auto &o = override_state();
    if (!std::isfinite(x) || !std::isfinite(y))
        throw std::runtime_error("Status models: nonfinite projected bounds");
    if (!o.preview_has_bounds) {
        o.preview_bounds = {x, y, x, y};
        o.preview_has_bounds = true;
    } else {
        o.preview_bounds[0] = std::min(o.preview_bounds[0], x);
        o.preview_bounds[1] = std::min(o.preview_bounds[1], y);
        o.preview_bounds[2] = std::max(o.preview_bounds[2], x);
        o.preview_bounds[3] = std::max(o.preview_bounds[3], y);
    }
}
void override_preview_finish(D3DDev *device = nullptr) {
    OverrideMxcsr preserve;
    mw34::vkscene::HostFpEnvironment fp;
    auto &o = override_state();
    if (o.preview_fit_applied)
        return;
    if (!device)
        for (auto &d : host.devices)
            if (d.in_scene) {
                if (device)
                    throw std::runtime_error("Status models: ambiguous preview scene");
                device = &d;
            }
    if (!device || !o.preview_has_bounds)
        return;
    // Include retained original stumps and any CPU-clipped replacement seams.
    for (size_t i = o.preview_begin; i < device->commands.size(); ++i) {
        const auto &c = device->commands[i];
        if (c.kind != D3DCmd::Draw || !c.condition_schematic || c.model)
            continue;
        for (size_t v = 0; v < c.vertices.size(); v += 32) {
            float xy[2];
            std::memcpy(xy, c.vertices.data() + v, sizeof xy);
            override_preview_point(xy[0], xy[1]);
        }
    }
    const auto box = o.preview_boxes.at(o.preview_role);
    const auto fit = mw34::status::fit(o.preview_bounds, {double(box.left), double(box.top),
                                                          double(box.right), double(box.bottom)});
    o.preview_fit_applied = true;
    if (!fit.changed())
        return;
    for (size_t i = o.preview_begin; i < device->commands.size(); ++i) {
        auto &c = device->commands[i];
        if (c.kind != D3DCmd::Draw || !c.condition_schematic)
            continue;
        if (c.model) {
            auto instance = std::make_shared<mw34::vkscene::ModelInstance>(*c.model);
            instance->projection[1] *= float(fit.scale);
            instance->projection[2] *= float(fit.scale);
            instance->projection[3] = float(instance->projection[3] * fit.scale + fit.x);
            instance->projection[4] = float(instance->projection[4] * fit.scale + fit.y);
            c.model = std::move(instance);
        } else {
            for (size_t v = 0; v < c.vertices.size(); v += 32) {
                float xy[2];
                std::memcpy(xy, c.vertices.data() + v, sizeof xy);
                xy[0] = float(xy[0] * fit.scale + fit.x);
                xy[1] = float(xy[1] * fit.scale + fit.y);
                std::memcpy(c.vertices.data() + v, xy, sizeof xy);
            }
        }
    }
    if (host.frames % 100 == 0)
        o.log << "{\"event\":\"preview_fit\",\"frame\":" << host.frames
              << ",\"role\":" << o.preview_role << ",\"scale\":" << fit.scale << ",\"x\":" << fit.x
              << ",\"y\":" << fit.y << "}\n";
}
