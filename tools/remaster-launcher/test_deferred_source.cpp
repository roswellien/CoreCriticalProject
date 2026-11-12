// Exercise the maintained deferred-draw adapter with authored guest memory.
// No original instructions, geometry, textures or graphics backend are required.
#include "../m4-crt-heap-carry/host/body_dispatch.hpp"
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <functional>
#include <iostream>
#include <map>
#include <stdexcept>
#include <vector>

namespace {
constexpr unsigned queue_count_address = 0x803550;
constexpr unsigned descriptor_base = 0x80cd9c;
constexpr unsigned vertex_base = 0x82449c;
constexpr unsigned vertex_capacity = 24000;
constexpr unsigned stack_address = 0x1000;
constexpr unsigned side_effect_address = 0x1100;
constexpr unsigned flush_return = 0x57e2ed;
constexpr unsigned primitive_type = 6;
constexpr unsigned vertex_count = 4;
constexpr unsigned fallback_role = 3;

enum WideHudRole : unsigned { WideWorld = 0, WideLeft = 1, WideRight = 2 };

void require(bool condition, const char *message) {
    if (!condition)
        throw std::runtime_error(message);
}

template <class Callback> void require_rejected(Callback callback, const char *message) {
    bool rejected = false;
    try {
        callback();
    } catch (const std::runtime_error &) {
        rejected = true;
    }
    require(rejected, message);
}

struct Register {
    unsigned dword{};
};

struct State {
    struct {
        Register rsp, rsi, rax;
    } gpr;
};

using Body = std::function<void *(State *, unsigned, void *)>;

struct FixtureStage {
    struct {
        unsigned frames{17};
    } host;
    State state;
    std::array<unsigned, 8> returns{};
    unsigned depth{};
    bool widescreen = true;
    bool source_suppressed{};
    unsigned hud_detail_frame{};
    unsigned blocked_address{}, blocked_size{};
    std::vector<unsigned char> memory = std::vector<unsigned char>(0x900000);

    bool wide_on() const { return widescreen; }
    bool override_suppress_draw() const { return source_suppressed; }
    FILE *wide_log_file() const { return nullptr; }

    bool readable(unsigned address, unsigned size) const {
        if (address > memory.size() || size > memory.size() - address)
            return false;
        return !blocked_size || std::uint64_t(address) + size <= blocked_address ||
               std::uint64_t(blocked_address) + blocked_size <= address;
    }

    unsigned load(unsigned address) const {
        require(readable(address, 4), "Fixture attempted an unreadable word load");
        unsigned value{};
        std::memcpy(&value, memory.data() + address, 4);
        return value;
    }

    void store(unsigned address, unsigned value) {
        require(readable(address, 4), "Fixture attempted an unwritable word store");
        std::memcpy(memory.data() + address, &value, 4);
    }

    [[noreturn]] void deny(const char *message, unsigned) const {
        throw std::runtime_error(message);
    }

#include "../m4-crt-heap-carry/host/hud_deferred_stage.inc"

    void producer(unsigned return_address) {
        returns.fill(0);
        depth = return_address ? 1U : 0U;
        returns[0] = return_address;
    }

    void flush(unsigned descriptor) {
        producer(0);
        source_suppressed = false;
        state.gpr.rsp.dword = stack_address;
        state.gpr.rsi.dword = descriptor;
        store(stack_address, flush_return);
    }

    unsigned append_entry(unsigned material, unsigned type = primitive_type,
                          unsigned count = vertex_count, unsigned vertices = vertex_base) {
        const unsigned queued_before = load(queue_count_address);
        const unsigned descriptor = descriptor_base + 16 * queued_before;
        store(descriptor, type);
        store(descriptor + 4, count);
        store(descriptor + 8, material);
        store(descriptor + 12, vertices);
        store(queue_count_address, queued_before + 1);
        return descriptor;
    }

    // The callback authors queue entries and unrelated guest effects. Its
    // post-call memory image is the oracle for detecting adapter writes.
    void run_body(unsigned adapter_target, bool suppress_after_body,
                  const std::function<void()> &queue_effects) {
        unsigned body_calls = 0;
        std::vector<unsigned char> expected_memory;
        int return_marker = 0;
        const auto original_body = [&](State *guest_state, unsigned target,
                                       void *context) -> void * {
            require(guest_state == &state && target == adapter_target && context == &return_marker,
                    "Adapter changed the original callback arguments");
            ++body_calls;
            store(side_effect_address, load(side_effect_address) + 1);
            queue_effects();
            guest_state->gpr.rax.dword = 0x12345678;
            source_suppressed = suppress_after_body;
            expected_memory = memory;
            return context;
        };
        void *result = adapter_target == 0x53f2e0
                           ? hud_deferred_source_body(&state, adapter_target, &return_marker,
                                                      original_body)
                           : hud_panel_body(&state, adapter_target, &return_marker, original_body);
        require(body_calls == 1, "Adapter did not execute the original callback exactly once");
        require(result == &return_marker, "Adapter changed the original callback return value");
        require(state.gpr.rax.dword == 0x12345678, "Adapter changed the original guest result");
        require(memory == expected_memory, "Adapter changed original queue or guest side effects");
    }

