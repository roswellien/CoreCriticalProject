"""Create the fresh functional allocator namespace from frozen heap-return sources.

This is source preparation only; it never launches a native worker or game.
"""
import pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
HERE=pathlib.Path(__file__).resolve().parent
OLD=ROOT/'tools/m4-crt-heap-return'
def main():
    for old,new in [('heap_return.hpp','allocation.hpp'),('heap_return_binding.inc','allocation_binding.inc'),
                    ('capture.s','capture.s'),('build_v2.ps1','build.ps1')]:
        p=HERE/new
        if p.exists():raise ValueError('Fresh source namespace required: '+str(p))
        s=(OLD/old).read_text()
        if old in ('heap_return.hpp','heap_return_binding.inc'):
            s=s.replace('m4_crt_heap_return','m4_crt_allocation')
        if old=='build_v2.ps1':
            s=s.replace('m4-crt-heap-return','m4-crt-allocation').replace('entry_heap_return.exe','entry_allocation.exe')
            s=s.replace('preparation-r2','preparation-r1')
        p.write_text(s)
    p=HERE/'native/CMakeLists.txt';p.parent.mkdir(parents=True,exist_ok=True)
    s=(OLD/'native/CMakeLists.txt').read_text().replace('MW34CRTHeapReturn','MW34CRTAllocation').replace('entry_heap_return','entry_allocation')
    p.write_text(s)
if __name__=='__main__':main()
