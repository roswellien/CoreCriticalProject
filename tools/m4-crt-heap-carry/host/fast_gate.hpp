// Gate published by the active MFC Stage for the inlined bridge fast paths (fast_bridges.cpp, linked into each
// recompiled function by inline_objects.py). Every field mirrors a value the Stage's own checks read; the fast
// path succeeds only when all of Stage::guard, read_fast/write_fast and the GuestMemory region cache admit the
// access, and otherwise calls the unchanged out-of-line bridge. The Stage publishes the gate in run() and clears
// it (enabled = 0) before returning.
#pragma once
// Header-free on purpose: the fast-path bitcode must not include C++ library headers, whose
// /FAILIFMISMATCH and /DEFAULTLIB directives would otherwise be copied into every recompiled object.

extern "C" {
struct Mw34FastGate {
    unsigned enabled;               // nonzero while Stage::run is executing guest code
    unsigned long thread;           // host thread id of that Stage (TEB ClientId.UniqueThread)
    void *const *owner_slot;        // address of mf::owner on the Stage thread
    const void *stage;              // the Stage (owner must equal it)
    const void *token;              // Stage token_ptr (the remill memory token)
    const bool *active, *complete;  // live Stage flags
    unsigned low, read_top, write_top;          // Stage::frame window: read (write=false) and write bounds
    unsigned image_lo, image_hi;                // initterm game image (empty range otherwise)
    unsigned data_lo, data_hi;                  // initterm game .data (empty range otherwise)
    unsigned gheap_lo;                          // Host::GuestHeap::lo
    const unsigned *gheap_mapped;               // live Host::GuestHeap::mapped
    const void *memory;                         // &runtime.memory()
    const void *hits;                           // the Stage thread's fastmem::hits array
    const unsigned long long *generation;       // &fastmem::generation
    unsigned *reads, *writes;                   // Stage counters
};
extern Mw34FastGate mw34_fast_gate;
// Layout mirror of mw34::fastmem::Hit (guest_memory_fast.hpp); mfc_stage.hpp static_asserts the offsets.
struct Mw34FastHit {
    const void *owner;
    unsigned long long generation;
    unsigned start;
    unsigned long long size;
    unsigned char *bytes;
    unsigned char permissions;
};
}
