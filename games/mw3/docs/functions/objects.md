# Objects

Constructors of some of the game's object classes, and the game's list of
numbered objects. The list is a global library `list` of object pointers at
`00603FD8`, built at startup by [`0040FFF0`](globals.md#sub_0040fff0); its
head-node pointer is at `00603FDC` and its count at `00603FE0`. Objects of the
numbered class add themselves to it when they are built, each with an ID
number, and other code finds them again by that number.

Profile `mw3-us-1-2-retail`, image SHA-256
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`. Studied
2026-11-04 in Ghidra 12.1.3 with the default analysis. Addresses are virtual
addresses at image base `0x400000`; RVAs are the address minus `0x400000`. To
repeat the work, import that `Mech3.exe` into Ghidra and go to each address; the
[README](README.md) has the details and the section format.

The program has no run-time type information, so these classes' real names
are unknown (the word before each table of virtual functions points into code,
not at type data). Each class is named here for what it does, and each section
gives the address of its table of virtual functions (its vtable), which is
what tells the classes apart. Library `list` and `vector` layouts are in
[`containers.md`](containers.md).

A numbered object starts with: `+0` vtable, `+4` the ID, then a library
`vector` of 4-byte pointers at `+8` (its allocator byte at `+8`, first `+0xC`,
last `+0x10`, buffer end `+0x14`).

## sub_004BF910

**Name and confidence:** `LinkedNumberedObject_Init`, confirmed.

**Kind:** the game's own code.

**Extent:** `004BF910` to `004BFB8F`, 640 bytes. Ghidra's listing of the
function stops at `004BFB41`; the rest, `004BFB43` to the return at
`004BFB8D`, is reached from inside it and is part of the same body.

**Callers:** three functions, each a constructor of a class built on this one
that calls it first, with the new object in ECX: `004C0310` (from `004C0348`)
and `004C0570` (from `004C05A8`), the constructors of the global objects
built by [`00410400`](globals.md#sub_00410400) and
[`00410450`](globals.md#sub_00410450), and `004BE300` (from `004BE3DD`). Each
passes an ID, a null array pointer and a count; `004C0310` and `004C0570`
pass the ID they got from [`0058B1C0`](#sub_0058b1c0) and a count of 1. After
it returns, each stores its own vtable.

**What it does,** in order. It takes the object in ECX and three stack
arguments: an ID, a pointer to an array of 4-byte object pointers, and a
count.

1. Registers the compiler's exception-cleanup handler data at `005B7898`, so
   that a failure part-way through undoes the parts already built.
2. Calls [`004D5120`](#sub_004d5120) with the ID, which builds the numbered
   object it is based on (its vector holds one empty slot).
3. Sets the vtable at `+0` to `005CA6D8` and clears bit 0 of the flag byte at
   `+0x18`.
4. Makes sure the vector at `+8` has room for the count: if its capacity (0
   when the first pointer is null, otherwise buffer end minus first, in
   elements) is below the count, it gets a buffer of count elements (or 0 if
   the count is negative) from [`operator_new`](heap.md#sub_005abd26), copies
   the old elements into it with an inline loop that skips a null
   destination, frees the old buffer with
   [`operator_delete`](heap.md#sub_005abd1a), and sets the first, last and
   end pointers to the new buffer, the same number of elements, and count
   elements.
5. Stores `00604068`, the address of the global object built by
   [`00410310`](globals.md#sub_00410310), into the vector's first slot,
   without changing the last pointer.
6. If the array pointer is null or the count is 0 or less, skips to step 8.
7. Otherwise, for each of the count array elements in turn, appends it to the
   vector at the last pointer. These are the library's
   `vector::insert(position, 1, value)` steps, written inline, with the
   position always the last pointer:
   - If there is no spare slot (buffer end minus last is below 1), it grows:
     the new capacity is the size plus the larger of the size and 1 (sizes
     from [`std_vector_size`](containers.md#sub_004fd1c0)); it gets a new
     buffer from `operator_new`, copies the elements before the position with
     [`std_vector__Ucopy`](containers.md#sub_00475bf0), places the value with
     [`std_vector__Ufill`](containers.md#sub_00475c20), copies the elements
     after the position (none) with `std_vector__Ucopy`, calls
     [`Stub_ReturnTwoArgs`](containers.md#sub_0040baf0) where the library
     destroys the old elements, frees the old buffer, and sets the end, last
     (old size plus one) and first pointers.
   - If there is a spare slot and no element after the position (always,
     since the position is the last pointer), it calls `std_vector__Ucopy`
     over an empty range, places the value at the last pointer with
     `std_vector__Ufill`, runs an inline fill over an empty range, then adds 4
     to the last pointer.
   - The third path, for a position with elements after it, shifts those
     elements up by one (`004BFB19` to `004BFB55`: `std_vector__Ucopy` for the
     last element, then an inline backward copy and fill) and then adds 4 to
     the last pointer. It can never run here, because the position is always
     the last pointer, so no element is ever after it.
8. Removes the exception-cleanup registration and returns the object,
   removing its three stack arguments.

All three callers pass a null array, so step 7 doesn't run for them. For
`004C0310` and `004C0570`, step 4 does nothing either (a count of 1 fits the
one empty slot), so the object leaves with `00604068` in the vector's slot and
an empty vector. Each of those two constructors then appends one pointer of
its own (`00604068` and `00604058`), which goes into that same first slot.

**Reads and writes:** the object's vtable, flag byte at `+0x18` and vector;
the array it is given; heap buffers through `operator_new` and
`operator_delete`; the thread's exception-handler chain.

**How the host reaches it:** `tools/m4-crt-heap-carry/host/composition.cpp`
routes calls to it to the heap stage (`heap_stage.hpp`), which runs it while
running the initializer roots 14 and 15. The heap-carry
[README](../../../../tools/m4-crt-heap-carry/README.md) ("Roots 14..15") says
each of those constructors pushes a pointer to another root's object
(`00604068` and `00604058`) into its own vector; that is the append after this
function returns, so it agrees with step 5 being overwritten. Context only,
not proof.

**Why this name:** the game-code rule. Every step and branch is described
above, including the shifting path, which can never run; the README's proof
rule counts a branch as described when the section says why it can't run.
Every caller uses it as a base constructor: it calls it first on
a new object and then stores its own vtable. It builds a numbered object that
also holds a list of pointers to other objects, so it is named for that.

**Still unknown:** what the class is, what the flag bit at `+0x18` means, and
why `00604068` is stored in the first slot before the callers store their own
pointer there.

## sub_004C8600

**Name and confidence:** `SimpleObject_Init`, confirmed.

**Kind:** the game's own code.

**Extent:** `004C8600` to `004C8618`, 25 bytes.

**Callers:** 17 functions, from 22 call sites. Each calls it with a new
object in ECX and then stores its own vtable into the object, so it is a base
constructor:
- `004105D0`, `00410610`, `00410630`, `00410650`, `00410680` and `004C8750`,
  the constructors of the six global objects built by
  [`00410220`](globals.md#sub_00410220) to
  [`004103B0`](globals.md#sub_004103b0);
- `004C9D00`, `004CA370`, `004CACA0`, `004CAD70`, `004CBE10`, `004D08D0` and
  `004D1C80`, each a short constructor of the same shape;
- `004C0090`, which builds six different objects in turn, calling it before
  each one's vtable (`004C0144` to `004C0273`);
- `0047A320`, `004CF820` and `004E9CA0`, longer functions that build one such
  object.

**What it does:** takes the object in ECX. It clears the word at `+8`, clears
bit 0 of the flag byte at `+4`, sets the vtable at `+0` to `005CB180`, and
returns the object. There are no branches and no stack arguments.

**Reads and writes:** the object's first 12 bytes.

**How the host reaches it:** `composition.cpp` routes calls to it to the heap
stage, which names it the base constructor of the roots 8 to 13 and runs it
for them. The heap-carry
[README](../../../../tools/m4-crt-heap-carry/README.md) ("Roots 8..13")
describes it the same way: vtable `005CB180`, field `+8` cleared, flag bit 0
cleared. Context only, not proof.

**Why this name:** the game-code rule. Its three steps are fully described,
and all 17 callers use it as the base constructor of their own classes. The
class is the simplest shared base among them, so it is named for that.

**Still unknown:** what the class is, and what `+4` and `+8` hold.

## sub_004D5120

**Name and confidence:** `NumberedObjectB_Init`, confirmed.

**Kind:** the game's own code.

**Extent:** `004D5120` to `004D5138`, 25 bytes.

**Callers:** six functions, each a constructor that calls it first with its
new object in ECX: `004021C0` (from `004021FF`, with an ID of -1), `004BCBA0`
(from `004BCBF0`) and `004BFBB0` (from `004BFBE9`), which pass an ID they got
from [`0058B1C0`](#sub_0058b1c0), and [`004BF910`](#sub_004bf910) (from
`004BF937`), `004BFE40` (from `004BFE64`) and `004C5640` (from `004C5665`),
which pass on an ID they were given.

**What it does:** takes the object in ECX and one stack argument, an ID.
Calls [`0058AEC0`](#sub_0058aec0) with the ID, which builds the numbered
object and adds it to the list, then sets the vtable at `+0` to `005CCDA8`,
returns the object and removes its argument. There are no branches.

**Reads and writes:** the object's vtable, plus what `0058AEC0` writes.

**How the host reaches it:** `composition.cpp` routes calls to it to the heap
stage, which runs it for the initializer roots 14 and 15. Context only, not
proof.

**Why this name:** the game-code rule. Both steps are described, and every
caller uses it as a base constructor with an ID. It is a second numbered
class, built directly on `0058AEC0`'s.

**Still unknown:** what the class is and what its own virtual functions do.

## sub_0058AEC0

**Name and confidence:** `NumberedObject_Init`, confirmed.

**Kind:** the game's own code.

**Extent:** `0058AEC0` to `0058AFDF`, 288 bytes.

**Callers:** one function, [`004D5120`](#sub_004d5120), from `004D5128`, which
passes its own object and ID on.

**What it does,** in order. It takes the object in ECX and one stack argument,
the ID.

1. Registers the compiler's exception-cleanup handler data at `005BA08B`.
2. Builds the empty vector at `+8`: stores the ID's low byte in the
   allocator byte at `+8` and clears the first, last and end pointers at
   `+0xC`, `+0x10` and `+0x14`.
3. Sets the vtable at `+0` to `005CEFD0` and stores the ID at `+4`.
4. Adds the object to the end of the global list: reads the head node from
   `00603FDC` and its previous node, gets a 12-byte node from
   [`operator_new`](heap.md#sub_005abd26), links it after the previous node
   and before the head (using the new node itself for either link that is
   null), points the head's previous link and the old last node's next link
   at it, stores the object in its value field through
   [`std__Construct`](containers.md#sub_004d5110), and adds 1 to the count at
   `00603FE0`.
5. Makes sure the vector has room for one element: if its capacity is below
   1 (always, since it was just cleared), it gets a 4-byte buffer from
   `operator_new`, copies the old elements into it with an inline loop (none),
   frees the old buffer (null) with [`operator_delete`](heap.md#sub_005abd1a)
   and sets the first, last and end pointers to the new buffer, the same
   number of elements (none) and one element. If the capacity were already
   1 or more, it would skip this step.
6. Stores 0 in the vector's first slot, without changing the last pointer.
7. Removes the exception-cleanup registration and returns the object,
   removing its argument.

**Reads and writes:** the object's first 24 bytes; the list's head node and
count at `00603FDC` and `00603FE0`; a new list node and a new vector buffer on
the heap; the thread's exception-handler chain.

**How the host reaches it:** `composition.cpp` routes calls to it to the heap
stage, which runs it for the initializer roots 14 and 15. The heap-carry
[README](../../../../tools/m4-crt-heap-carry/README.md) ("Roots 14..15") says
it inserts the object into root 1's list (head `603FDC`, size `603FE0`), which
agrees with step 4. Context only, not proof.

**Why this name:** the game-code rule. Every step is described; the one
branch inside step 5 and the null checks inside step 4 are the library's
`vector::reserve` and `list` node steps, written inline. Its one caller uses
it as a base constructor. It builds the base numbered object, the one that
adds itself to the list, so it is named for that.

**Still unknown:** the class's real name. Storing the ID's low byte at `+8`
is most likely how the compiler copies the vector's empty allocator object
from a reused stack slot; the byte has no meaning.

## sub_0058B160

**Name and confidence:** `NumberedObjects_FindByNumber`, confirmed.

**Kind:** the game's own code.

**Extent:** `0058B160` to `0058B1BF`, 96 bytes.

**Callers:** 11 functions: `0049DC80` (twice), `0049F800`, `0049FA20`,
`0049FCE0`, `004BC4E0`, `004BC570`, `004BC960`, `004BCBA0`, `004CF330`,
`004D9ED0` and [`0058B1C0`](#sub_0058b1c0) (twice). Each passes an ID in ECX
and checks the result for null before using it as an object; several then
call one of the object's virtual functions.

**What it does:** takes an ID in ECX and returns the first object in the list
whose ID matches, or 0.

1. Reads the head node from `00603FDC` and starts at the node after it.
2. While the current node isn't the head: calls the virtual function at
   `+0x18` of the vtable of the object in the node's value field, with that
   object in ECX. If the result equals the ID, it stops; otherwise it moves to
   the next node.
3. Reads the head node again. If the current node is the head (no match), it
   returns 0; otherwise it returns the object in the current node.

**Reads and writes:** reads the list at `00603FDC` and each object's vtable;
writes nothing itself.

**How the host reaches it:** `composition.cpp` routes calls to it to the heap
stage, which runs it for the initializer roots 14 and 15. The heap-carry
[README](../../../../tools/m4-crt-heap-carry/README.md) ("Roots 14..15") calls
the virtual function at `+0x18` each object's `GetID`, at `0040A850` for
those roots' objects. Context only, not proof.

**Why this name:** the game-code rule. Every step is described, and every
caller passes an ID and uses the result as the matching object or null.

**Still unknown:** whether every class in the list reads its ID the same way
(`0040A850` is one of them).

## sub_0058B1C0

**Name and confidence:** `NumberedObjects_PickFreeNumber`, confirmed.

**Kind:** the game's own code.

**Extent:** `0058B1C0` to `0058B21B`, 92 bytes.

**Callers:** seven functions: `004797C0`, `004BCBA0`, `004BFBB0`, `004C0310`,
`004C0570`, `004C5C00` and `004D5460`. Each gets an ID from it and passes it on
to build a numbered object: `004BFBB0` and `004BCBA0` to
[`004D5120`](#sub_004d5120), `004C0310` and `004C0570` to
[`004BF910`](#sub_004bf910), and `004D5460` to `0047A550`. Most pass the word
at `005F2A48` as the low bound and the preferred ID; `004BFBB0` passes 300.

**What it does:** takes a low bound in ECX, a high bound in EDX and a
preferred ID on the stack, and returns an ID that no object in the list has,
or -1.

1. If the preferred ID is negative, it becomes the low bound.
2. If the preferred ID is outside the range from the low bound up to (not
   including) the high bound, it asks
   [`0058B160`](#sub_0058b160) for that ID, returns it if no object has it,
   and otherwise starts the search at the low bound. If it is in range, the
   search starts at the preferred ID.
3. From the start, it asks `0058B160` for each ID in turn and returns the
   first one no object has. After the ID just below the high bound it goes
   back to the low bound, and stops when it gets there.
4. If it stops without finding a free ID, it returns -1.

Because the stop test compares with the low bound, not with the start, a
search that starts above the low bound never tries the IDs below its start.
It removes its stack argument.

**Reads and writes:** only what `0058B160` reads.

**How the host reaches it:** `composition.cpp` routes calls to it to the heap
stage, which runs it for the initializer roots 14 and 15. The heap-carry
[README](../../../../tools/m4-crt-heap-carry/README.md) ("Roots 14..15") says
those roots' constructors get IDs from `[10000, 10100)` starting at the word at
`005F2A48`, which is 10000; that matches `004C0310` passing that word as the
low bound and the preferred ID, with the low bound plus 100 as the high bound.
Context only, not proof.

**Why this name:** the game-code rule. Every step and branch is described,
and every caller uses the result as a new object's ID.

**Still unknown:** whether stopping at the low bound instead of the start is
intended; it only matters once the range is nearly full.
