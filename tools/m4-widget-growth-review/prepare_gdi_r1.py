"""Unexecuted preparation and ordinary physical PE smoke review only."""
from pathlib import Path
import ast,hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];PINS={}
def need(v,m):
 if not v:raise ValueError(m)
def raw(p):
 p=Path(p).resolve();b=p.read_bytes();PINS[str(p)]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};return b
def main(out):
 out=Path(out).resolve();need(not out.exists(),'Immutable additive preparation');out.mkdir(parents=True)
 module=R/'tools/m4-widget-growth-review/gdi_identity.py';text=raw(module).decode();tree=ast.parse(text);compile(text,str(module),'exec')
 f=next(v for v in tree.body if isinstance(v,ast.FunctionDef) and v.name=='verify');need([v.arg for v in f.args.args]==['getter','pin'] and [v.arg for v in f.args.kwonlyargs]==['prefix','source_records','manual_records','logical_names','expected_thread'],'Exact caller-owned pure verifier signature')
 sp=importlib.util.spec_from_file_location('ordinary_gdi_identity_preparation',module);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
 helper=R/'reports/m4-fps-native/connected-component-preparation-r4/gdi_provider_witness.hpp';cpp=helper.with_name('component.cpp');header=helper.with_name('component.hpp');asm=helper.with_name('native_api.s')
 h=raw(helper).decode();c=raw(cpp).decode();raw(header);raw(asm)
 need('std::array<std::uint64_t,9>w{1,kind,address,reinterpret_cast<std::uintptr_t>(owner),base,mbi.RegionSize,mbi.State,mbi.Protect,mbi.Type}' in h,'Exact recorded actual native provider 9Q layout')
 need('std::array<std::uint64_t,11>identity_call{1,serial,index,0,root->root,e.pc,f.frame,instance,reinterpret_cast<std::uintptr_t>(providers[index]),thread,rec.hardware.after.rax}' in c,'Exact actual source native call11Q layout')
 need('std::array<std::uint64_t,11>identity_call{1,serial,1,1,it->root,0,0,it->instance,reinterpret_cast<std::uintptr_t>(providers[1]),thread,hardware.after.rax}' in c,'Exact actual manual native call11Q layout')
 need('rec.metadata={1,root->root,e.pc,index,GDI_cursor,f.frame,f.ret,e.argc,instance,result,rec.hardware.after.rax,reinterpret_cast<std::uintptr_t>(providers[index]),thread,error_before,error_after,generation}' in c,'Whole actual source ApiRecord metadata16Q relation')
 raw(R/'tools/m4-mfc1168-native/verify_resource_fixture.py');raw(R/'tools/m4-mfc1168-native/resource_witness.hpp');raw(R/'tools/m4-tree-review/amd64_pe.py')
 modules=[]
 for name in ['gdi32.dll','gdi32full.dll','win32u.dll']:
  p=Path('C:/Windows/System32')/name;data=raw(p);pe=m.PhysicalPE(data);names={}
  for n in m.NAMES:
   row=pe.exports.get(n);names[n]=row
   if row and row['forwarder'] is None:
    entry,relocs=pe.entry64(row['rva'],pe.base);need(len(entry)==64,'Whole preferred-base physical entry64 parser smoke');names[n]=dict(row,physical_preferred_base_entry64=entry.hex(),affected_DIR64_relocations=relocs)
  modules.append({'path':str(p.resolve()),'sha256':hashlib.sha256(data).hexdigest(),'preferred_base':pe.base,'image_bytes':pe.image_bytes,'named_export_count':len(pe.exports),'complete_DIR64_rows':len(pe.relocations),'requested_export_rows':names,'actual_runtime_target_observed':False})
 need(all(modules[0]['requested_export_rows'][n] and modules[0]['requested_export_rows'][n]['forwarder'] is None for n in m.NAMES),'Current physical GDI32 three direct requested exports')
 detail=out/'physical-provider-preparation.json';detail.write_text(json.dumps(modules,indent=2)+'\n');raw(detail);raw(__file__);raw(sys.executable)
 report={'passed':True,'scope':'Pure unexecuted reusable strict GDI identity verifier preparation plus ordinary current physical AMD64 exports/DIR64 parser smoke; no native-call acceptance','module':str(module),'module_sha256':hashlib.sha256(module.read_bytes()).hexdigest(),'entrypoint':'verify(getter, pin, *, prefix, source_records, manual_records, logical_names, expected_thread=None)','logical_getter_contract':'Exact bytes for canonical whole caller-owned logical records; complete inventory is mandatory and all identity rows are consumed','pin_contract':'pin(Path, expected_sha256) records complete ordinary physical-file reads, called at first whole module read and stable completion','source_records_layout':{'bytes':1488,'metadata16Q_offset':0,'CPU_before40_offset':128,'CPU_after40_offset':168,'arguments14I_offset':208,'frame64_offset':264,'ApiHardware1152_offset':336,'actual_native_RAX_offset':912},'manual_records_layout':'Ordered pairs (complete64-byte 8Q row, complete1152-byte actual native hardware); full RCX font argument and actual RAX joins','identity_layout':'9Q version/kind/target/owner/regionBase/regionBytes/state/protect/type; complete four before and four after rows plus call11Q','whole_current_physical_provider_files':3,'current_GDI32_direct_requested_exports':3,'pure_parser_compile_succeeded':True,'native_worker_executed':False,'actual_logical_capture_read':False,'archive_reader_opened':False,'actual_native_provider_acceptance':False,'different_named_aliases_admitted':False,'origin_forwarder_chain_verified':False,'source_output_equivalence_claimed':False,'font_lifetime_closure_claimed':False,'initializer_credit':0,'forwarder_scope':'Authenticates exact requested non-forwarded final owning export. Same-name final owner can be upstream-forwarded, but origin module/forwarder-chain identity is not captured and is not claimed. A different NtGdi/other alias fails closed.','files':PINS}
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'passed':True,'actual_native_acceptance':False}))
if __name__=='__main__':main(sys.argv[1])
