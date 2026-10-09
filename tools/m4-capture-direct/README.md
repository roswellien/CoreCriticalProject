# Direct native capture transport

The canonical integration is `capture_direct_v3.hpp`, `capture_direct_v3.cpp`
and `preserve_v2.s`, built by `build_v3.ps1` into `build-r4`. Link the writer
object and preservation object with BCrypt and the normal Windows C++ runtime.
All prior source versions and failed receipts remain available as history.

```cpp
#include "capture_direct_v3.hpp"
namespace cd = mw34::capture_direct;
auto sink = cd::Writer::try_create(output_directory, cd::Options{});
if (!sink) return false;
if (!sink->try_append("row-0/phase/state.bin", data, bytes)) return false;
// Optional row/batch closure. Automatic bounded partitioning is always active.
if (!sink->try_close_batch()) return false;
const auto* receipt = sink->try_finish();
if (!receipt) return false;
```

The checked operations report failure without letting a C++ exception leave the
protected callback. Failed writers retain their first diagnostic, stay poisoned,
and refuse retries. Throwing convenience methods remain for CLI transport use;
there is no hardware preservation claim across the caller's exception handling.

Append writes one compact spool per part and remembers names, extents and system
BCrypt SHA-256 values. Part closure sorts ASCII logical names and emits exactly
the frozen `MW34CAP1` header, canonical `mw34.capture.v1` index, and contiguous
payload bytes. It rechecks spool records and rereads each finalized archive before
publication. No physical row, phase or logical-record file is emitted.

Limits remain 200,000 records, 64 MiB index, 256 MiB individual payload and 2 GiB
total payload per archive. Options may lower count, payload and index limits;
they cannot raise those limits. The conservative index budget can close a part
early. ASCII names explicitly restrict the existing reader's broader Unicode
domain. Names are unique across every part, including ASCII case aliases.

Every part and the manifest stay in one fresh private sibling directory until a
no-replacement whole-directory rename publishes the complete set. Files are
flushed before publication. This is atomic whole-set publication, without a claim
of power-loss durability. Ordinary rejected operations clean only explicitly
owned private files; changed/reparsed ancestors cause cleanup to abandon debris.
A fatal process interruption can leave a private `.partial` directory, but cannot
make that directory a published successful capture set.

`transport.json` associates every part with its external whole-file SHA-256,
index hash, physical extent and logical/payload counts. Its emission timing and
part-finalization timing use disjoint intervals. Returned receipt and driver
stdout also include final manifest/publication time in `finalize_seconds`.
The manifest's `native_executed:false` is a game-semantic disclaimer; the transport
driver itself is native code. Transport receipts do not grant game-source credit.

The driver accepts `replay INPUT OUTPUT` or the bounded `flat INPUT OUTPUT`
benchmark mode. Input is eight-byte `MW34REC1`, LE32 record count, followed by
LE32 name extent, LE64 payload extent, ASCII name and payload for each record,
with exact EOF. Replay options are `--files-per-part`, `--bytes-per-part`,
`--index-bytes-per-part`, `--close-every` and fixture-only `--fail-after`, each
followed by an unsigned number. Flat mode is limited to 10,000 records and exists
only for comparable transport benchmarks; game captures use replay/Writer.

`controls-r3` passed both O0 and O2: 108 actual rich hardware pairs, 54 refusals,
and 400,002 actual default-limit records. Each level emitted 200,001 records into
two archives containing 200,000 and one record, verified through the unchanged
strict Python reader. Rich checked boundaries preserve complete legacy ENV28
with nonzero legacy instruction evidence, CW/SW/FTW, every physical raw80
register, MXCSR, XMM6..15, ABI direction-flag equality and caller LastError.
Equality of volatile XMM0..5 is not claimed. The two earlier throwing-boundary
failures remain preserved; their checks were not relaxed.

The independent root representative benchmark compares identical reversed input
records and verifies both transports. Its measured improvement applies only to
that local workload, not to compilation or total project progress.
