#include "native-overrides/projection_contract.hpp"
#include <cstdio>
#include <cstdlib>

static void require(bool value, const char* message) {
    if (!value) { std::fprintf(stderr, "FAIL: %s\n", message); std::exit(1); }
}

int main() {
    using namespace mw34::projection;
    require(!overlaps(scratch, 0), "empty access");
    require(!overlaps(scratch-4, 4), "left adjacent");
    require(!overlaps(scratch+extent, 4), "right adjacent");
    require(overlaps(scratch-1, 2), "left partial overlap");
    require(overlaps(scratch+extent-1, 2), "right partial overlap");
    require(!overlaps(0xfffffff0U, 32), "high address does not wrap into scratch");
    require(overlaps(0, std::uint64_t(scratch)+1), "wide access arithmetic");

    Dirty dirty;
    require(!dirty.any(scratch, extent), "initially clean");
    dirty.prefix(3);
    for(unsigned i=0;i<extent;++i)
        require(bool(dirty.bytes[i]) == (i<64 && i%32<12), "only omitted xyz dirty");
    dirty.set(scratch+3, 2, false);
    require(dirty.any(scratch+2, 1) && !dirty.any(scratch+3, 2) && dirty.any(scratch+5, 1), "partial write exact bytes");
    dirty.set(scratch-2, 3, false);
    require(!dirty.any(scratch, 1) && dirty.any(scratch+1, 1), "left overlapping write clamped");
    dirty.set(0xfffffff0U, 32, false);
    require(dirty.any(scratch+1, 1), "high write cannot clear low address");
    dirty.set(scratch+extent-1, 8, true);
    require(dirty.any(scratch+extent-1, 1) && !dirty.any(scratch+extent, 8), "right overlap clamped");
    dirty.set(scratch, extent, false);
    dirty.prefix(1);
    dirty.prefix(0);
    require(!dirty.any(scratch, extent), "zero omitted corners for zero and one counts");
    dirty.prefix(128);
    require(dirty.any(scratch+126*32,12) && !dirty.any(scratch+127*32,32), "last original iteration clean");
    dirty.set(scratch+12,4,dirty.any(scratch+8,4));
    require(dirty.any(scratch+12,4), "callback depth copy propagates dirty RHW");
    dirty.set(scratch+8,4,false);
    require(dirty.any(scratch+12,4), "later depth write does not clear copied RHW");
    dirty.set(scratch+12,4,false);
    require(!dirty.any(scratch+8,8), "independent overwrite clears remaining RHW");

    require(operand(0) && operand(0x80000000U), "both signed zeros");
    require(operand(0x3b800000U) && operand(0x47800000U), "finite magnitude boundaries");
    require(operand(0xbb800000U) && operand(0xc7800000U), "negative magnitude boundaries");
    require(!operand(1) && !operand(0x3b7fffffU) && !operand(0x47800001U), "unsafe finite ranges rejected");
    require(!operand(0x7f800000U) && !operand(0xff800000U) && !operand(0x7fc00001U), "infinities and NaN rejected");
    require(positive(0x3b800000U) && positive(0x47800000U), "positive boundaries");
    require(!positive(0) && !positive(0x80000000U) && !positive(0xbf800000U) && !positive(0x7f800000U), "nonpositive and nonfinite depth rejected");
    std::puts("Projection contract fixture passed");
}
