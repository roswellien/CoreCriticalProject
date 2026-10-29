// Always-inline fast paths for the hottest remill bridges, compiled to bitcode and linked into each recompiled
// function (inline_objects.py). Each returns the same result as the out-of-line bridge in composition.cpp when
// every condition that bridge checks holds; any other case calls that bridge, which performs the full check
// (and any denial) exactly as before.
//
// Memory: __remill_{read,write}_memory_* with an MFC Stage owner run Stage::read<T>/write<T>: guard(p), then
// read_fast/write_fast (a subset of readable/writable), then the GuestMemory region cache, then a memcpy and the
// reads/writes counter. The fast path performs exactly those steps from the published gate.
// x87: __remill_fpu_exception_clear(127) is fnclex and __remill_fpu_exception_test(127) is fnstsw & 127 whenever
// a Stage owner exists on this thread. The inline asm carries the clobbers remill's own FP ordering barriers use.
#include "fast_gate.hpp"  // header-free: no C++ library headers (see fast_gate.hpp)

// Real definitions (llvm-link --only-needed --internalize makes them internal to each object); always_inline
// lets the O2 pipeline inline them at every call site. Compiled with exceptions: the slow paths throw Faults.
#define MW34_FAST extern "C" __attribute__((always_inline))

extern "C" {
unsigned char __remill_read_memory_8(void *, unsigned);
unsigned short __remill_read_memory_16(void *, unsigned);
unsigned __remill_read_memory_32(void *, unsigned);
unsigned long long __remill_read_memory_64(void *, unsigned);
float __remill_read_memory_f32(void *, unsigned);
double __remill_read_memory_f64(void *, unsigned);
void *__remill_write_memory_8(void *, unsigned, unsigned char);
void *__remill_write_memory_16(void *, unsigned, unsigned short);
void *__remill_write_memory_32(void *, unsigned, unsigned);
void *__remill_write_memory_64(void *, unsigned, unsigned long long);
void *__remill_write_memory_f32(void *, unsigned, float);
void *__remill_write_memory_f64(void *, unsigned, double);
void __remill_fpu_exception_clear(int);
int __remill_fpu_exception_test(int);
}

namespace {
using Hit = Mw34FastHit;
__attribute__((always_inline)) inline unsigned long current_thread() {  // TEB ClientId.UniqueThread, as GetCurrentThreadId
    unsigned long t; __asm__("movl %%gs:0x48, %0" : "=r"(t)); return t;
}

__attribute__((always_inline)) inline bool owner_here(const Mw34FastGate &g) {
    return g.enabled && current_thread() == g.thread;
}
__attribute__((always_inline)) inline bool guard(const Mw34FastGate &g, void *p) {
    return owner_here(g) && *g.owner_slot == g.stage && *g.active && !*g.complete && p == g.token;
}
__attribute__((always_inline)) inline unsigned char *cached(const Mw34FastGate &g, unsigned a, unsigned n, unsigned char perm) {
    const Hit &h = static_cast<const Hit *>(g.hits)[(a >> 12) & 1023];
    if (h.owner == g.memory && h.generation == *g.generation && a >= h.start &&
        (unsigned long long)a - h.start + n <= h.size && (h.permissions & perm) != 0)
        return h.bytes + (a - h.start);
    return nullptr;
}
template <class T> __attribute__((always_inline)) inline bool load(void *p, unsigned a, T &v) {
    const Mw34FastGate &g = mw34_fast_gate;
    if (!guard(g, p)) return false;
    const unsigned long long e = (unsigned long long)a + sizeof(T);
    if (!((a >= g.low && e <= g.read_top) || (a >= g.image_lo && e <= g.image_hi) || (a >= g.gheap_lo && e <= *g.gheap_mapped)))
        return false;
    const unsigned char *b = cached(g, a, sizeof(T), 1);
    if (!b) return false;
    __builtin_memcpy(&v, b, sizeof(T));
    ++*g.reads;
    return true;
}
template <class T> __attribute__((always_inline)) inline bool store(void *p, unsigned a, T v) {
    const Mw34FastGate &g = mw34_fast_gate;
    if (!guard(g, p)) return false;
    const unsigned long long e = (unsigned long long)a + sizeof(T);
    if (!((a >= g.low && e <= g.write_top) || (a >= g.data_lo && e <= g.data_hi) || (a >= g.gheap_lo && e <= *g.gheap_mapped)))
        return false;
    unsigned char *b = cached(g, a, sizeof(T), 2);
    if (!b) return false;
    __builtin_memcpy(b, &v, sizeof(T));
    ++*g.writes;
    return true;
}
} // namespace

