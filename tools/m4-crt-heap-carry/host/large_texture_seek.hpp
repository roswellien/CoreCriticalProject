#pragma once

#include <algorithm>
#include <cstdint>
#include <span>

namespace mw34::texture_banks {

// The admitted MW3 1.2 texture-table record stores an unsigned 32-bit offset,
// but sub_00518db0 passes it through the old CRT's signed-long fseek. Preserve
// the CRT's buffering/locking and widen only this known archive access at its
// final host I/O boundary. Ordinary negative seeks retain Win32 semantics.
// The imported CRT has more than one seek path (buffer state changes it).
// Its internal return 78012115 is not a required caller of SetFilePointer.
// The original MW3 table-loader return, replacement handle and absolute
// high-bit offset identify this operation regardless of that CRT path.
inline bool unsigned_archive_seek(bool replacement_bank, std::uint32_t offset,
                                  std::uint32_t high_pointer, std::uint32_t origin,
                                  std::span<const unsigned> returns) {
    return replacement_bank && (offset & 0x80000000U) && !high_pointer && origin == 0 &&
           std::find(returns.begin(), returns.end(), 0x00518e08U) != returns.end();
}

} // namespace mw34::texture_banks
