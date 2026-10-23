#include "native-overrides/texture_read_diagnostics.hpp"
#include <map>
#include <stdexcept>
#include <iostream>

int main() {
    using namespace mw34::texture_diagnostics;
    unsigned checks = 0;
    auto check = [&](bool okay) { ++checks; if (!okay) throw std::runtime_error("Texture diagnostic fixture failed"); };
    const std::array<unsigned, 3> returns{0x518e16, 0x517ea7, 0x78022476};
    const std::array<unsigned, 3> slots{0x1078, 0x1038, 0x1018};
    std::map<unsigned, unsigned> memory{{0x1030,0x50010000},{0x103c,0},{0x1040,1},{0x1044,512},{0x1048,0x51382000}};
    unsigned reads = 0;
    auto read = [&](unsigned a) { ++reads; return memory.at(a); };
    auto valid = [](unsigned a,unsigned n) { return a == 0x1030 && n == 28; };
    auto f = read_frame(returns, slots, valid, read);
    check(f.found && f.site == 0x517ea7 && f.destination == 0 && f.size == 1 && f.count == 512);
    check(f.stream == 0x51382000 && f.object == 0x50010000 && reads == 5);
    reads = 0;
    check(!read_frame(returns, slots, [](unsigned,unsigned){return false;},read).found && reads == 0);
    check(!read_frame(std::span<const unsigned>(returns.data(),1), slots, valid,read).found && reads == 0);
    const std::array<unsigned, 1> overflow_slot{0xfffffff8}, underflow_slot{4}, one_site{0x517ea7};
    check(!read_frame(one_site, overflow_slot, valid,read).found && reads == 0);
    check(!read_frame(one_site, underflow_slot, valid,read).found && reads == 0);
    for (unsigned site : {0x517e2dU,0x517e5dU,0x517ea7U}) {
        const std::array<unsigned,1> r{site},s{0x1038};
        check(read_frame(r,s,valid,read).site == site);
    }
    memory[0x1074]=0x50020000;
    auto entry_valid=[](unsigned a,unsigned n){return (a==0x1074 && n==4)||(a==0x50020000 && n==40);};
    check(lookup_entry(returns,slots,entry_valid,read)==0x50020000);
    check(lookup_entry(returns,slots,[](unsigned,unsigned){return false;},read)==0);
    memory[0x1074]=0xfffffff0;
    check(lookup_entry(returns,slots,entry_valid,read)==0);
    RecentSeeks history;
    for (unsigned i=0;i<17;++i) history.push({i,i*4096,0,0,i*4096,0,true,true,false});
    check(history.count == 17);
    for (unsigned i=9;i<17;++i) check(history.entries[i%8].handle == i);
    std::cout << "Texture fault metadata fixtures: " << checks << " checks passed\n";
}
