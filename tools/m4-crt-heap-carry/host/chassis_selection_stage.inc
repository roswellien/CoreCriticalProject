// Additional catalogue entries enter the original Instant Action dropdown and
// the Mech Lab's owning preview collection. Original input callbacks choose the
// configuration; no selected index or loadout is injected by this adapter.
void chassis_instant_action_widget(unsigned widget, unsigned stock_count,
                                   unsigned message, const char* role) {
    chassis_read();
    if (additional_chassis.records.empty()) return;
    if (!readable(widget, 0x170))
        throw std::runtime_error("Additional chassis: Instant Action widget unavailable");
    const unsigned first = load(widget + 0x15c), last = load(widget + 0x160);
    if (!first || last < first || (last - first) % 4 ||
        !readable(first, last - first))
        throw std::runtime_error("Additional chassis: unexpected original Instant Action list");
    const unsigned count = (last - first) / 4;
    // Enemy lists can be rebuilt independently by 48A930. Never duplicate rows
    // when the outer 48AAC0 initializer returns through the same adapter.
    if (count != stock_count && count != stock_count + additional_chassis.records.size())
        throw std::runtime_error("Additional chassis: unexpected Instant Action row count");
    if (count != stock_count) {
        for (unsigned i = 0; i < additional_chassis.records.size(); ++i)
            if (load(load(first + 4 * (stock_count + i)) + 4) != mw34::chassis::first_runtime_id + i)
                throw std::runtime_error("Additional chassis: Instant Action row identity mismatch");
        return;
    }
    for (unsigned i = 0; i < additional_chassis.records.size(); ++i) {
        auto& record = additional_chassis.records[i];
        const unsigned id = mw34::chassis::first_runtime_id + i;
        const unsigned text = chassis_text(record.display_text, record.registration.name);
        const unsigned label = gheap_alloc(256, true);
        if (!label) throw std::runtime_error("Additional chassis: label allocation failed");
        unsigned row;
        try {
            chassis_call(0x575fd0, 0, {label, 256, message, text}, false);
            row = chassis_call(0x48bac0, widget, {label, id});
        } catch (...) { gheap_free(label); throw; }
        gheap_free(label);
        if (row != stock_count + i ||
            load(load(load(widget + 0x15c) + 4 * row) + 4) != id)
            throw std::runtime_error("Additional chassis: Instant Action insertion displaced a stock row");
        std::fprintf(stderr, "Additional chassis selectable: role=%s id=%s index=%u row=%u\n",
                     role, record.registration.id.c_str(), id, row);
    }
}

void chassis_instant_action_enemies(unsigned dialog) {
    for (unsigned i = 0; i < 6; ++i)
        chassis_instant_action_widget(dialog + 0x138f8 + i * 0x868,
                                     i ? 20 : 19, 0x28f, "enemy");
}
void chassis_instant_action_list(unsigned dialog) {
    chassis_instant_action_widget(dialog + 0x11fc8, 18, 0x18b, "commander");
    for (unsigned i = 0; i < 3; ++i)
        chassis_instant_action_widget(dialog + 0x12830 + i * 0x434,
                                     19, 0x28d, "lancemate");
    // Progression mode leaves the enemy mech widgets empty; 48A930 owns their
    // normal-mode population and extension, including later mode changes.
}

void chassis_lab_inventory(unsigned inventory) {
    if (!inventory) return; // The original widget also accepts an empty source.
    if (!readable(inventory, 0x14))
        throw std::runtime_error("Additional chassis: Mech Lab inventory unavailable");
    // A pack registers a chassis; it does not grant salvage in a campaign.
    // The original unlimited inventory flag identifies the Instant Action pool.
    if (!runtime.memory().load<std::uint8_t>({inventory + 0x10})) return;
    const unsigned sentinel = load(inventory + 8);
    if (!sentinel || !readable(sentinel, 12))
        throw std::runtime_error("Additional chassis: invalid inventory list");
    std::set<unsigned> present, visited;
    for (unsigned node = load(sentinel); node != sentinel; node = load(node)) {
        if (!node || !readable(node, 12) || !visited.insert(node).second || visited.size() > 4096)
            throw std::runtime_error("Additional chassis: malformed inventory chain");
        const unsigned item = load(node + 8);
        if (!item || !readable(item, 0x18))
            throw std::runtime_error("Additional chassis: invalid inventory item");
        if (load(item) == 0x5bc160) present.insert(load(item + 0x14));
    }
    for (unsigned i = 0; i < additional_chassis.records.size(); ++i) {
        const unsigned id = mw34::chassis::first_runtime_id + i;
        if (present.count(id)) continue;
        const unsigned item = chassis_call(0x471c10, inventory, {id});
        if (!item || !readable(item, 0x18) || load(item) != 0x5bc160 || load(item + 0x14) != id)
            throw std::runtime_error("Additional chassis: original inventory insertion failed");
        // 470E30 marks each stock item unlimited as well as its inventory.
        // 471C10 creates a finite item by default; without the item flag the
        // roster validator consumes the Commander's only unit and substitutes
        // a stock chassis for the next lancemate choosing the same addition.
        runtime.memory().store<std::uint8_t>({item + 0x10}, 1);
        std::fprintf(stderr, "Additional chassis inventory: id=%s index=%u\n",
                     additional_chassis.records[i].registration.id.c_str(), id);
    }
}

