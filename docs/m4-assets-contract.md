# M4 read-only asset format prerequisite

`tools/m4-assets` supplies an owning host byte store, a checked reader-archive
directory parser and a lossless binary ZRD token parser. These are prerequisites
for the reached retail frontend's asset services. They do not establish full M4
startup or a working native menu. The public sources contain authored fixtures
and format/control-flow rules; game data and recovery dumps stay in ignored
`reports/m4-assets`.

The exact admitted executable has SHA256
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`.
Its startup calls `0x557320` to register an archive. The reader constructor/open
path is `0x5764E0`/`0x576520`; `0x5767B0` reads the directory. The final eight
bytes are little-endian **version 1 then record count**. Each directory record
is `0x94` bytes. The index starts at file size minus eight minus count times
`0x94`; arithmetic appears at `0x57683E..0x57684A`. Record fields are payload
offset at `+0`, payload byte count at `+4`, a 64-byte name at `+8`, an opaque
word at `+0x48`, and 72 remaining opaque metadata bytes. The name lookup calls
MSVCRT `_stricmp` at `0x576A9E`, scans in index order and returns the first match.
The public interface supports ASCII folding and explicitly rejects non-ASCII
lookup semantics until a provider locale contract is available. It preserves
the opaque fields without assigning compression or path semantics.

`0x576AE0` seeks the original archive HANDLE to the selected entry's `+0`
offset, optionally returns its `+4` byte count, and returns that same HANDLE.
`0x5572C0` searches registered readers in order. Neither routine creates a
bounded entry stream. The host parser deliberately limits a payload view to the
directory's declared extent and rejects payloads crossing into the directory.
It does not reconstruct the original reader object, shared HANDLE cursor,
reader registry, provider file service or guest heap layout.

`0x556740` uses the registered-archive lookup and calls binary reader
`0x557180`; its external-file branch instead invokes the textual parser
`0x5563D0`, which this component does not implement. The binary reader reads a
32-bit type, checks `type - 1 <= 3` at `0x5571A4..0x5571A8`, and dispatches
through four exact targets in the table at `0x5572A8`:

| Type | Target | Wire value after type |
| --- | --- | --- |
| 1 | `0x55722C` | raw 32-bit signed integer word |
| 2 | `0x55724A` | raw 32-bit floating-point bits |
| 3 | `0x557268` -> `0x576460` | 32-bit length followed by exactly that many bytes |
| 4 | `0x5571B5` | 32-bit count followed by `count - 1` recursively encoded tokens |

The list count includes a synthetic metadata token that the original creates
in memory at slot zero (`0x5571E5..0x5571F3`); it is absent from the wire. The
string reader appends a zero byte in allocated memory (`0x57649B..0x5764AC`);
the terminator is absent from the wire. Strings retain embedded NUL bytes and
all numeric words retain their exact bits, including NaN payloads. There is no
integer-to-host-float conversion; the original accessor `0x556A60` uses x87
conversion, which requires its own ABI/rounding proof.

`Document::find_label` matches `0x556930` on valid lists: visit children in
order, recurse into a child list before examining later siblings, compare a
string case-sensitively until its first NUL, and return its following sibling.
The original returns an out-of-list address for a matching terminal label at
`0x5569C6`. The bounded host interface rejects that malformed case explicitly.
It does not supply missing-property defaults. The parser requires one complete
document with no trailing bytes, limits source size, directory entries, nodes,
depth and individual string size, and rejects unknown versions/token types,
negative counts/lengths and truncated/extending fields. These malformed-input
controls are host safety policy, not a claim of original error equivalence.

Every `ByteView` retains shared ownership of a private immutable byte copy,
its computed SHA256/source label and an exact source offset/count. Nodes retain
absolute source offsets and end offsets; strings expose read-only spans while
their document or another source owner remains alive. A returned raw span
must not outlive all owners. Nodes are addressed by checked host indices.
No host pointer or span is a `GuestAddress`, Windows HANDLE, or guest object.
Future service integration must define reader lifetimes/cursor operations,
opaque-handle ownership and explicit copies to the runtime's owned guest arena.

The conditional retail path is app constructor `0x47F7A0` -> state `0x608F00`
with table `0x5C5030` -> state setup `0x486990` -> composite constructor
`0x486260` -> `0x59F010` requesting its binary section. `0x59F050` resolves the
section with `0x5569E0` and passes it to `0x59F080`. The composite only binds
buttons if that reader returns true. `0x59F8B0` -> `0x59F810` then resolves
the button collection and named button and dispatches original widget slots
`+0x84`/`+0x88`. Actual table targets for all seven reached buttons are
`0x48E6B0` and `0x42A250`. Those functions call x87 conversion, image/font/
primitive loaders, inherited widget methods and dynamic callbacks. This
component does not create/render widgets, initialize DirectDraw/DirectInput/
DirectSound, select a loaded provider, execute original code, or claim these
callbacks succeeded. Their recovery and runtime proofs remain required.

`build_assets.ps1` requires fresh ordinary private report/build directories,
preserves literal source copies and binds compiler/tools/artifacts/commands.
`assets_tests.cpp` exercises authored valid/malformed structures, bit retention,
lookup order and lifetime/provenance. `check_assets.py` compares every directory
record and complete token stream from selected installed payloads against an
independently written read-only Python wire model, records raw streams and
checks intended command failures. This is data-format agreement, not an
original parser execution oracle. Sequential private ordinary directories are
the supported build/report scope; concurrent writers/reparse points and atomic
publication are outside it.
