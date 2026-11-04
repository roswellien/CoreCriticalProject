# Containers

Small helpers from the C++ standard library that ships with Visual C++ 6, as
the game's vectors and lists use them. Each body is generated from a template,
so one body may serve every container of 4-byte elements (pointers or
integers) the game declares.

Profile `mw3-us-1-2-retail`, image SHA-256
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`. Studied
2026-11-04 in Ghidra 12.1.3 with the default analysis. Addresses are virtual
addresses at image base `0x400000`; RVAs are the address minus `0x400000`. To
repeat the work, import that `Mech3.exe` into Ghidra and go to each address; the
[README](README.md) has the details and the section format.

The library's `vector` (in the `<vector>` header) is 16 bytes: an empty
allocator object at `+0` (padded to 4 bytes), then three pointers: `+4` the
first element, `+8` one past the last element, `+0xC` one past the end of the
buffer. A null first pointer means no buffer. Its `list` (in `<list>`) keeps a
pointer to a head node and a count; each node is 12 bytes: next at `+0`,
previous at `+4`, value at `+8`.

Most of the game's own functions take their first two plain arguments in ECX
and EDX (the "fastcall" convention), and member functions take the object in
ECX. The library templates are compiled the same way, which is why
`004D5110` below takes its arguments in registers.

## sub_0040BAF0

**Name and confidence:** `Stub_ReturnTwoArgs`, confirmed.

**Kind:** a merged body that stands for several functions.

**Extent:** `0040BAF0` to `0040BAF2`, 3 bytes.

**Callers:** Ghidra lists 66 functions that call it, with 73 call sites in
all, two of them in code it hasn't marked as a function (`005891A0` and
`004A82B8`), and 492 data references, nearly all of them slots in tables of virtual
functions from `005BBCDC` onward (for example `005BBCDC`, `005BBCE8` and
`005BBD6C`). Among the calls, [`004BF910`](objects.md#sub_004bf910) calls it at
`004BFA9C` with a vector in ECX and that vector's first and last pointers as
two stack arguments, after copying the elements to a bigger buffer and before
freeing the old one.

**What it does:** returns at once and removes 8 bytes of stack arguments. Its
only instruction is a return with an 8-byte pop. There are no branches, reads
or writes.

**Reads and writes:** none.

**How the host reaches it:** `tools/m4-crt-heap-carry/host/composition.cpp`
routes calls to it to the heap stage (`heap_stage.hpp`), which lists it among
the helpers it runs for the initializer roots 14 and 15. Context only, not
proof.

**Why this name:** the merged-body rule in the [README](README.md): its whole
behaviour is one instruction, so it is fully described. At `004BFA9C` it
stands where the library's `vector` calls `_Destroy(first, last)`, which does
nothing for pointer elements and so compiles to an empty function with two
arguments. The many virtual-function slots that point at it are other empty
functions with two arguments that the linker folded into the same body. No
single official name fits them all, so it gets an `Area_Action` name that says
what it does, in the style of [`Stub_Return`](startup.md#sub_005ac5c0).

**Still unknown:** which empty functions, other than `vector::_Destroy`, were
merged into it.

## sub_00475BF0

**Name and confidence:** `std_vector__Ucopy`, confirmed.

**Kind:** statically linked Microsoft library code: the `vector` member
`_Ucopy` from Visual C++ 6's `<vector>`, for 4-byte elements.

**Extent:** `00475BF0` to `00475C1D`, 46 bytes.

**Callers:** Ghidra lists 41 functions that call it, and 143 call sites in
all, six of them in code it hasn't marked as a function (for example
`00589189` and `004A82A9`); other callers include `004025B0` and `0040AA30`.
[`004BF910`](objects.md#sub_004bf910) calls it four times, each with its
vector in ECX: at `004BFA66` and `004BFA8D` to copy the elements before and
after the insert point into a new, bigger buffer, at `004BFADD` over an empty
range, and at `004BFB25` on its path that shifts elements up.

**What it does:** takes the vector in ECX (unused) and three stack arguments:
the first and one-past-last element of a source range, and a destination.

1. If the first and last are equal, it returns the destination unchanged.
2. Otherwise, for each 4-byte element in the range, in order: if the
   destination pointer isn't null, it copies the element there; it then moves
   both pointers on by 4. It stops when the source pointer reaches the last.
3. It returns the destination pointer just past the copied elements.

It removes its three stack arguments.

**Reads and writes:** reads the source range; writes the destination range.

**How the host reaches it:** `composition.cpp` routes calls to it to the heap
stage, which lists it among the helpers for the initializer roots 14 and 15.
Context only, not proof.

**Why this name:** the library-code rule. Visual C++ 6's `vector::_Ucopy(first,
last, dest)` walks the range and constructs each element at the destination
with the library's placement copy, which skips a null destination, then
returns the destination's end. That matches the steps above, including the
null check and the return value. `004BF910` uses it as `vector::insert` does:
to copy the old elements around the insert point into a new buffer.

**Still unknown:** nothing about the name. The body may also serve other
4-byte element types' `_Ucopy`; the name fits all of them.

## sub_00475C20

**Name and confidence:** `std_vector__Ufill`, confirmed.

**Kind:** statically linked Microsoft library code: the `vector` member
`_Ufill` from Visual C++ 6's `<vector>`, for 4-byte elements.

**Extent:** `00475C20` to `00475C42`, 35 bytes.

**Callers:** Ghidra lists 39 functions that call it, and 80 call sites in all,
four of them in code it hasn't marked as a function (for example `00589173`
and `004A8299`). [`004BF910`](objects.md#sub_004bf910) calls it at `004BFA79`
to put one new element into a new buffer and at `004BFAFC` to put one new
element at the vector's end, each time with a count of 1.

**What it does:** takes the vector in ECX (unused) and three stack arguments:
a destination, a count and a pointer to a 4-byte value.

1. If the count is 0, it returns at once.
2. Otherwise, count times: if the destination pointer isn't null, it copies
   the value there; it then moves the destination on by 4.

It returns no value and removes its three stack arguments.

**Reads and writes:** reads the value; writes count elements at the
destination.

**How the host reaches it:** `composition.cpp` routes calls to it to the heap
stage, which lists it among the helpers for the initializer roots 14 and 15.
Context only, not proof.

**Why this name:** the library-code rule. Visual C++ 6's `vector::_Ufill(dest,
count, value)` constructs count copies of the value from the destination on,
with the same null-skipping placement copy, and returns nothing. That matches
the steps above. `004BF910` uses it as `vector::insert(position, 1, value)`
does, to place the inserted copy.

**Still unknown:** nothing about the name. The body may also serve other
4-byte element types' `_Ufill`; the name fits all of them.

## sub_004D5110

**Name and confidence:** `std__Construct`, confirmed.

**Kind:** statically linked Microsoft library code: the function template
`_Construct` from Visual C++ 6's `<xmemory>`, for 4-byte values.

**Extent:** `004D5110` to `004D5118`, 9 bytes.

**Callers:** Ghidra lists 39 functions that call it, and 62 call sites in all,
nine of them in code it hasn't marked as a function (for example `00589157`
and `0045A9BF`). [`0058AEC0`](objects.md#sub_0058aec0) calls it at `0058AF3E`
with a new list node's value field (`+8`) in ECX and a pointer to the object
being added in EDX, to store the object in the node.

**What it does:** takes a destination pointer in ECX and a pointer to a 4-byte
value in EDX. If the destination isn't null, it copies the value into it.
Either way it returns. It has no stack arguments.

**Reads and writes:** reads the value; writes the destination.

**How the host reaches it:** `composition.cpp` routes calls to it to the heap
stage, which lists it among the helpers for the initializer roots 14 and 15.
Context only, not proof.

**Why this name:** the library-code rule. Visual C++ 6's
`_Construct(pointer, value)` copy-constructs the value in place with a
placement `new`, and the compiler skips the construction when the pointer is
null. For a 4-byte value that is exactly the one guarded copy above. It takes
its two arguments in ECX and EDX because, like the game's own plain functions
(for example [`0058B1C0`](objects.md#sub_0058b1c0)), it was compiled with
fastcall. `0058AEC0` uses it where the library's `list` builds a new node's
value.

**Still unknown:** nothing about the name.

## sub_004FD1C0

**Name and confidence:** `std_vector_size`, confirmed.

**Kind:** statically linked Microsoft library code: the `vector` member `size`
from Visual C++ 6's `<vector>`, for 4-byte elements.

**Extent:** `004FD1C0` to `004FD1D2`, 19 bytes.

**Callers:** Ghidra lists 50 functions that call it, and 156 call sites in
all, 24 of them in code it hasn't marked as a function (for example
`00499EDB` and `0042E485`). [`004BF910`](objects.md#sub_004bf910) calls it with
its vector in ECX at `004BFA21`, `004BFA2D` and `004BFA3D` to work out a new
buffer size, and at `004BFAB5` to set the new last pointer.

**What it does:** takes the vector in ECX. If the first-element pointer at
`+4` is null, it returns 0. Otherwise it returns the last pointer at `+8`
minus the first pointer, divided by 4 (an arithmetic shift right by 2): the
number of elements.

**Reads and writes:** reads `+4` and `+8` of the vector.

**How the host reaches it:** `composition.cpp` routes calls to it to the heap
stage, which lists it among the helpers for the initializer roots 14 and 15.
Context only, not proof.

**Why this name:** the library-code rule. Visual C++ 6's `vector::size()`
returns 0 when the first pointer is null and otherwise last minus first, in
elements; for 4-byte elements that is the subtraction and shift above, at the
layout's `+4` and `+8`. `004BF910` uses it as `vector::insert` does when it
grows the buffer: the new size is the old size plus the larger of the old size
and 1.

**Still unknown:** nothing about the name. The body may also serve other
4-byte element types' `size`; the name fits all of them.
