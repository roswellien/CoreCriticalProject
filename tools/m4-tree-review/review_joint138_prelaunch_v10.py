"""Attribute the actual compiler's four-byte thread epoch TLS cell explicitly."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('review_joint138_prelaunch_v9.py')
scope={'__file__':str(p),'__name__':'materialize_epoch_TLS'}
exec(compile(p.read_text(),str(p),'exec'),scope);t=scope['t']
a="x['type']==11 and x['symbol']['section']>0";assert t.count(a)==1
t=t.replace(a,"x['type']==11 and (x['symbol']['section']>0 or x['symbol']['name']=='_Init_thread_epoch' and x['symbol']['section']==0)")
a="      sym=x['symbol'];assert se[sym['section']]['bytes'][sym['value']:sym['value']+8]==bytes(8)"
assert t.count(a)==1
extra="""      sym=x['symbol']
      if sym['section']==0:
       assert sym['name']=='_Init_thread_epoch' and sym['value']==0
       epoch=pin(Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231/crt/src/vcruntime/thread_safe_statics.cpp')).read_text()
       assert 'static int const epoch_start = INT_MIN;'in epoch and '__declspec(thread) int _Init_thread_epoch = epoch_start;'in epoch
       offset=struct.unpack_from('<i',actual,x['offset'])[0]-struct.unpack_from('<i',raw,x['offset'])[0]
       d=N.directories(image)[9];start,end,_,_,zero,_=struct.unpack('<4Q2I',N.image_bytes(image,image.image_base+d[0],40))
       assert offset>=0 and offset+4<=end-start+zero and N.image_bytes(image,start+offset,4)==struct.pack('<I',0x80000000)
       counts['actual_compiler_thread_epoch_TLS_cells']+=1
       continue
      assert se[sym['section']]['bytes'][sym['value']:sym['value']+8]==bytes(8)"""
t=t.replace(a,extra)
t=t.replace("  pin(R/'tools/m4-tree-review/review_joint138_prelaunch_v8.py');","  pin(R/'tools/m4-tree-review/review_joint138_prelaunch_v9.py');pin(R/'tools/m4-tree-review/review_joint138_prelaunch_v8.py');")
exec(compile(t,str(Path(__file__)),'exec'),globals())
