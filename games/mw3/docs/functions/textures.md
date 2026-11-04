# Textures

How the game loads a texture by name from one of its texture banks. A bank is
an archive file holding a table of named texture records and a set of shared
palettes; the bank code opens it on first use, finds the record, seeks to the
texture and reads it into a new texture descriptor.

Profile `mw3-us-1-2-retail`, image SHA-256
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`. Studied
2026-11-04 in Ghidra 12.1.3 with the default analysis. Addresses are virtual
addresses at image base `0x400000`; RVAs are the address minus `0x400000`. To
repeat the work, import that `Mech3.exe` into Ghidra and go to each address; the
[README](README.md) has the details and the section format. Every import slot
named here is checked against
[`../imports-mw3-us-1-2-retail.csv`](../imports-mw3-us-1-2-retail.csv).

Offsets on a texture descriptor (the 56-byte block `00517F80` allocates) used
below: `+0` the pixel count, `+9` a flag byte, `+0x0E` the palette entry count,
`+0x10` the pixel buffer, `+0x14` an optional second block, `+0x18` the palette.

## sub_00517DF0

**Name and confidence:** `Texture_ReadData`, confirmed.

**Kind:** the game's own code.

**Extent:** `00517DF0` to `00517F60`, 369 bytes.

**Callers:** one function, `00517F80`, from `00517FB7` (return `00517FBC`).
`00517F80` builds a texture from the bank file's current position: it allocates
a zeroed 56-byte descriptor, reads the texture's 16-byte header and copies its
fields into it through `00517D80` (returning 0 only if the file or descriptor
is null; `00517D80` doesn't check its own `fread`, so a short header read goes
unnoticed), allocates the pixel buffer at `+0x10`, then calls this function
with a wanted pixel size of 0, sets flag `0x20` at `+9` and returns the
descriptor. It ignores this function's result, so the texture is returned
even after a short read. Its own one caller is [`00518DB0`](#sub_00518db0).

**What it does,** in order. It takes the open file in ECX, the descriptor in
EDX (kept in ESI throughout) and one stack argument, the wanted pixel size in
bytes, where 0 means the texture's own.

1. Gets the texture's pixel size from `00517C20`: 2 if flag `0x01` at `+9` is
   set, otherwise 1. A wanted size of 0 becomes that size.
2. If the wanted size differs from the texture's, it returns -1 when the
   wanted size is smaller and 0 when it is larger, reading nothing.
   `00517F80` always passes 0, so it never takes this branch.
3. Reads the pixel data into the buffer at `+0x10` with `fread` (slot RVA
   `0x1BB594`), called at `00517E27`, return `00517E2D`. The size comes from
   `00517F70`: the pixel count at `+0` if the texture has a palette, otherwise
   that count times the pixel size. A short read returns -1.
4. If flag `0x08` at `+9` is set, allocates a second block of `+0` bytes with
   `malloc` (slot RVA `0x1BB664`), stores it at `+0x14` and reads into it with
   `fread`, called at `00517E57`, return `00517E5D`. It then sets flag `0x40`
   at `+9`; a short read returns -1.
5. If flag `0x10` at `+9` is clear and the palette count at `+0x0E` is not
   zero, allocates the count times the pixel size with `malloc`, stores it at
   `+0x18` and reads the palette into it with `fread`, called at `00517EA1`,
   return `00517EA7`. It then sets flag `0x80` at `+9`; a short read returns
   -1.
6. A 1-byte texture, or one with flag `0x10`, returns 0 here. (There is also
   an exit for a size other than 1 or 2, which can't happen: `00517C20` only
   returns 1 or 2.)
7. For a 2-byte texture, it calls `00579260`, which copies the three globals at
   `00802720`, `00802724` and `00802728`. If the second is 5, it rewrites each
   16-bit color from 5-6-5 to 5-5-5 (red and green move down a bit, losing
   green's lowest bit; blue stays): the palette's entries if there is a
   palette, otherwise the pixel count's worth of pixels.
8. If there is a palette, whatever the format, it passes it to `00519740` and
   stores the result back at `+0x18`. `00519740` returns the palette
   unchanged unless the global at `00638514` is non-zero; then it enlarges it
   and fills 32 tables of 512 bytes after it for each unit of that global.
9. Returns 0.

Neither `malloc` result is checked, and neither is the pixel buffer
`00517F80` allocated, so a failed allocation reaches `fread` with a null
buffer.

**Reads and writes:** the file through `fread`; the descriptor's pixel count,
flags, palette count and the three buffers named above; the globals at
`00802720` to `00802728` (through `00579260`) and `00638514` (through
`00519740`); the import slots for `fread` and `malloc`.

**How the host reaches it:** `tools/m4-crt-heap-carry/host/texture_read_diagnostics.hpp`
(`read_frame`), used only when a fault is being logged, looks on the stack for
one of the three `fread` returns `00517E2D`, `00517E5D` and `00517EA7`. Above
that return it reads the four `fread` arguments (buffer, element size, count,
file); below it, the descriptor `fread` saved from ESI, which this function
holds there at all three calls. So a fault inside one of these reads reports
which read failed, into what buffer and for which texture. A copy of the
header is in `tools/remaster-launcher/native-overrides/`, and
`docs/archive/op1m1-texture-crash-diagnostics-2026-10-23.md` records the same
stack layout. Context only, not proof.

**Why this name:** the game-code rule. Every step and branch is described
above, and its one caller uses it the same way: to fill a just-allocated
texture descriptor from the bank file. "Texture" is the descriptor it fills;
"ReadData" says it reads the texture's data (pixels, extra block, palette)
rather than its header, which `00517D80` reads first.

**Still unknown:** what flags `0x08` and `0x10` mean and what the second block
holds; what the globals at `00802720` to `00802728` are (the value 5 likely
names a 5-5-5 display mode, not proven); what the global at `00638514`
controls. None of these bears on the name.

## sub_00518DB0

**Name and confidence:** `TextureBank_LoadByName`, confirmed.

**Kind:** the game's own code.

**Extent:** `00518DB0` to `00518E41`, 146 bytes.

**Callers:** one function, `00518D60`, from `00518D82`. `00518D60` walks a
list of banks (a circular linked list at its object's `+4`, each node holding
a bank at `+8`) and calls this function on each with the same name until one
returns a texture, or returns 0. `00518D60` is itself called twice from
`00518EE0`, which picks one of two bank lists from the two-entry table at
`005ECC28` by the global at `0063851C`. If that list finds nothing, it switches
the global between 0 and 1 and tries the other list; the switch stays in
effect afterwards. `00518EE0` has 4 callers, among them
`005176B0` and `00519E50`.

**What it does,** in order. It is called on a bank object (ECX) with one stack
argument, the texture's name.

1. Calls `005187C0` to make sure the bank is open. That first fails if the
   global at `005ECC20` is 0. If the flag at `+0xA8` is set, it then calls
   `00518A30`, which clears that flag, writes candidate file names for the
   bank with `sprintf` (slot RVA `0x1BB658`), checks each through
   `005187A0`, and sets the flag at `+0xAA` if none is found. It then
   succeeds if the bank's file at `+0x80` is already open, and fails if the
   flag at `+0xAA` is set. Otherwise it opens the archive file and, if the
   record table isn't loaded yet, reads its 24-byte header into
   `+0x84` (the record count is at `+0x90` and the palette count at `+0x8C`;
   the word at `+0x88` must be 1), its table of 40-byte records into a buffer
   at `+0x9C`, and the bank's palettes. It adds those palettes to a shared
   table whose pointer is in the global at `00638510`, enlarging that table,
   and saves the bank's first index in it at `+0xA0`. If this fails, this
   function returns 0.
2. Returns 0 if the record table pointer at `+0x9C` is null.
3. Walks the records in order, up to the record count at `+0x90`, comparing
   each record's name (its first 32 bytes) with the argument through
   `_stricmp` (slot RVA `0x1BB580`), so case doesn't matter. If no record
   matches, it returns 0. The step to the next record (`00518DE7` to
   `00518DEA`) also ends the walk with 0 if the record pointer wraps to zero,
   which a real table never reaches.
4. On a match, calls `fseek` (slot RVA `0x1BB59C`) on the bank's file with the
   record's offset at `+0x20`, from the start of the file; the call is at
   `00518E02`, return `00518E08`. The result isn't checked.
5. Calls `00517F80` from `00518E11` (return `00518E16`), which builds the
   texture from that position (see [`sub_00517DF0`](#sub_00517df0)).
6. If the record's palette index at `+0x24` is not -1, takes the palette at
   index `+0xA0` plus that value in the shared table and stores it at `+0x18`
   in the new texture, replacing any palette read with the texture. It doesn't
   check that `00517F80` returned a texture first.
7. Returns the texture.

**Reads and writes:** the bank object's file, header fields, record table and
first palette index; the matched record's name, offset and palette index; the
shared palette table through the global at `00638510`; the new texture's
`+0x18`; the import slots for `_stricmp` and `fseek`.

**How the host reaches it:** `tools/m4-crt-heap-carry/host/texture_read_diagnostics.hpp`
(`lookup_entry`), used only when a fault is being logged, looks on the stack
for the return `00518E16`. At the call before it, ESI holds the matched
40-byte record, and `00517F80`'s first instruction pushes ESI, so the
diagnostics read the record's address from just below that return and report
the texture's name and offset. `tools/m4-crt-heap-carry/host/large_texture_seek.hpp`
matches the `fseek` return `00518E08` to widen the seek for replacement banks
larger than 2 GiB, whose record offsets don't fit the signed offset `fseek`
takes; its comment names this function `sub_00518db0`. Near-copies of both
headers are in `tools/remaster-launcher/native-overrides/`, and
`docs/archive/large-texture-archive-repair-2026-10-22.md` records the seek
problem. Context only, not proof.

**Why this name:** the game-code rule. Every step and branch is described
above, and its one caller uses it as a by-name lookup across a list of banks.
"TextureBank" is the object it runs on; "LoadByName" says it finds a texture
by name and loads it. The host's own comment calls it "TextureBank::load".

**Still unknown:** what the global at `005ECC20` and the flag at `+0xA8` mean,
which file `005187C0` opens (it gets the file from `005763B0`, passing the
address `005EB908`), and what the two bank lists at `005ECC28` hold. None of
these bears on the name.
