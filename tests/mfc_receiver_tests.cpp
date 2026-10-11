#include "mfc/app_receiver_state.hpp"

#include <exception>
#include <iostream>
#include <stdexcept>

namespace {

using namespace mw34::mfc;
constexpr ModuleStateId first{{0x1000}}, second{{0x2000}};
constexpr ThreadSlotId thread{{0x3000}}, other_thread{{0x4000}};
constexpr AppReceiverId receiver{{0x608c88}}, replacement{{0x7000}};
constexpr ReceiverProviderIdentity fixture{staged_mfc42_sha256,
                                           ProviderEvidence::controlled_fixture};

void require(bool condition, const char *message) {
    if (!condition) {
        throw std::runtime_error(message);
    }
}

template <typename Exception, typename Action> void expect_exception(Action action) {
    try {
        action();
    } catch (const Exception &) {
        return;
    }
    throw std::runtime_error("Expected transition refusal");
}

void initialize(AppReceiverState &state) {
    state.initialize_module(first);
    state.initialize_module(second);
    state.initialize_thread(thread);
    state.initialize_thread(other_thread);
}

ConstructionTicket publish(AppReceiverState &state, AppReceiverId app, ThreadSlotId owner) {
    const auto ticket = state.begin_construction(app, owner);
    state.complete_construction(ticket);
    return ticket;
}

void test_initialization_and_identity() {
    expect_exception<std::invalid_argument>(
        [] { AppReceiverState state{{"unidentified", ProviderEvidence::controlled_fixture}}; });
    expect_exception<std::invalid_argument>(
        [] { AppReceiverState state{{staged_mfc42_sha256, ProviderEvidence::unobserved}}; });
    AppReceiverState state{fixture};
    require(!state.lookup_receiver(thread), "Uninitialized thread must not resolve a receiver");
    initialize(state);
    require(!state.current_module(thread) && !state.lookup_receiver(thread),
            "Initialization must not seed module selection or receiver");
    require(!state.module_receiver(first) && !state.thread_receiver(thread),
            "Owned slots start without a receiver");
    expect_exception<std::invalid_argument>([&] { state.initialize_module(first); });
    expect_exception<std::invalid_argument>([&] { state.initialize_thread(thread); });
    expect_exception<std::invalid_argument>([&] { state.initialize_module({{0}}); });
    expect_exception<std::invalid_argument>([&] { state.initialize_thread({{0}}); });
    expect_exception<std::invalid_argument>(
        [&] { (void)state.begin_construction(receiver, thread); });
    expect_exception<std::logic_error>([&] { state.require_live_dispatch(); });
}

void test_publication_and_callback_lookup() {
    AppReceiverState state{fixture};
    initialize(state);
    (void)state.select_module(thread, first);
    const auto ticket = state.begin_construction(receiver, thread);
    require(state.saved_module(ticket) == first, "Construction must save the selected module");
    require(!state.lookup_receiver(thread) && !state.thread_receiver(thread),
            "Pending construction must not publish");
    state.complete_construction(ticket);
    require(state.module_receiver(first) == receiver && state.thread_receiver(thread) == receiver,
            "Complete construction must publish both +4 associations");
    require(state.lookup_receiver(thread) == receiver,
            "Callback lookup must read current module +4");
    require(!state.lookup_receiver(other_thread), "Thread selection must remain independent");
    (void)state.select_module(other_thread, first);
    require(state.lookup_receiver(other_thread) == receiver && !state.thread_receiver(other_thread),
            "Callback gate uses shared module receiver, not an invented thread-slot check");
    expect_exception<std::logic_error>([&] { state.complete_construction(ticket); });
    expect_exception<std::logic_error>([&] { state.fail_construction(ticket); });
    expect_exception<std::invalid_argument>(
        [&] { (void)state.begin_construction(receiver, thread); });
    expect_exception<std::logic_error>([&] { state.require_live_dispatch(); });
}

void test_fallback_switch_restore_and_null() {
    AppReceiverState state{fixture};
    initialize(state);
    state.set_fallback(first);
    require(!state.current_module({{0x9000}}), "Fallback must not initialize an unknown thread");
    (void)publish(state, receiver, thread);
    require(state.lookup_receiver(thread) == receiver, "Controlled fallback must supply module +4");
    const auto previous = state.select_module(thread, second);
    require(!previous && !state.lookup_receiver(thread), "Explicit module overrides fallback");
    (void)publish(state, replacement, thread);
    (void)state.select_module(thread, previous);
    require(state.lookup_receiver(thread) == receiver &&
                state.thread_receiver(thread) == replacement,
            "Restore must select module +4 despite the newer thread +4 publication");
    state.set_fallback(std::nullopt);
    require(!state.lookup_receiver(thread), "Null current and fallback must refuse lookup");
    (void)state.select_module(thread, second);
    require(state.lookup_receiver(thread) == replacement, "Explicit module survives null fallback");
    expect_exception<std::out_of_range>([&] { state.set_fallback(ModuleStateId{{0x9000}}); });
    expect_exception<std::out_of_range>(
        [&] { (void)state.select_module(thread, ModuleStateId{{0x9000}}); });
    require(state.lookup_receiver(thread) == replacement, "Rejected selection must preserve state");
}

void test_failure_and_ticket_ownership() {
    AppReceiverState state{fixture};
    initialize(state);
    (void)state.select_module(thread, first);
    expect_exception<std::invalid_argument>([&] { (void)state.begin_construction({{0}}, thread); });
    const auto failed = state.begin_construction(receiver, thread);
    (void)state.select_module(thread, second);
    expect_exception<std::logic_error>([&] { state.complete_construction(failed); });
    require(!state.lookup_receiver(thread) && !state.module_receiver(first),
            "Changed module must not publish a pending receiver");
    state.fail_construction(failed);
    const auto reused = state.begin_construction(receiver, thread);
    expect_exception<std::out_of_range>([&] { state.complete_construction(failed); });
    AppReceiverState foreign{fixture};
    initialize(foreign);
    (void)foreign.select_module(thread, first);
    const auto foreign_ticket = foreign.begin_construction(replacement, thread);
    expect_exception<std::invalid_argument>([&] { foreign.complete_construction(reused); });
    expect_exception<std::invalid_argument>([&] { foreign.fail_construction(reused); });
    expect_exception<std::invalid_argument>([&] { (void)foreign.saved_module(reused); });
    foreign.fail_construction(foreign_ticket);
    state.complete_construction(reused);
    require(state.lookup_receiver(thread) == receiver, "Address reuse requires a fresh transition");
    const auto pending = state.begin_construction(replacement, thread);
    state.fail_construction(pending);
    require(state.lookup_receiver(thread) == receiver,
            "Failed replacement must preserve publication");
}

void test_replacement_and_destruction() {
    AppReceiverState state{fixture};
    initialize(state);
    (void)state.select_module(thread, first);
    const auto old = publish(state, receiver, thread);
    (void)state.select_module(other_thread, first);
    (void)publish(state, replacement, other_thread);
    require(state.lookup_receiver(thread) == replacement &&
                state.module_receiver(first) == replacement,
            "Later module publication replaces callback lookup");
    state.destroy_receiver(receiver);
    require(!state.thread_receiver(thread) && state.lookup_receiver(thread) == replacement,
            "Old destruction must clear only associations still naming the old receiver");
    expect_exception<std::out_of_range>([&] { state.complete_construction(old); });
    state.destroy_receiver(replacement);
    require(!state.lookup_receiver(thread) && !state.thread_receiver(other_thread),
            "Destruction must invalidate all matching associations");
}

void test_owner_teardown() {
    AppReceiverState state{fixture};
    initialize(state);
    state.set_fallback(first);
    const auto complete = publish(state, receiver, thread);
    const auto pending = state.begin_construction(replacement, thread);
    state.teardown_thread(thread);
    require(!state.lookup_receiver(thread) && !state.lookup_receiver(other_thread),
            "Thread teardown must invalidate shared module receiver");
    expect_exception<std::out_of_range>([&] { state.complete_construction(pending); });
    state.initialize_thread(thread);
    expect_exception<std::out_of_range>([&] { state.complete_construction(complete); });
    (void)publish(state, receiver, thread);
    (void)state.select_module(other_thread, first);
    const auto module_pending = state.begin_construction(replacement, other_thread);
    state.teardown_module(first);
    require(!state.current_module(thread) && !state.current_module(other_thread) &&
                !state.thread_receiver(thread) && !state.lookup_receiver(other_thread),
            "Module teardown must invalidate fallback, selections and receiver associations");
    state.initialize_module(first);
    expect_exception<std::out_of_range>([&] { state.complete_construction(module_pending); });
    state.set_fallback(first);
    require(!state.lookup_receiver(thread), "Reinitialized module must not revive old publication");
    (void)publish(state, receiver, thread);
    (void)state.select_module(other_thread, second);
    (void)publish(state, replacement, other_thread);
    state.teardown_module(first);
    require(state.lookup_receiver(other_thread) == replacement,
            "Teardown must preserve unrelated owner lifetimes");
}

} // namespace

int main() {
    try {
        test_initialization_and_identity();
        test_publication_and_callback_lookup();
        test_fallback_switch_restore_and_null();
        test_failure_and_ticket_ownership();
        test_replacement_and_destruction();
        test_owner_teardown();
        std::cout << "6 MFC receiver lifecycle scenarios passed\n";
        return 0;
    } catch (const std::exception &error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
