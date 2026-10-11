#include "mfc/app_receiver_state.hpp"

#include <limits>
#include <stdexcept>

namespace mw34::mfc {

AppReceiverState::AppReceiverState(ReceiverProviderIdentity provider) {
    if (provider.image_sha256 != staged_mfc42_sha256 ||
        provider.evidence != ProviderEvidence::controlled_fixture) {
        throw std::invalid_argument(
            "MFC receiver model requires exact controlled fixture identity");
    }
}

void AppReceiverState::initialize_module(ModuleStateId module) {
    if (module.address.value == 0 || !modules_.try_emplace(module.address.value).second) {
        throw std::invalid_argument("MFC module must be nonnull and owned once");
    }
}

void AppReceiverState::initialize_thread(ThreadSlotId thread) {
    if (thread.address.value == 0 || !threads_.try_emplace(thread.address.value).second) {
        throw std::invalid_argument("MFC thread slot must be nonnull and owned once");
    }
}

void AppReceiverState::set_fallback(std::optional<ModuleStateId> module) {
    if (module) {
        (void)modules_.at(module->address.value);
    }
    fallback_ = module;
}

std::optional<ModuleStateId> AppReceiverState::select_module(ThreadSlotId thread,
                                                             std::optional<ModuleStateId> module) {
    auto &slot = threads_.at(thread.address.value);
    if (module) {
        (void)modules_.at(module->address.value);
    }
    const auto previous = slot.current;
    slot.current = module;
    return previous;
}

std::optional<ModuleStateId> AppReceiverState::current_module(ThreadSlotId thread) const {
    const auto found = threads_.find(thread.address.value);
    if (found == threads_.end()) {
        return std::nullopt;
    }
    return found->second.current ? found->second.current : fallback_;
}

ConstructionTicket AppReceiverState::begin_construction(AppReceiverId receiver,
                                                        ThreadSlotId thread) {
    const auto module = current_module(thread);
    if (!module || receiver.address.value == 0) {
        throw std::invalid_argument(
            "Construction requires current owned state and nonnull receiver");
    }
    for (const auto &[ticket, app] : applications_) {
        (void)ticket;
        if (app.receiver == receiver) {
            throw std::invalid_argument("Receiver already has an active lifetime");
        }
    }
    if (next_ticket_ == std::numeric_limits<std::uint64_t>::max()) {
        throw std::overflow_error("Construction ticket space exhausted");
    }
    const auto ticket = next_ticket_++;
    applications_.emplace(ticket, Application{receiver, thread, *module, false});
    return ConstructionTicket{this, ticket};
}

void AppReceiverState::validate_ticket(ConstructionTicket ticket) const {
    if (ticket.owner_ != this) {
        throw std::invalid_argument("Construction ticket belongs to another adapter");
    }
}

void AppReceiverState::complete_construction(ConstructionTicket ticket) {
    validate_ticket(ticket);
    auto &app = applications_.at(ticket.value_);
    if (app.complete || current_module(app.thread) != app.module) {
        throw std::logic_error("Completion requires pending construction in its saved module");
    }
    // Source publication order: thread-object +4, then saved module-state +4.
    // Both owners were initialized explicitly; no allocation/provider code runs here.
    threads_.at(app.thread.address.value).receiver = app.receiver;
    modules_.at(app.module.address.value).receiver = app.receiver;
    app.complete = true;
}

void AppReceiverState::invalidate(std::uint64_t ticket) {
    const auto receiver = applications_.at(ticket).receiver;
    for (auto &[address, module] : modules_) {
        (void)address;
        if (module.receiver == receiver) {
            module.receiver.reset();
        }
    }
    for (auto &[address, thread] : threads_) {
        (void)address;
        if (thread.receiver == receiver) {
            thread.receiver.reset();
        }
    }
    applications_.erase(ticket);
}

void AppReceiverState::fail_construction(ConstructionTicket ticket) {
    validate_ticket(ticket);
    if (applications_.at(ticket.value_).complete) {
        throw std::logic_error("Completed receiver requires destruction, not construction failure");
    }
    invalidate(ticket.value_);
}

void AppReceiverState::destroy_receiver(AppReceiverId receiver) {
    for (const auto &[ticket, app] : applications_) {
        if (app.receiver == receiver) {
            invalidate(ticket);
            return;
        }
    }
    throw std::invalid_argument("Receiver has no owned lifetime");
}

void AppReceiverState::teardown_thread(ThreadSlotId thread) {
    (void)threads_.at(thread.address.value);
    for (auto it = applications_.begin(); it != applications_.end();) {
        const auto current = it++;
        if (current->second.thread == thread) {
            invalidate(current->first);
        }
    }
    threads_.erase(thread.address.value);
}

void AppReceiverState::teardown_module(ModuleStateId module) {
    (void)modules_.at(module.address.value);
    for (auto it = applications_.begin(); it != applications_.end();) {
        const auto current = it++;
        if (current->second.module == module) {
            invalidate(current->first);
        }
    }
    for (auto &[address, thread] : threads_) {
        (void)address;
        if (thread.current == module) {
            thread.current.reset();
        }
    }
    if (fallback_ == module) {
        fallback_.reset();
    }
    modules_.erase(module.address.value);
}

std::optional<AppReceiverId> AppReceiverState::lookup_receiver(ThreadSlotId thread) const {
    const auto module = current_module(thread);
    return module ? module_receiver(*module) : std::nullopt;
}

std::optional<AppReceiverId> AppReceiverState::module_receiver(ModuleStateId module) const {
    return modules_.at(module.address.value).receiver;
}

std::optional<AppReceiverId> AppReceiverState::thread_receiver(ThreadSlotId thread) const {
    return threads_.at(thread.address.value).receiver;
}

ModuleStateId AppReceiverState::saved_module(ConstructionTicket ticket) const {
    validate_ticket(ticket);
    return applications_.at(ticket.value_).module;
}

void AppReceiverState::require_live_dispatch() const {
    throw std::logic_error(
        "Live MFC dispatch blocked: provider and callback lifetime not admitted");
}

} // namespace mw34::mfc
