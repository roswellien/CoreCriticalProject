"""Add causal address contracts; no original operand values enter executable."""
from pathlib import Path
import hashlib,json
p=Path(__file__).resolve().parent;R=p.parents[1];base=p/'prepare.py'
frozen=json.loads((R/'reports/m4-widget-native/preparation-r1/report.json').read_text());assert hashlib.sha256(base.read_bytes()).hexdigest()==frozen['files'][str(base)]
s=base.read_text()
s=s.replace("for name in ('component.hpp','component.cpp','native_api.s'):\n  p=bind('tools/m4-widget-native/'+name);shutil.copyfile(p,out/name)","for name in ('component.hpp','component.cpp','native_api.s'):\n  p=bind('tools/m4-widget-native/'+('component_v2.cpp'if name=='component.cpp'else name));shutil.copyfile(p,out/name)")
s=s.replace("FS_begin,FS_count;};'","FS_begin,FS_count,operand_begin,operand_count;};'")
s=s.replace('gi=vi=fi=0','gi=vi=fi=oi=0')
old="h.append('{%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d},'%(row['root'],row['slot'],row['object'],reg['callback'],reg.get('CALL_pc',reg.get('registration_CALL_pc')),gi,len(row['GDI_calls']),vi,len(row['virtual_calls']),fi,len(row['FS_operations'])));gi+=len(row['GDI_calls']);vi+=len(row['virtual_calls']);fi+=len(row['FS_operations'])"
new="observed=next(v for v in font if v['root']==row['root']);h.append('{%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d},'%(row['root'],row['slot'],row['object'],reg['callback'],reg.get('CALL_pc',reg.get('registration_CALL_pc')),gi,len(row['GDI_calls']),vi,len(row['virtual_calls']),fi,len(row['FS_operations']),oi,len(observed['source_accesses'])));gi+=len(row['GDI_calls']);vi+=len(row['virtual_calls']);fi+=len(row['FS_operations']);oi+=len(observed['source_accesses'])"
assert s.count(old)==1;s=s.replace(old,new)
old="h+=['};','using Body=void*(*)(State*,unsigned,void*);']"
new="""h+=['};','struct Operand {unsigned pc,role;long long offset;unsigned width;bool writing;};','inline constexpr Operand operands[]{']
 for observed in font:
  for pc,a,_ignored_actual_value,width,writing in observed['source_accesses']:
   need(pc in byPC,'Every causal widget operand is exact literal source')
   role=1 if 0x20001000<=a<0x20002000 else 2 if a==0x7ffde000 else 0;offset=a-root_frame if role==1 else 0 if role==2 else a
   h.append('{%d,%d,%d,%d,%s},'%(pc,role,offset,width,str(bool(writing)).lower()))
 h+=['};','using Body=void*(*)(State*,unsigned,void*);']"""
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace("'array_iterations':75,'IRs':irs", "'array_iterations':75,'causal_operands':oi,'original_operand_values_seeded':False,'IRs':irs")
s=s.replace("for p in [Path(__file__).resolve(),R/'tools/m4-widget-native/build.py'", "for p in [base,Path(__file__).resolve(),R/'tools/m4-widget-native/derive_component_v2.py',R/'tools/m4-widget-native/build_v2.py',R/'tools/m4-widget-native/build_v2.ps1',R/'tools/m4-widget-native/build.py'")
exec(compile(s,str(base),'exec'),globals())
