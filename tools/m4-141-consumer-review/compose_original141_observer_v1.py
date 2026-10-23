"""Immutable original138 plus tested constructor observation composition.

Preparation only. Whole linked observer attribution and strict transition
validators must be independently admitted before any compiler or worker run.
"""
from pathlib import Path
import hashlib,json,re,shutil,struct
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main():
 out=R/'reports/m4-original141/source-preparation-r1';need(not out.exists(),'Fresh original141 observer');out.mkdir(parents=True);files={};changes=[];asmchanges=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Exact preparation input '+str(p));files[str(p)]=v;return p
 old=R/'reports/m4-startup138-original/preparation-r8';supp=R/'reports/m4-138-validation-review/constructor-input-capture-preparation-r5';geometry=R/'reports/m4-original141/geometry-preparation-r3'
 pin(old/'report.json','9bd1ef9049eccaeb9f87e81f38e001d0d1c805f077c75a8563fc08ec0e67b161');pin(geometry/'report.json','ac67522e4f1cb6089ba3aae2f53be9bd7e141353eaa180afb46f4bf6fb60bc5d')
 for f in old.iterdir():
  if f.is_file()and f.name not in('report.json','pins.json'):shutil.copyfile(pin(f),out/f.name)
 for name in ['pages.bin','spec.hpp','protocol.hpp','selected-order.json','fs-hook-bindings.json']:shutil.copyfile(pin(geometry/name),out/name)
 for name in ['constructor_normal.hpp','constructor_observer_x86.asm','constructor-hook-bindings.json']:shutil.copyfile(pin(supp/name),out/name)
 source=pin(old/'reference.cpp').read_text();parent=source;other=pin(supp/'reference.cpp').read_text();lines=other.splitlines();suppdeltas=json.loads(pin(supp/'changes.json').read_text())
 def change(old,new):
  nonlocal source
  need(source.count(old)==1,'Exact original138 CPP hunk '+old[:90]);source=source.replace(old,new,1);changes.append(dict(old=old,new=new))
 def line(fragment):
  rows=[v for v in lines if fragment in v];need(len(rows)==1,'One tested supplement line '+fragment);return rows[0]
 # Keep current kind0|3 backing observer and add the tested CS input branch.
 for index in(0,4,6):change(suppdeltas[index]['old'],suppdeltas[index]['new'])
 diag='unsigned ctor_fs_failure_line{},ctor_fs_failure_root{};const char*ctor_fs_failure_source{};\n'+line('void ctor_record_fs_failure(unsigned')+'\n'
 change('FsEvent fs_events[256]{};','FsEvent fs_events[256]{};\n'+diag)
 change('#include "prerequisite_observer.hpp"','#include "prerequisite_observer.hpp"\n#include "constructor_normal.hpp"')
 # Genuine current native141 physical order, with entire old guards retained.
 change('require(phase==13,"Actual chronology has13 carried roots before MFC")','require(phase==15,"Actual chronology has13 carried roots plus2 new constructors before MFC")')
 change('copy_pages(r->memory_before);','copy_pages(r->memory_before);\n'+line('const bool constructor_phase=constructor_is_root(entries[phase]);'))
 change(suppdeltas[1]['old'],suppdeltas[1]['new'])
 install=line('if(constructor_phase){const unsigned actual=dword(0x5bb4bc);')
 binding=suppdeltas[2]['new'][:-len(suppdeltas[2]['old'])]
 need(suppdeltas[2]['new'].endswith(suppdeltas[2]['old']),'Named binding exact additive prefix')
 change('            if(mfc_phase){named_IAT(true);connected_patch_sources(true);}',binding+install+'\n            if(mfc_phase){named_IAT(true);connected_patch_sources(true);}')
 restored=line('copy_capture(*r);if(constructor_phase)');restore=restored.split('copy_capture(*r);',1)[1].split('if(mfc_phase)',1)[0]
 change('copy_capture(*r);if(mfc_phase)','copy_capture(*r);'+restore+'if(mfc_phase)')
 collect=line('constructor_collect(phase,phase_stem);if(constructor_phase)')
 change('            if(phase<13)constructor_collect(phase,phase_stem);',collect)
 change(suppdeltas[3]['old'],suppdeltas[3]['new'])
 cs=suppdeltas[5]['new'][:-len(suppdeltas[5]['old'])];need(suppdeltas[5]['new'].endswith(suppdeltas[5]['old']),'Typed CS exact additive prefix')
 # Two identical bound guards exist in original138; choose unique export site.
 anchor='            require(registry_API_count<=256,"Bounded actualAPI ledger");out.append('
 change(anchor,cs+anchor)
 declaration=line('const std::array<unsigned,7>ctor_named_entries').split('const auto service=',1)[0]
 change('    const auto service=GetProcAddress(mfc,reinterpret_cast<LPCSTR>(1168)),mbcp=GetProcAddress(crt,"_setmbcp");',declaration+'const auto service=GetProcAddress(mfc,reinterpret_cast<LPCSTR>(1168)),mbcp=GetProcAddress(crt,"_setmbcp");')
 change('out.append("crt-api-targets.bin",registry_API_targets,sizeof(registry_API_targets));','out.append("crt-api-targets.bin",registry_API_targets,sizeof(registry_API_targets));out.append("constructor/provider-entries.bin",ctor_named_entries.data(),sizeof(ctor_named_entries));')
 change('require(*crtnext-*crtbegin==108*4,"Exact108callback vector extent");out.append("cleanup/"+std::to_string(sequence)+"/registry.bin",reinterpret_cast<void*>(*crtbegin),108*4);','require(*crtnext-*crtbegin==111*4,"Exact111callback vector extent");out.append("cleanup/"+std::to_string(sequence)+"/registry.bin",reinterpret_cast<void*>(*crtbegin),111*4);')
 cleanup=line('for(auto&v:constructor_occurrences)if(v.alive&&v.phase<entries.size()')
 change('        out.append("cleanup/"+std::to_string(sequence)+"/mixed-owner-count.bin",',cleanup+'\n        out.append("cleanup/"+std::to_string(sequence)+"/mixed-owner-count.bin",')
 # Whole extra global page comparison target, never source execution input.
 change('copy_pages(r->memory_before);','copy_pages(r->memory_before);out.append(phase_stem+"/constructor-global-before.bin",reinterpret_cast<void*>(0x5f2000),4096);')
 change('copy_capture(*r);if(constructor_phase)','copy_capture(*r);out.append(phase_stem+"/constructor-global-after.bin",reinterpret_cast<void*>(0x5f2000),4096);if(constructor_phase)')
 change('std::array<void*,161> pages','std::array<void*,176> pages')
 # Retain every old normal hook; add tested fifteen complete replay bridges.
 new=json.loads(pin(geometry/'new-FS-bindings.json').read_text());union=json.loads(pin(geometry/'fs-hook-bindings.json').read_text())
 declarations='\n'.join(f'extern "C" void {v["declared_observer"]}();\nextern "C" const unsigned fs_continue_{v["PC"]:x}={hex(v["continuation"])};'for v in new)+'\n'
 change('struct FsHook{',declarations+'struct FsHook{')
 pat=r'const std::array<FsHook,93>fs_hooks\{\{[^;]+;';match=re.search(pat,source);need(match is not None,'Actual old93 FS hook declaration')
 table='const std::array<FsHook,108>fs_hooks{{'+','.join('{'+hex(v['PC'])+','+str(len(bytes.fromhex(v['raw_bytes'])))+','+str(v['kind'])+',&'+v['declared_observer']+',{'+','.join(hex(b)for b in bytes.fromhex(v['raw_bytes']))+'}}'for v in union)+'}};';change(match[0],table)
 reverse=source
 for d in reversed(changes):need(reverse.count(d['new'])==1,'Exact CPP inverse');reverse=reverse.replace(d['new'],d['old'],1)
 need(reverse==parent,'Entire original138 CPP recovered, no weakened guards');(out/'reference.cpp').write_text(source)
 # These two tested ASM changes preserve all CPU/flags and inline CS-before.
 asm=pin(old/'reference_x86.asm').read_text();asmparent=asm
 for d in json.loads(pin(supp/'asm-changes.json').read_text()):
  need(asm.count(d['old'])==1,'Exact old reference ASM supplement');asm=asm.replace(d['old'],d['new'],1);asmchanges.append(d)
 reverse=asm
 for d in reversed(asmchanges):need(reverse.count(d['new'])==1,'Exact reference ASM inverse');reverse=reverse.replace(d['new'],d['old'],1)
 need(reverse==asmparent,'Whole inherited reference ASM retained');(out/'reference_x86.asm').write_text(asm)
 fsasm=pin(old/'fs_observer_x86.asm').read_text();oldfsasm=fsasm;donor=pin(supp/'fs_observer_x86.asm').read_text();bridges=[]
 for v in new:
  name=v['declared_observer'];m=re.search(r'PUBLIC '+name+r'\n'+name+r' PROC\n.*?'+name+r' ENDP\n',donor,re.S);need(m is not None,'Tested exact whole constructor FS replay bridge');bridges.append(m[0])
 fsdeltas=[dict(old='.code\n',new='\n'.join(f'EXTERN fs_continue_{v["PC"]:x}:DWORD'for v in new)+'\n.code\n'),dict(old='END\n',new=''.join(bridges)+'END\n')]
 for d in fsdeltas:need(fsasm.count(d['old'])==1,'One complete FS ASM additive insertion');fsasm=fsasm.replace(d['old'],d['new'],1)
 reverse=fsasm
 for d in reversed(fsdeltas):need(reverse.count(d['new'])==1,'Whole FS ASM inverse');reverse=reverse.replace(d['new'],d['old'],1)
 need(reverse==oldfsasm,'Entire old93 bridge ASM preserved');(out/'fs_observer_x86.asm').write_text(fsasm)
 cmake=pin(old/'CMakeLists.txt').read_text();need(cmake.count('api_boundaries.asm "')==1,'Existing original138 link source set');(out/'CMakeLists.txt').write_text(cmake.replace('api_boundaries.asm "','api_boundaries.asm constructor_observer_x86.asm "',1))
 # Pre-CRT reservation must cover all sparse pages before genuine DLL loaders.
 broker=pin(old/'original_broker.hpp').read_text();match=re.search(r'inline constexpr std::array<std::uint32_t,\d+> bases\{([^;]+)\};',broker);need(match is not None,'Physical original broker reservation table');bases={int(v,16)for v in match[1].split(',')};raw=(out/'pages.bin').read_bytes();n=struct.unpack_from('<I',raw,8)[0];required={struct.unpack_from('<I',raw,12+i*4104)[0]&~65535 for i in range(n)};extra=sorted(required-bases);allbases=sorted(bases|required);newtable=f'inline constexpr std::array<std::uint32_t,{len(allbases)}> bases'+'{'+','.join(hex(v)for v in allbases)+'};';(out/'original_broker.hpp').write_text(broker.replace(match[0],newtable,1))
 for name,value in [('CPP-deltas.json',changes),('reference-ASM-deltas.json',asmchanges),('FS-ASM-deltas.json',fsdeltas),('broker-delta.json',dict(old=match[0],new=newtable,new_reservation_bases=extra))]:(out/name).write_text(json.dumps(value,indent=2)+'\n')
 # Explicit whole original138 guard retention, including complete family counts.
 guards=['container_allocation_count==5','fs_allocation_count==10','registry_API_count<=256','capacity<=512','HeapReAlloc API-return backing','widget_fs_event_count<=2048','fps_count<=8','Same-worker whole initialized MFC page phase carry']
 for guard in guards:need(guard in parent and guard in source,'Whole retained original138 gate '+guard)
 for p in out.iterdir():pin(p)
 pin(__file__);pin(R/'reports/m4-original141/patch-inventory-r1/report.json','fce4a4f45872ea36d21333b19861e3316c6ec31ca6818a6ccdd9f2ab2dc671cc')
 report=dict(passed=True,prepared_only=True,source_composed=True,CPP_deltas=len(changes),reference_ASM_deltas=len(asmchanges),FS_ASM_deltas=len(fsdeltas),exact_CPP_inverse=True,exact_reference_ASM_inverse=True,exact_FS_ASM_inverse=True,whole_original138_guards_retained=guards,root_count=141,sequences=6,phases=846,callback_count=111,Record_bytes=356992,new_constructor_input_supplement_retained=True,source_model_AFTER_seed=False,physical_compiled_observer_attribution_pending=True,exact_source_computed_PUSHFD_shadow_review_pending=True,exact_CRT_and_constructor_IAT_fullpage_transition_validator_pending=True,build_admitted=False,build_executed=False,worker_admitted=False,worker_executed=False,canonical_reader_opened=False,initializer_credit=0,files=files)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');(out/'pins.json').write_text(json.dumps(dict(files={**files,str((out/'report.json').resolve()):sha(out/'report.json')}),indent=2)+'\n');print(json.dumps(dict(path=str(out/'report.json'),sha256=sha(out/'report.json'),CPP_deltas=len(changes))))
if __name__=='__main__':main()
