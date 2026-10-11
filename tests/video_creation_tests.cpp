#include "graphics/direct_draw_creation.hpp"

#include <array>
#include <exception>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

using namespace mw34;
using namespace mw34::graphics;
constexpr GuestAddress scratch{0x1000};
constexpr GuestAddress initial{0x2000};
constexpr GuestAddress queried{0x3000};
constexpr GuestAddress receiver{0x4000};

void require(bool value, const char *message) {
    if (!value) {
        throw std::runtime_error(message);
    }
}

class FixtureProvider final : public DirectDrawCreationProvider {
  public:
    Hresult creation_status{};
    Hresult query_status{};
    Hresult restore_status{};
    std::uint32_t error_result{0xffffffff};
    bool write_creation{true};
    bool write_query{true};
    bool mutate_query_table{};
    bool mutate_restore_global{};
    bool throw_release{};
    std::vector<std::string> events;

    Hresult direct_draw_create(GuestMemory &memory, GuestAddress adapter, GuestAddress output,
                               GuestAddress outer) override {
        require(adapter.value == 0x5000 && output == scratch && outer.value == 0,
                "Creation arguments lost guest identity");
        events.emplace_back("create");
        if (write_creation) {
            memory.store<std::uint32_t>(output, initial.value);
        }
        return creation_status;
    }

    Hresult query_interface(GuestMemory &memory, ComMethod method, GuestAddress iid,
                            GuestAddress output) override {
        require(method.object == initial && method.target.value == 0xa000,
                "QI must resolve actual guest slot zero");
        require(iid == direct_draw4_iid && output == direct_draw4_global,
                "QI GUID/output destination mismatch");
        events.emplace_back("query");
        if (write_query) {
            memory.store<std::uint32_t>(output, queried.value);
        }
        if (mutate_query_table) {
            memory.store<std::uint32_t>({0x2108}, 0xa018);
        }
        return query_status;
    }

    std::uint32_t release(GuestMemory &memory, ComMethod method) override {
        const bool temporary = method.object == initial;
        const auto expected = temporary ? (mutate_query_table ? 0xa018U : 0xa008U) : 0xb008U;
        require(method.target.value == expected, "Release must reread guest vtable slot");
        require(temporary || method.object == queried, "Release object mismatch");
        if (!temporary) {
            require(memory.load<std::uint32_t>(direct_draw4_global) == queried.value,
                    "Global cleared before Release");
        }
        events.emplace_back(temporary ? "release-temporary" : "release-owned");
        if (throw_release) {
            throw std::runtime_error("fixture release refusal");
        }
        return 7; // Refcount is not the function's success return.
    }

    Hresult restore_display_mode(GuestMemory &memory, ComMethod method) override {
        require(method.object == queried && method.target.value == 0xb04c,
                "RestoreDisplayMode slot/object mismatch");
        events.emplace_back("restore");
        if (mutate_restore_global) {
            memory.store<std::uint32_t>(direct_draw4_global, initial.value);
        }
        return restore_status;
    }

    std::uint32_t report_error(Hresult status, GuestAddress file, std::uint32_t line) override {
        require(file == video_error_file, "Error file address mismatch");
        require((line == 0x3bb && status == creation_status && status != 0) ||
                    (line == 0x3bf && status == query_status && status != 0),
                "Error context/status mismatch");
        events.emplace_back(line == 0x3bb ? "creation-error" : "query-error");
        return error_result;
    }
};

struct Fixture {
    GuestMemory memory;
    FixtureProvider provider;
    Fixture() {
        constexpr auto rw = Permissions::read | Permissions::write;
        memory.map(scratch, 4, rw);
        memory.map(initial, 0x200, rw);
        memory.map(queried, 0x200, rw);
        memory.map(receiver, 4, rw);
        memory.map(direct_draw_adapter_receiver, 4, rw);
        memory.map(direct_draw4_global, 4, rw);
        memory.store<std::uint32_t>(direct_draw_adapter_receiver, receiver.value);
        memory.store<std::uint32_t>(receiver, 0x5000);
        memory.store<std::uint32_t>(initial, 0x2100);
        memory.store<std::uint32_t>({0x2100}, 0xa000);
        memory.store<std::uint32_t>({0x2108}, 0xa008);
        memory.store<std::uint32_t>(queried, 0x3100);
        memory.store<std::uint32_t>({0x3108}, 0xb008);
        memory.store<std::uint32_t>({0x314c}, 0xb04c);
        memory.store<std::uint32_t>(scratch, 0xfeedface);
        memory.store<std::uint32_t>(direct_draw4_global, 0x12345678);
    }
};

