// Original definition construction remains 46B7A0 -> 46B890 -> 46BA40.
// This extends lookup and ownership; it does not seed a definition object.
struct AdditionalChassisRecord {
    mw34::chassis::Registration registration;
    unsigned resource_text{}, display_text{}, definition{};
};
struct AdditionalChassisState {
    bool read{};
    std::vector<AdditionalChassisRecord> records;
    std::map<unsigned, unsigned> actor_roots;
} additional_chassis;

void chassis_retire_root(unsigned root) { additional_chassis.actor_roots.erase(root); }
const char* chassis_actor_resource(unsigned root) {
    const auto at = additional_chassis.actor_roots.find(root);
    if (at == additional_chassis.actor_roots.end()) return nullptr;
    const auto& record = additional_chassis.records.at(at->second - mw34::chassis::first_runtime_id);
    return record.registration.visual_template.empty() ? nullptr : record.registration.resource.c_str();
}

static bool chassis_target(unsigned target) {
    switch (target) {
    case 0x41e9a0: case 0x41df10:
    case 0x4844b0: case 0x4845f0: case 0x484650: case 0x484670:
    case 0x4846a0: case 0x4846e0: case 0x484700: case 0x484720: return true;
    default: return false;
    }
}

void chassis_read() {
    auto& a = additional_chassis;
    if (a.read) return;
    for (const auto& r : mw34::chassis::configured_catalog()) a.records.push_back({r});
    a.read = true;
}
unsigned chassis_text(unsigned& address, const std::string& text) {
    if (!address) {
        address = gheap_alloc(unsigned(text.size() + 1), true);
        if (!address) throw std::runtime_error("Additional chassis: text allocation failed");
        write_bytes(address, text.c_str(), unsigned(text.size() + 1));
    }
    return address;
}
unsigned chassis_call(unsigned target, unsigned object, std::initializer_list<unsigned> arguments,
                      bool callee_pops = true) {
    const State saved = state; OverrideMxcsr fp;
    try {
        state.gpr.rcx.dword = object;
        const unsigned result = call_guest(target, arguments, callee_pops,
                                          "Additional chassis", 0, true);
        state = saved; return result;
    } catch (...) { state = saved; throw; }
}
void chassis_cleanup() {
    headlight_clear();
    additional_chassis.actor_roots.clear();
    for (auto& r : additional_chassis.records) {
        if (r.definition) {
            chassis_call(0x46b9b0, r.definition, {});
            chassis_call(0x5abd1a, 0, {r.definition}, false); // Original cdecl operator delete.
            r.definition = 0;
        }
        if (r.resource_text) { gheap_free(r.resource_text); r.resource_text = 0; }
        if (r.display_text) { gheap_free(r.display_text); r.display_text = 0; }
    }
}
void* chassis_body(State* s, unsigned target, void* p, Body body) {
    chassis_read();
    if (target == 0x41e9a0 || target == 0x41df10) {
        // These original actor getters fuse their final direct JMP into the
        // lifted body. Their inherited lookup therefore has no router callback.
        // Read the recovered actor -> MechData -> catalogue index, execute the
        // original getter/return, then supply its genuine extended lookup result.
        const unsigned actor = state.gpr.rcx.dword;
        if (!readable(actor + 0x684, 4)) return body(s, target, p);
        const unsigned data = load(actor + 0x684);
        if (!data || !readable(data, 16)) return body(s, target, p);
        const unsigned index = load(data + 0xc);
        // Live actor construction may rename the copied model root. Retain the
        // actual actor's chassis identity independently of that display name.
        const unsigned root = readable(actor + 4, 4) ? load(actor + 4) : 0;
        if (root) {
            if (index >= mw34::chassis::first_runtime_id &&
                index - mw34::chassis::first_runtime_id < additional_chassis.records.size()) {
                const auto [at, inserted] = additional_chassis.actor_roots.insert_or_assign(root, index);
                if (inserted) std::fprintf(stderr, "Additional chassis actor: index=%u root=0x%08x\n", index, root);
            } else additional_chassis.actor_roots.erase(root);
        }
        void* result = body(s, target, p);
        if (index >= mw34::chassis::first_runtime_id &&
            index - mw34::chassis::first_runtime_id < additional_chassis.records.size())
            state.gpr.rax.dword = chassis_call(target == 0x41e9a0 ? 0x4846a0 : 0x484720, index, {});
        return result;
    }
    if (target == 0x4844b0) { chassis_cleanup(); return body(s, target, p); }
    const unsigned input = state.gpr.rcx.dword;
    if (target == 0x4845f0) {
        void* result = body(s, target, p);
        if (state.gpr.rax.dword != ~0U) return result;
        // Original _stricmp has already validated/read the caller's text.
        for (unsigned i = 0; i < additional_chassis.records.size(); ++i) {
            const auto& key = additional_chassis.records[i].registration.resource;
            bool match = readable(input, unsigned(key.size() + 1));
            for (unsigned n = 0; match && n <= key.size(); ++n) {
                const auto c = runtime.memory().load<std::uint8_t>({input + n});
                const unsigned char expected = n == key.size() ? 0 : key[n];
                match = (c >= 'A' && c <= 'Z' ? c + 32 : c) == expected;
            }
            if (match) { state.gpr.rax.dword = mw34::chassis::first_runtime_id + i; break; }
        }
        if (state.gpr.rax.dword == ~0U && readable(input, 14)) {
            std::string key;
            for (unsigned n=0; n<14; ++n) {
                const auto c=runtime.memory().load<std::uint8_t>({input+n});
                if (!c) break;
                key+=char(c);
            }
            const bool generated=key.size()==13 && key[0]=='c' &&
                std::all_of(key.begin()+1,key.end(),[](char c){return (c>='0'&&c<='9')||(c>='a'&&c<='f');});
            if (generated) throw std::runtime_error("Missing additional mech content: " + key +
                ". Enable the pack used by this saved configuration.");
        }
        return result;
    }
    if (input < mw34::chassis::first_runtime_id ||
        input - mw34::chassis::first_runtime_id >= additional_chassis.records.size())
        return body(s, target, p);
    auto& r = additional_chassis.records[input - mw34::chassis::first_runtime_id];
    if (target == 0x4846e0 || target == 0x484700 || target == 0x484720) {
        // Let the original metadata getter preserve its x87/fastcall contract.
        // This first boundary inherits mass/class/technology from a stock template.
        state.gpr.rcx.dword = r.registration.metadata_template;
        try { void* result = body(s, target, p); state.gpr.rcx.dword = input; return result; }
        catch (...) { state.gpr.rcx.dword = input; throw; }
    }
    void* result = body(s, target, p);
    if (target == 0x484650)
        state.gpr.rax.dword = chassis_text(r.resource_text, r.registration.resource);
    else if (target == 0x484670)
        state.gpr.rax.dword = chassis_text(r.display_text, r.registration.name);
    else if (target == 0x4846a0) {
        if (!r.definition) {
            r.definition = chassis_call(0x46b7a0, input, {});
            if (!r.definition) throw std::runtime_error("Additional chassis: original definition parser rejected " + r.registration.id);
            if (!readable(r.definition, 0x1a8) || load(r.definition) != input)
                throw std::runtime_error("Additional chassis: constructed definition identity mismatch");
            std::fprintf(stderr, "Additional chassis definition: id=%s index=%u object=0x%08x\n",
                         r.registration.id.c_str(), input, r.definition);
        }
        state.gpr.rax.dword = r.definition;
    }
    return result;
}