MW34_FAST unsigned char mw34_fast_read_memory_8(void *p, unsigned a) { unsigned char v; return load(p, a, v) ? v : __remill_read_memory_8(p, a); }
MW34_FAST unsigned short mw34_fast_read_memory_16(void *p, unsigned a) { unsigned short v; return load(p, a, v) ? v : __remill_read_memory_16(p, a); }
MW34_FAST unsigned mw34_fast_read_memory_32(void *p, unsigned a) { unsigned v; return load(p, a, v) ? v : __remill_read_memory_32(p, a); }
MW34_FAST unsigned long long mw34_fast_read_memory_64(void *p, unsigned a) { unsigned long long v; return load(p, a, v) ? v : __remill_read_memory_64(p, a); }
MW34_FAST float mw34_fast_read_memory_f32(void *p, unsigned a) {
    unsigned v;
    if (!load(p, a, v)) return __remill_read_memory_f32(p, a);
    float f; __builtin_memcpy(&f, &v, 4); return f;
}
MW34_FAST double mw34_fast_read_memory_f64(void *p, unsigned a) {
    unsigned long long v;
    if (!load(p, a, v)) return __remill_read_memory_f64(p, a);
    double f; __builtin_memcpy(&f, &v, 8); return f;
}
MW34_FAST void *mw34_fast_write_memory_8(void *p, unsigned a, unsigned char v) { return store(p, a, v) ? p : __remill_write_memory_8(p, a, v); }
MW34_FAST void *mw34_fast_write_memory_16(void *p, unsigned a, unsigned short v) { return store(p, a, v) ? p : __remill_write_memory_16(p, a, v); }
MW34_FAST void *mw34_fast_write_memory_32(void *p, unsigned a, unsigned v) { return store(p, a, v) ? p : __remill_write_memory_32(p, a, v); }
MW34_FAST void *mw34_fast_write_memory_64(void *p, unsigned a, unsigned long long v) { return store(p, a, v) ? p : __remill_write_memory_64(p, a, v); }
MW34_FAST void *mw34_fast_write_memory_f32(void *p, unsigned a, float f) {
    unsigned v; __builtin_memcpy(&v, &f, 4); return store(p, a, v) ? p : __remill_write_memory_f32(p, a, f);
}
MW34_FAST void *mw34_fast_write_memory_f64(void *p, unsigned a, double f) {
    unsigned long long v; __builtin_memcpy(&v, &f, 8); return store(p, a, v) ? p : __remill_write_memory_f64(p, a, f);
}
MW34_FAST void mw34_fast_fpu_exception_clear(int mask) {
    const Mw34FastGate &g = mw34_fast_gate;
    if (mask == 127 && owner_here(g) && *g.owner_slot) { __asm__ volatile("fnclex" ::: "memory", "fpsr", "dirflag", "flags"); return; }
    __remill_fpu_exception_clear(mask);
}
MW34_FAST int mw34_fast_fpu_exception_test(int mask) {
    const Mw34FastGate &g = mw34_fast_gate;
    if (mask == 127 && owner_here(g) && *g.owner_slot) {
        unsigned short st;
        __asm__ volatile("fnstsw %0" : "=m"(st) : : "memory", "fpsr", "dirflag", "flags");
        return st & 127;
    }
    return __remill_fpu_exception_test(mask);
}
