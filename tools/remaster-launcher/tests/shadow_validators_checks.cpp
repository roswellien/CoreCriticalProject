#include "../native-overrides/shadow_validators.hpp"
#include <cstdio>
#include <memory>
#include <stdexcept>

unsigned checks{};
void require(bool value) {
    ++checks;
    if (!value)
        throw std::runtime_error("Shadow validator ownership check failed");
}
template <class F> void rejects(F fn) {
    bool rejected = false;
    try {
        fn();
    } catch (const std::out_of_range &) {
        rejected = true;
    }
    require(rejected);
}
int main() {
    using Store = mw34::submission::ShadowValidators;
    Store store;
    require(!store.has(Store::none) && !store.get(Store::none));
    require(store.capture({}) == Store::none && store.size() == 0);
    auto proof = std::make_shared<unsigned>(0);
    std::weak_ptr<unsigned> lifetime = proof;
    unsigned calls{};
    const auto first = store.capture([proof, &calls] { ++calls; return *proof == 0; });
    require(first == 0 && calls == 0 && store.has(first));
    for (unsigned i = 0; i < 10000; ++i) {
        const auto index = store.capture([i] { return i % 2 == 0; });
        require(index == i + 1);
    }
    require(calls == 0 && store.get(first)() && calls == 1);
    *proof = 1;
    require(!store.get(first)() && calls == 2);
    Store copied = store;
    Store moved = std::move(copied);
    for (unsigned i = 0; i < 10000; ++i)
        require(moved.get(i + 1)() == (i % 2 == 0));
    auto retained = moved.get(first);
    store = {};
    moved = {};
    proof.reset();
    require(!lifetime.expired() && !retained() && calls == 3);
    retained = {};
    require(lifetime.expired());
    Store invalid;
    rejects([&] { invalid.has(0); });
    rejects([&] { invalid.get(1); });
    require(!invalid.has(Store::none));
    std::printf("%u shadow validator ownership checks passed\n", checks);
}
