"""Physical native State projector authority; no source/model/readers."""
from pathlib import Path
import hashlib,json,ast,difflib
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-startup141-paired/native-constructor-source-preparation-r4';assert not out.exists();out.mkdir();files={}
 p=R/'tools/m4-startup141-paired/constructor_native36_source141_v3.py';q=p.with_name('constructor_native36_source141_v4.py');assert not q.exists();a=p.read_text();b=a;changes=[]
 def edit(old,new):
  nonlocal b
  assert b.count(old)==1,(old,b.count(old));b=b.replace(old,new);changes.append((old,new))
 anchor="  sys.addaudithook(input_audit)\n"
 add="""  executed=receipt['executed_lineage'];build=json.loads(pin(executed['build'],executed['build_sha256']).read_bytes());joint_preparation=json.loads(pin(executed['joint_preparation'],executed['joint_preparation_sha256']).read_bytes());need(build['passed']and joint_preparation['passed']and build['preparation_sha256']==executed['joint_preparation_sha256'],'Exact current compiled native ENV producer lineage')
  projector_receipt=json.loads(pin(R/'reports/m4-startup141-paired/native-constructor-source-preparation-r4/projector-contract.json').read_bytes());need(projector_receipt['joint_preparation_sha256']==executed['joint_preparation_sha256']and projector_receipt['native_build_sha256']==executed['build_sha256'],'Physically reviewed same current protocol/remill layout')
  for dep,h in projector_receipt['files'].items():pin(dep,h)
  ENV=load('tools/m4-startup141-paired/native_ENV28_v1.py','current_native_State_ENV_projector')
"""
 edit(anchor,anchor+add)
 old="     need(len(bytes.fromhex(inp['BEFORE_ENV28_hex']))==28 and len(inp['APIs'])==5 and all(len(bytes.fromhex(v['actual_API_before_FX512_hex']))==512 and v['actual_API_before_FX512_hex']==v['actual_API_after_FX512_hex']for v in inp['APIs']),'Complete actual all5 API FX preservation proves source noFP seam scope')\n     result['source_computed_ENV28_hex']=inp['BEFORE_ENV28_hex'];result['source_ENV_input_cut']='Genuine own phase BEFORE28 plus complete integer-only literal path and whole5 actual API FX conservation; no endpoint input'"
 new="""     need(len(bytes.fromhex(inp['BEFORE_ENV28_hex']))==28 and len(inp['APIs'])==5 and all(len(bytes.fromhex(v['actual_API_before_FX512_hex']))==512 and v['actual_API_before_FX512_hex']==v['actual_API_after_FX512_hex']for v in inp['APIs']),'Complete actual all5 API FX conservation corroboration only; not an ENV equality theorem')
     need(ENV.project(bytes.fromhex(inp['BEFORE_State_hex'])).hex()==inp['BEFORE_ENV28_hex'],'Actual ownBEFORE28 equals physical deterministic native State projector')
     result['source_computed_ENV28_hex']=ENV.project(bytes.fromhex(result['source_computed_State_hex'])).hex();result['source_ENV_input_cut']='Entire literal SOURCE-computed State3504 projected by exact current native protocol, including metadata intentionally zeroed in observed FX6..23; hardware/original FNSTENV not inferred'
"""
 edit(old,new)
 edit('source_ENV28_derived_from_BEFORE=True,actual_all5_API_FX_conserved=True','source_ENV28_derived_from_BEFORE=True,source_ENV28_projected_from_entire_source_computed_State=True,actual_all5_API_FX_conserved=True,API_FX_implies_hardware_ENV_equality_claim=False')
 ast.parse(b);q.write_text(b);back=b
 for old,new in reversed(changes):assert back.count(new)==1;back=back.replace(new,old)
 assert back==a;before=a.splitlines(True);after=b.splitlines(True);d=[]
 for tag,i,j,k,l in difflib.SequenceMatcher(None,before,after,autojunk=False).get_opcodes():
  if tag!='equal':d.append(dict(parent_start=i,parent_stop=j,child_start=k,child_stop=l,parent=''.join(before[i:j]),child=''.join(after[k:l])))
 (out/'inverse.json').write_text(json.dumps(d,indent=2)+'\n')
 proto=R/'reports/m4-startup141-runway/preparation-r3/joint_protocol.hpp';layout=R/'local/tools/remill-v6.0.1/remill-6.0.1/include/remill/Arch/X86/Runtime/State.h';source=proto.read_text();st=layout.read_text();assert 'std::memset(fx.data()+6,0,18);'in source
 for statement in ['put(0,0xffff0000U|s.x87.fxsave.cwd.flat);put(4,0xffff0000U|sw);put(8,0xffffffffU);','put(12,s.x87.fxsave.ip);put(16,s.x87.fxsave.cs.flat|(std::uint32_t{s.x87.fxsave.fop}<<16));put(20,s.x87.fxsave.dp);put(24,0xffff0000U|s.x87.fxsave.ds.flat);']:assert statement in source
 for statement in ['FPUStatusFlags sw;  // 24 bytes','uint8_t _padding[8]; // 8 bytes','FPU x87;  // 512 bytes','uint32_t ip;  // Offset in segment of last non-control FPU instruction.','uint32_t dp;  // Operand address.']:assert statement in st
 native=R/'reports/m4-startup141-source/combined-source-provider-r6/report.json';N=json.loads(native.read_bytes());assert N['passed'];lineage=N['executed_lineage'];joint=json.loads(Path(lineage['joint_preparation']).read_bytes());build=json.loads(Path(lineage['build']).read_bytes());assert joint['passed']and build['passed']and joint['files'][str(proto)]==sha(proto)
 # Header/layout physical identities must belong to current compiled lineage;
 # compile manifests may use real workspace paths for Remill include files.
 assert any(str(Path(k).resolve())==str(layout.resolve())and h==sha(layout)for k,h in build['files'].items())or any(str(Path(k).resolve())==str(layout.resolve())and h==sha(layout)for k,h in joint['files'].items()),'Actual compiler layout dependency must be physically bound'
 deps=[R/'tools/m4-startup141-paired/native_ENV28_v1.py',proto,layout,Path(lineage['joint_preparation']),Path(lineage['build']),native]
 contract=dict(joint_preparation_sha256=lineage['joint_preparation_sha256'],native_build_sha256=lineage['build_sha256'],source_State_bytes=3504,source_x87_offset=2768,source_sw_offset=2736,observed_FX_metadata_zero_span=[6,24],projector_uses_entire_computed_State=True,hardware_ENV_equality_from_FX_claim=False,files={str(x.resolve()):sha(x)for x in deps})
 c=out/'projector-contract.json';c.write_text(json.dumps(contract,indent=2)+'\n')
 for x in[p,q,out/'inverse.json',c,*deps,Path(__file__).resolve()]:files[str(x.resolve())]=sha(x)
 r=out/'report.json';r.write_text(json.dumps(dict(prepared_only=True,imports_executed=False,source_execution=False,canonical_reader_opened=False,ordinary_export_reader_opened=False,initializer_credit=0,exact_whole_parent_inverse=True,inverse_hunks=len(d),physical_native_ENV_projector_bound=True,full_computed_State_required=True,raw_FNStENV_from_API_FX_inferred=False,previous_checkpoint_nonphase_owner_carry_proven=False,files=files),indent=2)+'\n');print(json.dumps(dict(path=str(r),sha256=sha(r))))
if __name__=='__main__':main()