    unsigned enqueue(unsigned material, bool suppress_after_body, bool append = true,
                     unsigned type = primitive_type, unsigned count = vertex_count,
                     unsigned vertices = vertex_base) {
        producer(0);
        const unsigned descriptor = descriptor_base + 16 * load(queue_count_address);
        run_body(0x53f2e0, suppress_after_body, [&] {
            if (append)
                append_entry(material, type, count, vertices);
        });
        return descriptor;
    }

    unsigned enqueue_hud(unsigned return_address) {
        producer(return_address);
        const unsigned descriptor = descriptor_base + 16 * load(queue_count_address);
        run_body(0x57bf80, false, [&] { append_entry(0); });
        return descriptor;
    }
};

void queue_routes_reach_adapters() {
    for (unsigned target : {0x53f2e0U, 0x57bf80U, 0x57e110U})
        require(mw34::body_dispatch::handled(target),
                "Fast body dispatch bypasses an original deferred queue adapter");
    require(!mw34::body_dispatch::handled(0x53f2e1),
            "Fast body dispatch accepted an unaligned queue target");
}

void suppression_survives_scope_exit() {
    for (bool widescreen : {false, true}) {
        for (unsigned material : {0U, 0x2200U}) {
            FixtureStage stage;
            stage.widescreen = widescreen;
            // Distinct, authored TL bytes must survive both enqueue and lookup.
            for (unsigned byte = 0; byte < 32 * vertex_count; ++byte)
                stage.memory[vertex_base + byte] = static_cast<unsigned char>(byte ^ 0x5aU);
            const unsigned descriptor = stage.enqueue(material, true);
            require(stage.load(side_effect_address) == 1, "Original guest side effect was lost");
            stage.flush(descriptor);
            const auto original_memory = stage.memory;
            require(stage.hud_deferred_source_suppressed(primitive_type, vertex_base, vertex_count),
                    "Deferred source suppression was lost after its producer returned");
            require(stage.memory == original_memory,
                    "Deferred lookup changed original guest bytes");
            if (!widescreen)
                require(stage.hud_deferred_role(primitive_type, vertex_base, vertex_count,
                                                fallback_role) == fallback_role,
                        "Source suppression changed widescreen-off HUD presentation");
        }
    }
}

void independent_sorted_provenance() {
    FixtureStage stage;
    const unsigned replaced = stage.enqueue(0x2200, true);
    const unsigned stock = stage.enqueue(0x2200, false);
    const unsigned left = stage.enqueue_hud(0x43c767);
    const unsigned right = stage.enqueue_hud(0x43c77d);
    struct Submission {
        unsigned descriptor, role;
        bool suppressed;
    };
    // The original sorter changes submission order without moving descriptors.
    for (const auto submission : {Submission{right, WideRight, false},
                                  Submission{left, WideLeft, false},
                                  Submission{stock, fallback_role, false},
                                  Submission{replaced, WideWorld, true}}) {
        stage.flush(submission.descriptor);
        require(stage.hud_deferred_source_suppressed(primitive_type, vertex_base, vertex_count) ==
                    submission.suppressed,
                "Sorted descriptors acquired another producer's suppression");
        if (!submission.suppressed)
            require(stage.hud_deferred_role(primitive_type, vertex_base, vertex_count,
                                            fallback_role) == submission.role,
                    "Sorted descriptors lost their original HUD role");
    }
    stage.flush(stock);
    stage.source_suppressed = true;
    require(!stage.hud_deferred_source_suppressed(primitive_type, vertex_base, vertex_count),
            "Unknown stock polygon inherited the current caller's suppression");
}

void source_range_preserves_earlier_hud_entries() {
    FixtureStage stage;
    const unsigned earlier_hud = stage.enqueue_hud(0x43c767);
    struct Entry {
        unsigned material, count, vertices;
    };
    const std::array<Entry, 3> entries{{{0, 3, vertex_base + 128},
                                      {0x2200, 4, vertex_base + 256},
                                      {0x3300, 5, vertex_base + 384}}};
    std::array<unsigned, 3> descriptors{};
    stage.producer(0);
    stage.run_body(0x53f2e0, true, [&] {
        for (std::size_t index = 0; index < entries.size(); ++index) {
            const auto &entry = entries[index];
            descriptors[index] =
                stage.append_entry(entry.material, primitive_type, entry.count, entry.vertices);
        }
    });
    require(stage.load(queue_count_address) == 4, "Source adapter changed the appended range");
    for (std::size_t index = entries.size(); index-- > 0;) {
        const auto &entry = entries[index];
        stage.flush(descriptors[index]);
        require(stage.hud_deferred_source_suppressed(primitive_type, entry.vertices, entry.count),
                "Source range omitted an appended material descriptor");
    }
    stage.flush(earlier_hud);
    require(!stage.hud_deferred_source_suppressed(primitive_type, vertex_base, vertex_count),
            "Source range suppressed an earlier unrelated HUD descriptor");
    require(stage.hud_deferred_role(primitive_type, vertex_base, vertex_count, fallback_role) ==
                WideLeft,
            "Source range discarded earlier HUD provenance");
}

void identical_source_record_preserves_hud_role() {
    FixtureStage stage;
    unsigned descriptor{};
    stage.run_body(0x53f2e0, true, [&] { descriptor = stage.enqueue_hud(0x43c77d); });
    stage.flush(descriptor);
    require(stage.hud_deferred_source_suppressed(primitive_type, vertex_base, vertex_count),
            "Source range did not merge suppression into identical queued metadata");
    require(stage.hud_deferred_role(primitive_type, vertex_base, vertex_count, fallback_role) ==
                WideRight,
            "Source range overwrote an identical descriptor's HUD role");
}

void invalid_source_count_changes_fail_after_original_body() {
    struct Counts {
        unsigned before, after;
    };
    for (const auto counts : {Counts{5, 4}, Counts{5, 0}, Counts{6000, 6001},
                              Counts{6001, 6001}, Counts{0, 6001}}) {
        FixtureStage stage;
        stage.store(queue_count_address, counts.before);
        require_rejected(
            [&] {
                stage.run_body(0x53f2e0, true,
                               [&] { stage.store(queue_count_address, counts.after); });
            },
            "Invalid source queue-count transition did not fail visibly");
        require(stage.load(side_effect_address) == 1,
                "Source count validation skipped or repeated the original body");
        require(stage.load(queue_count_address) == counts.after,
                "Source count validation changed original guest effects");
    }
}

void source_exception_propagates_and_clears_metadata() {
    FixtureStage stage;
    const unsigned earlier_hud = stage.enqueue_hud(0x43c767);
    unsigned body_calls = 0;
    int context_marker = 0;
    std::vector<unsigned char> expected_memory;
    const auto throwing_body = [&](State *guest_state, unsigned target, void *context) -> void * {
        require(guest_state == &stage.state && target == 0x53f2e0 && context == &context_marker,
                "Source exception path changed callback arguments");
        ++body_calls;
        stage.store(side_effect_address, stage.load(side_effect_address) + 1);
        stage.append_entry(0x2200);
        expected_memory = stage.memory;
        throw std::runtime_error("Authored source-body failure");
    };
    bool propagated = false;
    try {
        (void)stage.hud_deferred_source_body(&stage.state, 0x53f2e0, &context_marker,
                                             throwing_body);
    } catch (const std::runtime_error &error) {
        propagated = std::strcmp(error.what(), "Authored source-body failure") == 0;
    }
    require(propagated && body_calls == 1, "Source adapter changed original exception propagation");
    require(stage.memory == expected_memory,
            "Source exception cleanup changed original guest bytes");
    stage.flush(earlier_hud);
    require(stage.hud_deferred_role(primitive_type, vertex_base, vertex_count, fallback_role) ==
                fallback_role,
            "Source exception left deferred HUD metadata live");
    require(!stage.hud_deferred_source_suppressed(primitive_type, vertex_base, vertex_count),
            "Source exception left deferred source metadata live");
}

void exact_flush_identity_is_required() {
    FixtureStage stage;
    const unsigned descriptor = stage.enqueue(0x2200, true);
    stage.flush(descriptor);
    stage.store(stack_address, flush_return + 1);
    require(!stage.hud_deferred_source_suppressed(primitive_type, vertex_base, vertex_count),
            "An unrelated provider call consumed deferred source provenance");
    stage.store(stack_address, flush_return);
    stage.state.gpr.rsi.dword = descriptor + 16;
    require(!stage.hud_deferred_source_suppressed(primitive_type, vertex_base, vertex_count),
            "An unknown descriptor inherited source provenance");
    stage.state.gpr.rsi.dword = descriptor;
    stage.blocked_address = stack_address;
    stage.blocked_size = 4;
    require(!stage.hud_deferred_source_suppressed(primitive_type, vertex_base, vertex_count),
            "Unreadable API return was accepted as the original flush");
}

void changed_known_descriptors_are_rejected() {
    // Test both changed live descriptors and changed API arguments. Matching a
    // new live value must not override the producer's retained identity.
    for (unsigned mutation = 0; mutation < 11; ++mutation) {
        FixtureStage stage;
        const unsigned descriptor = stage.enqueue(0x2200, true);
        stage.flush(descriptor);
        unsigned type = primitive_type, count = vertex_count, vertices = vertex_base;
        switch (mutation) {
        case 0:
            stage.store(descriptor, ++type);
            break;
        case 1:
            stage.store(descriptor + 4, ++count);
            break;
        case 2:
            stage.store(descriptor + 8, 0x3300);
            break;
        case 3:
            vertices += 32;
            stage.store(descriptor + 12, vertices);
            break;
        case 4:
            ++type;
            break;
        case 5:
            ++count;
            break;
        case 6:
            vertices += 32;
            break;
        case 7:
            ++stage.host.frames;
            break;
        case 8:
            stage.blocked_address = descriptor;
            stage.blocked_size = 16;
            break;
        case 9:
            stage.store(descriptor, primitive_type + 1);
            break;
        case 10:
            stage.blocked_address = vertex_base;
            stage.blocked_size = 32 * vertex_count;
            break;
        }
        require_rejected(
            [&] { (void)stage.hud_deferred_source_suppressed(type, vertices, count); },
            "Changed known source descriptor did not fail visibly");
        require_rejected(
            [&] { (void)stage.hud_deferred_role(type, vertices, count, fallback_role); },
            "HUD lookup accepted changed known descriptor identity");
    }
}

void queue_reuse_does_not_retain_suppression() {
    for (bool advance_frame : {false, true}) {
        FixtureStage stage;
        const unsigned descriptor = stage.enqueue(0x2200, true);
        if (advance_frame)
            ++stage.host.frames;
        stage.store(queue_count_address, 0);
        const unsigned reused = stage.enqueue(0x2200, false);
        require(reused == descriptor, "Fixture did not reuse the original queue slot");
        stage.flush(reused);
        require(!stage.hud_deferred_source_suppressed(primitive_type, vertex_base, vertex_count),
                "A fresh queue inherited a previous source suppression token");
        require(stage.hud_deferred_role(primitive_type, vertex_base, vertex_count, fallback_role) ==
                    fallback_role,
                "A fresh queue inherited previous HUD provenance");
    }
}

void nonqueued_and_retained_original_paths() {
    // Full, immediate and separately flagged paths do not append descriptors.
    for (unsigned queued : {0U, 17U, 6000U}) {
        FixtureStage stage;
        stage.store(queue_count_address, queued);
        const unsigned descriptor = stage.enqueue(0x2200, true, false);
        require(stage.load(queue_count_address) == queued, "Adapter changed a nonqueued count");
        stage.flush(descriptor);
        require(!stage.hud_deferred_source_suppressed(primitive_type, vertex_base, vertex_count),
                "A nonqueued polygon acquired suppression provenance");
    }
    for (bool widescreen : {false, true}) {
        FixtureStage stage;
        stage.widescreen = widescreen;
        // The producer's policy is false for stock/fallback geometry and a
        // preview whose replacement has not emitted. The tracker preserves it.
        const unsigned descriptor = stage.enqueue(0x2200, false);
        stage.flush(descriptor);
        require(!stage.hud_deferred_source_suppressed(primitive_type, vertex_base, vertex_count),
                "Retained original geometry acquired deferred suppression");
    }
}

void invalid_source_queue_ranges_are_rejected() {
    struct QueueRecord {
        unsigned count, vertices;
    };
    for (const auto record : {QueueRecord{0, vertex_base},
                              QueueRecord{vertex_capacity + 1, vertex_base},
                              QueueRecord{vertex_count, vertex_base - 32},
                              QueueRecord{vertex_count, vertex_base + 32 * vertex_capacity - 32},
                              QueueRecord{vertex_count, 0xfffffff0U}}) {
        FixtureStage stage;
        require_rejected(
            [&] {
                (void)stage.enqueue(0x2200, true, true, primitive_type, record.count,
                                    record.vertices);
            },
            "Suppressed source entry outside the original queue contract was accepted");
    }
}
} // namespace

int main() {
    try {
        queue_routes_reach_adapters();
        suppression_survives_scope_exit();
        independent_sorted_provenance();
        source_range_preserves_earlier_hud_entries();
        identical_source_record_preserves_hud_role();
        invalid_source_count_changes_fail_after_original_body();
        source_exception_propagates_and_clears_metadata();
        exact_flush_identity_is_required();
        changed_known_descriptors_are_rejected();
        queue_reuse_does_not_retain_suppression();
        nonqueued_and_retained_original_paths();
        invalid_source_queue_ranges_are_rejected();
        std::cout << "PASS: deferred source provenance, HUD roles, queue identity and guest effects"
                     "\n";
        return 0;
    } catch (const std::exception &error) {
        std::cerr << "FAIL: " << error.what() << '\n';
        return 1;
    }
}