void test_success_and_teardown() {
    Fixture f;
    f.provider.mutate_query_table = true;
    require(create_direct_draw4(f.memory, f.provider, scratch) == 0, "Creation success return");
    require(f.memory.load<std::uint32_t>(direct_draw4_global) == queried.value,
            "QI output must remain owned");
    require(f.provider.events == std::vector<std::string>{"create", "query", "release-temporary"},
            "Creation ownership/order mismatch");
    f.provider.restore_status = 0x80004005;
    release_direct_draw4_after_dependents(f.memory, f.provider);
    require(f.memory.load<std::uint32_t>(direct_draw4_global) == 0, "Teardown must clear global");
    require(f.provider.events == std::vector<std::string>{"create", "query", "release-temporary",
                                                          "restore", "release-owned"},
            "Teardown order or ignored restore status mismatch");
    release_direct_draw4_after_dependents(f.memory, f.provider);
    require(f.provider.events.size() == 5, "Repeated teardown must be a no-op");
}

void test_failure_outputs_and_zero_tests() {
    for (const Hresult status : std::array<Hresult, 3>{1, 0x80004005, 0xffffffff}) {
        for (const bool writes : {false, true}) {
            Fixture creation;
            creation.provider.creation_status = status;
            creation.provider.write_creation = writes;
            creation.provider.error_result = 0x76543210;
            require(create_direct_draw4(creation.memory, creation.provider, scratch) == 0x76543210,
                    "Creation error helper return not preserved");
            require(creation.provider.events ==
                        std::vector<std::string>{"create", "creation-error"},
                    "Creation failure must not QI or Release");
            require(creation.memory.load<std::uint32_t>(scratch) ==
                        (writes ? initial.value : 0xfeedface),
                    "Creation failure output overwritten");
            require(creation.memory.load<std::uint32_t>(direct_draw4_global) == 0x12345678,
                    "Creation failure touched global interface");

            Fixture query;
            query.provider.query_status = status;
            query.provider.write_query = writes;
            require(create_direct_draw4(query.memory, query.provider, scratch) == 0xffffffff,
                    "QI failure return mismatch");
            require(query.provider.events ==
                        std::vector<std::string>{"create", "query", "query-error"},
                    "QI failure must not release temporary");
            require(query.memory.load<std::uint32_t>(direct_draw4_global) ==
                        (writes ? queried.value : 0x12345678),
                    "QI failure output must preserve actual provider writes");
        }
    }
}

void test_faults_and_partial_cleanup() {
    Fixture inaccessible;
    inaccessible.memory.unmap(receiver);
    try {
        (void)create_direct_draw4(inaccessible.memory, inaccessible.provider, scratch);
        throw std::runtime_error("Expected receiver memory fault");
    } catch (const MemoryFault &) {
        require(inaccessible.provider.events.empty(), "Provider called after invalid receiver");
    }

    Fixture denied;
    denied.memory.protect(direct_draw4_global, Permissions::read);
    try {
        (void)create_direct_draw4(denied.memory, denied.provider, scratch);
        throw std::runtime_error("Expected QI output permission fault");
    } catch (const MemoryFault &fault) {
        require(fault.reason() == MemoryFaultReason::permission_denied, "Wrong QI fault");
        require(denied.provider.events == std::vector<std::string>{"create", "query"},
                "Fault must not synthesize error return or Release");
    }

    Fixture changed;
    changed.memory.store<std::uint32_t>(direct_draw4_global, queried.value);
    changed.provider.mutate_restore_global = true;
    release_direct_draw4_after_dependents(changed.memory, changed.provider);
    require(changed.provider.events == std::vector<std::string>{"restore", "release-temporary"},
            "Teardown must reread global after provider call");

    Fixture refused;
    refused.memory.store<std::uint32_t>(direct_draw4_global, queried.value);
    refused.provider.throw_release = true;
    bool threw = false;
    try {
        release_direct_draw4_after_dependents(refused.memory, refused.provider);
    } catch (const std::runtime_error &) {
        threw = true;
    }
    require(threw && refused.memory.load<std::uint32_t>(direct_draw4_global) == queried.value,
            "Refused release must not clear owned state");
}

} // namespace

int main() {
    try {
        test_success_and_teardown();
        test_failure_outputs_and_zero_tests();
        test_faults_and_partial_cleanup();
        std::cout << "Authored video creation fixtures passed; no game/provider execution\n";
        return 0;
    } catch (const std::exception &error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
