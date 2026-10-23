#include "../native-overrides/service_history.hpp"
#include <iostream>
#include <deque>

int main() {
    unsigned checks = 0;
    auto check = [&](bool value) {
        ++checks;
        if (!value) throw std::runtime_error("Service history mismatch");
    };
    mw34::ServiceHistory log(7);
    std::vector<std::string> reference;
    std::deque<std::string> labels;
    for (unsigned n = 0; n < 1000; ++n) {
        const std::string value = "KERNEL32.dll!EnterCriticalSection " + std::to_string(n);
        if (reference.size() == 7) reference.erase(reference.begin());
        reference.push_back(value);
        labels.push_back(value);
        log.push_back(&labels.back());
        if (n % 3 == 0) { log.back() += "(annotation)"; reference.back() += "(annotation)"; }
        check(log.size() == reference.size());
        check(log.back().text() == reference.back());
        for (std::size_t i = 0; i < reference.size(); ++i) check(log[i] == reference[i]);
        check(std::vector<std::string>(log) == reference);
    }
    bool rejected = false;
    try { mw34::ServiceHistory invalid(0); } catch (const std::invalid_argument&) { rejected = true; }
    check(rejected);
    log.push_back(std::string("guest thread summary"));
    log.back() += "(exit 0)";
    check(log[log.size() - 1] == "guest thread summary(exit 0)");
    for (unsigned n = 0; n < 8; ++n) log.push_back(&labels.front());
    check(log[0] == labels.front());
    std::cout << "service history checks=" << checks << " failures=0\n";
}