void chassis_lab_previews(unsigned controller) {
    chassis_read();
    if (additional_chassis.records.empty()) return;
    if (!readable(controller, 0x80))
        throw std::runtime_error("Additional chassis: Mech Lab controller unavailable");
    const unsigned first = load(controller + 0x20), last = load(controller + 0x24);
    const unsigned capacity = load(controller + 0x28);
    if (!first || last < first || capacity < last || (last - first) % 4 ||
        (last - first) / 4 != 19 || !readable(first, last - first))
        throw std::runtime_error("Additional chassis: unexpected original preview collection");
    // The original initializer inlines vector growth. Build the extension with
    // its allocator and 44FCC0 constructor, then transfer it to the same owning
    // vector. 450390 destroys every element with 44FCE0 + operator delete.
    const unsigned count = 19 + unsigned(additional_chassis.records.size());
    const unsigned storage = chassis_call(0x5abd26, 0, {4 * count}, false);
    if (!storage) throw std::runtime_error("Additional chassis: preview collection allocation failed");
    std::vector<unsigned> created;
    try {
        for (unsigned i = 0; i < 19; ++i) store(storage + 4 * i, load(first + 4 * i));
        for (unsigned i = 0; i < additional_chassis.records.size(); ++i) {
            const unsigned object = chassis_call(0x5abd26, 0, {0x14}, false);
            if (!object) throw std::runtime_error("Additional chassis: preview allocation failed");
            created.push_back(object);
            chassis_call(0x44fcc0, object, {mw34::chassis::first_runtime_id + i});
            store(storage + 4 * (19 + i), object);
        }
    } catch (...) {
        // 44FCC0 is nonthrowing and starts with a null model; no resource has
        // been loaded into these new objects before they enter the collection.
        for (unsigned object : created) chassis_call(0x5abd1a, 0, {object}, false);
        chassis_call(0x5abd1a, 0, {storage}, false);
        throw;
    }
    store(controller + 0x20, storage);
    store(controller + 0x24, storage + 4 * count);
    store(controller + 0x28, storage + 4 * count);
    chassis_call(0x5abd1a, 0, {first}, false);
    std::fprintf(stderr, "Additional chassis previews: stock=19 added=%zu\n",
                 additional_chassis.records.size());
}

void* chassis_selection_body(State* s, unsigned target, void* p, Body body) {
    chassis_read();
    if (target == 0x449220) {
        if (!additional_chassis.records.empty()) chassis_lab_inventory(load(state.gpr.rsp.dword + 4));
        return body(s, target, p);
    }
    const unsigned object = state.gpr.rcx.dword;
    void* result = body(s, target, p);
    const State returned = state;
    try {
        // 408B40 prepares/returns the active stockpile before 408C30 validates
        // the roster. Waiting for the Mech Lab inventory widget (449220) lets
        // that validator reject new IDs and cycle back into the stock roster.
        if (target == 0x408b40 && state.gpr.rax.dword)
            chassis_lab_inventory(state.gpr.rax.dword);
        else if (target == 0x48aac0) chassis_instant_action_list(object);
        else if (target == 0x48a930) chassis_instant_action_enemies(object);
        else if (target == 0x44ffc0 && state.gpr.rax.dword) chassis_lab_previews(object);
    } catch (...) { state = returned; throw; }
    state = returned;
    return result;
}
