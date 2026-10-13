"""x87/FP lowering extension for lift_closure.py, the same contract as tools/m4-mfc-source/lift.py.

The lowering admits remill's float/double and 64-bit memory bridges, the x87 exception clear/test
bridges (served from the host x87 status right after the lifted operation), the reviewed FP LLVM
intrinsics (fabs, constrained FP, memcpy/memmove, lifetime markers) and exactly the empty FP
ordering barrier remill emits around x87 operations. Anything else still fails the component.
"""
import ctypes as c
import x87_bridges
BRIDGES={'__remill_read_memory_'+x for x in ('64','f32','f64','f80')}|{'__remill_write_memory_'+x for x in ('64','f32','f64','f80')}|{'__remill_fpu_exception_clear','__remill_fpu_exception_test','__remill_fpu_set_rounding','__remill_fpu_get_rounding','__remill_sync_hyper_call'}|x87_bridges.BRIDGES
BARRIER='call void asm sideeffect "", "~{memory},~{dirflag},~{fpsr},~{flags}"()'
PATCHES=[
 ("need(n in ('llvm.ctpop.i8','llvm.ctpop.i32','llvm.fshl.i32','llvm.fshr.i32')",
  "need(n in ('llvm.ctpop.i8','llvm.ctpop.i32','llvm.abs.i64','llvm.abs.i32','llvm.smax.v4i16','llvm.smin.v4i16','llvm.umax.v8i8','llvm.umin.v8i8','llvm.smax.v8i8','llvm.smin.v8i8','llvm.umax.v4i16','llvm.umin.v4i16','llvm.uadd.sat.v8i8','llvm.usub.sat.v8i8','llvm.sadd.sat.v8i8','llvm.ssub.sat.v8i8','llvm.uadd.sat.v4i16','llvm.usub.sat.v4i16','llvm.sadd.sat.v4i16','llvm.ssub.sat.v4i16','llvm.bswap.i32','llvm.bswap.i16','llvm.smax.i16','llvm.smin.i16','llvm.umax.i16','llvm.umin.i16','llvm.smax.i32','llvm.smin.i32','llvm.umax.i32','llvm.umin.i32','llvm.smax.i8','llvm.smin.i8','llvm.umax.i8','llvm.umin.i8','llvm.usub.sat.i16','llvm.uadd.sat.i16','llvm.ssub.sat.i16','llvm.sadd.sat.i16','llvm.usub.sat.i8','llvm.uadd.sat.i8','llvm.ssub.sat.i8','llvm.sadd.sat.i8','llvm.fshl.i32','llvm.fshr.i32','llvm.fabs.f80','llvm.fabs.f32','llvm.fabs.f64','llvm.memcpy.p0.p0.i32','llvm.memmove.p0.p0.i32','llvm.lifetime.start.p0','llvm.lifetime.end.p0','llvm.is.fpclass.f80','llvm.cttz.i32','llvm.ctlz.i32','llvm.cttz.i16','llvm.ctlz.i16') or n.startswith('llvm.experimental.constrained.')"),
 ("need(api.IsAFunction(api.GetCalledValue(inst)),'Only named LLVM calls')",
  "\n                    if not api.IsAFunction(api.GetCalledValue(inst)):\n                        need('"+BARRIER+"' in api.text(inst),'Only exact original empty FP ordering barrier');continue"),
]
def llvm_class(base):
    class FPTypes(base):
        def text(self,v):
            p=self.PrintValueToString(v);s=c.string_at(p).decode();self.DisposeMessage(p);return s
    return FPTypes
