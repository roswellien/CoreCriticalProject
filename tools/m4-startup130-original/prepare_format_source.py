"""Derive the current genuine four-format source comparer without opening data."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2]
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main():
 old=R/'tools/m4-mixed-format-original/compare_source_v8.py';new=R/'tools/m4-startup130-original/format_source.py';need(not new.exists(),'Fresh derivative')
 body=old.read_text();hunks=[]
 def one(a,b):
  nonlocal body
  need(body.count(a)==1,'Exactly one hunk '+a[:100]);body=body.replace(a,b);hunks.append(dict(old=a,new=b))
 one("if path.suffix.lower()=='.mwb':need(path.is_relative_to(R/'reports/m4-mixed-format-original/trace-execution-r1'),'No inherited/native capture in bounded source audit')","if path.suffix.lower()=='.mwb':need(path.is_relative_to(R/'reports/m4-startup130-original/execution-r2'),'Only the one current-original130 archive')")
 one('def main(name):','def main(name,shared_reader):')
 one("out=R/'reports/m4-mixed-format-original'/name","out=R/'reports/m4-startup130-original'/name")
 a=body.index("        original=R/'reports/m4-mixed-format-original/trace-validation-r1'");b=body.index("        M=load(",a)
 setup="""        validation=read(R/'reports/m4-startup130-original/validation-r2/report.json','91a3ca940214636b0d4c1a08c7ccf503a5c06127a3af4b26fdad50c876f1ffca');need(validation['passed'],'Fresh original130 structural evidence')
        boundaries=[dict(x,cpu=x['CPU'])for x in read(R/'reports/m4-startup130-original/validation-r2/fresh-cdecl.json',validation['files'][str((R/'reports/m4-startup130-original/validation-r2/fresh-cdecl.json').resolve())])]
        owner_rows=read(R/'reports/m4-startup130-original/validation-r2/fresh-format_owners.json',validation['files'][str((R/'reports/m4-startup130-original/validation-r2/fresh-format_owners.json').resolve())])
        owners=[dict(x,pointer=x['meta'][5],request=x['meta'][4],capacity=x['meta'][6],API_index=x['meta'][7])for x in owner_rows]
        execution=read(Path(validation['execution_path'])/'report.json',validation['execution_sha256']);build=read(validation['build_path'],validation['build_sha256']);pin(build['worker'],build['worker_sha256']);preparation=read(Path(validation['preparation_path'])/'report.json',validation['preparation_sha256'])
"""
 hunks.append(dict(old=body[a:b],new=setup));body=body[:a]+setup+body[b:]
 one("roots=game['roots'];G=load", "roots=read(R/'reports/m4-formatting-source/normal-contracts-r1/normal-contracts.json')['roots']+game['roots'];format_contracts=read(R/'reports/m4-formatting-frontier/recovery-r1/instruction-contracts.json');G=load")
 one("for row in allocator['instructions']+game['instructions']:","for row in allocator['instructions']+game['instructions']+format_contracts['instructions']:\n            if row['pc']>=0x78000000 and row['pc']in provider_program:continue")
 one("bundle=D.DirectSet(execution['original_capture'],pin)","bundle=shared_reader;need(Path(bundle.path).resolve()==Path(execution['original_capture']).resolve(),'One authenticated current-original130 session')")
 a=body.index("        mixed_owners=read(Path(validation['normal_validation_path'])");b=body.index("            raw=bundle.data(",a)
 setup="""        full_mixed_owners=read(R/'reports/m4-startup130-original/validation-r2/fresh-mixed_owners.json',validation['files'][str((R/'reports/m4-startup130-original/validation-r2/fresh-mixed_owners.json').resolve())])
        full_CP=read(R/'reports/m4-startup130-original/validation-r2/fresh-mixed_CP.json',validation['files'][str((R/'reports/m4-startup130-original/validation-r2/fresh-mixed_CP.json').resolve())])
        for sequence in range(6):
         for root in roots:
            phase=next(i for i,x in enumerate(preparation['selected_order'])if x['entry']==root['entry'])
            phase_boundaries=[x for x in boundaries if x['sequence']==sequence and x['root']==root['entry']];need(len(phase_boundaries)==6,'Exactly current cdecl boundaries')
            selected_owners=[x for x in owners if x['sequence']==sequence and x['root']==root['entry']];need(len(selected_owners)==1,'Exactly current formatter owner');owner=selected_owners[0]
            mixed_owners=[]
            for x in full_mixed_owners:
             if x['sequence']!=sequence or root['entry']!=0x4e1ca0:continue
             m=x['meta'];mixed_owners.append(dict(x,pointer=m[7],source_request=m[4],capacity=m[8],API_index=m[6],CALL_pc=m[3]))
            cp_events=[x for x in full_CP if x['sequence']==sequence and root['entry']==0x4e1ca0]
            fs_raw=bundle.data(f'phase/{sequence}/{phase}/fs-events.bin');fs_events=[]
            for offset in range(0,len(fs_raw),1216):
             b=fs_raw[offset:offset+1216];h=list(u(b,0,8));fs_events.append(dict(PC=h[2],kind=h[3],header=h,CPU_before=list(u(b,32,10)),record_before_hex=b[112:124].hex(),FX_before_hex=b[136:648].hex(),ENV_before_hex=b[1160:1188].hex()))
"""
 hunks.append(dict(old=body[a:b],new=setup));body=body[:a]+setup+body[b:]
 # Preserve current sequence in every logical original record access.
 body=body.replace("f'phase/0/{phase}","f'phase/{sequence}/{phase}")
 one("first=next(x for x in boundaries if x['phase']==phase and x['kind']==0);memory[0x7ffde000]=bytearray(struct.pack('<I',fs_events[0]['header'][4]))", "if fs_events:memory[0x7ffde000]=bytearray(struct.pack('<I',fs_events[0]['header'][4]))")
 one("owner=owners[phase];literal=[];imports=[];api=[];boundary_index=[0];cp_index=[0];fs_index=[0];phase_boundaries=[x for x in boundaries if x['phase']==phase];boundary_PCs=", "literal=[];imports=[];api=[];boundary_index=[0];cp_index=[0];fs_index=[0];boundary_PCs=")
 one("if address!=0x7ffde000 or source_pc>=0x78000000:return","if address!=0x7ffde000:return")
 one("if actual['owned_hex']:eq(self.bytes(owner['pointer'],owner['capacity']).hex(),actual['owned_hex'],'Entire actual capacity at source API boundary')","eq(raw[2164:2192].hex(),actual['ENV28_hex'],'Entire carried source ENV at cdecl boundary')\n                        if actual['owned_hex']:eq(self.bytes(owner['pointer'],owner['capacity']).hex(),actual['owned_hex'],'Entire actual capacity at source API boundary')")
 a=body.index("                    before=list(self.projected_cpu());begin=len(self.accesses);preimage=");b=body.index("            machine=Prefix(",a)
 newstep="""                    before=dict(getattr(self,'undefined_flag_domain',{}));after=F.advance(self,self.program[pc],before)
                    consumed={'je':('ZF',),'jne':('ZF',),'ja':('CF','ZF'),'jae':('CF',),'jb':('CF',),'jbe':('CF','ZF'),'jg':('ZF','SF','OF'),'jge':('SF','OF'),'jl':('SF','OF'),'jle':('ZF','SF','OF'),'js':('SF',),'jns':('SF',),'jo':('OF',),'jno':('OF',),'adc':('CF',),'sbb':('CF',),'scasb':('DF',)}.get(self.program[pc]['mnemonic'],())
                    need(not set(consumed)&set(before),'No undefined source control input');result=super().step();self.undefined_flag_domain=after;return result
"""
 hunks.append(dict(old=body[a:b],new=newstep));body=body[:a]+newstep+body[b:]
 one("need(boundary_index[0]==6 and len(imports)==5 and len(api)==6 and cp_index[0]==6 and fs_index[0]==6 and len(retained_owners)==4,'All exact cdecl/CP/FS/API witnesses exhausted')", "expected_cp=6 if root['entry']==0x4e1ca0 else 0;expected_owners=4 if expected_cp else 1;need(boundary_index[0]==6 and len(imports)==(5 if expected_cp else 3)and len(api)==expected_owners+(2 if expected_cp else 0)and cp_index[0]==expected_cp and fs_index[0]==len(fs_events)and len(retained_owners)==expected_owners,'Every genuine current cdecl/CP/FS/API occurrence exhausted')")
 # Genuine complete CRT AFTER pages contain the separate registration suffix.
 # Its only ordinary table change is derived from literal _onexit cursor+4;
 # the callback vector is related from previous whole genuine registry backing.
 a=body.index("            actual=[x for x in trace if x['phase']==phase]");b=body.index("        need(counts['literal_actual_provider_instructions']==797",a)
 tail="""            eq([x['index']for x in machine.output_dispatches],[1,7,1,7],'Literal default narrow table dispatches')
            current_next=u(machine.bytes(0x78037888,4))[0];current_begin=u(machine.bytes(0x7803788c,4))[0]
            previous=bundle.data(f'phase/{sequence}/{phase-1}.bin');prevmeta=u(previous,356464,4);aftermeta=u(raw,356464,4)
            need(prevmeta[0]==current_begin and prevmeta[1]==current_next and aftermeta[0]==current_begin and aftermeta[1]==current_next+4 and prevmeta[2]==aftermeta[2] and current_next-current_begin+4<=prevmeta[2],'Separate actual original registry suffix takes the literal no-growth append domain')
            expected_vector=bytearray(previous[356480:356480+prevmeta[2]]);struct.pack_into('<I',expected_vector,current_next-current_begin,root['registration']['callback']);eq(bytes(expected_vector),raw[356480:356480+aftermeta[2]],'Whole genuine registry backing from preceding carried BEFORE plus one physical callback store')
            for page,protect,type_ in meta:
                predicted=bytearray(machine.bytes(page,4096))
                if page==0x78037000:struct.pack_into('<I',predicted,0x888,current_next+4)
                eq(bytes(predicted),bundle.data(f'phase/{sequence}/{phase}/CRT-image/after/{page}.bin'),'Whole original CRT source prefix plus separate literal registration cursor store '+hex(page));counts['whole_original_CRT_prefix_and_registration_pages']+=1
            source_owners=[]
            for ai,o in retained_owners.items():
                source_owners.append(dict(o,source_final_hex=machine.bytes(o['pointer'],o['capacity']).hex(),source_owned_accesses=[list(a)for a in machine.accesses if o['pointer']<=a[1]<o['pointer']+o['capacity']]))
            results.append(dict(sequence=sequence,phase=phase,root=root['entry'],source_PCs=machine.PCs,source_accesses=machine.accesses,import_projections=imports,API_inputs=api,dispatches=machine.output_dispatches,string_iterations=machine.string_iterations,object_hex=machine.bytes(root['object'],root['object_extent']).hex(),owner=dict(owner,source_final_hex=machine.bytes(owner['pointer'],owner['capacity']).hex()),all_owners=source_owners,mixed_owners=[x for x in source_owners if x['CALL_pc']!=0x4deab1],FS_events=fs_events,original_boundary_joins=phase_boundaries,original_CP_joins=cp_events,registration_suffix=dict(before_begin=current_begin,before_next=current_next,after_next=current_next+4,callback=root['registration']['callback'],literal_cursor_store_PC=0x78004a69,literal_callback_store_PC=0x78004a67,whole_vector_source_derived=True,full_registration_provider_CPU_executed_by_model=False),no_post_source_seed=True));api_inputs.extend(api);counts['literal_constructor_prefixes']+=1
            print(json.dumps(dict(sequence=sequence,root=hex(root['entry']),source_instructions=len(machine.PCs),passed=True)),flush=True)
"""
 hunks.append(dict(old=body[a:b],new=tail));body=body[:a]+tail+body[b:]
 one("need(counts['literal_actual_provider_instructions']==797 and counts['whole_projected_CPU_sides']==1594,'Complete measured original provider trace extent');passed=True", "need(counts['literal_constructor_prefixes']==24 and counts['whole_cdecl_CPU_FX_frame_capacity_joins']==144 and counts['whole_literal_owned_byteflows']==42 and counts['literal_actual_CP_CPU_FX_ENV_frame_CS_joins']==36,'All24 current original prefixes/full42owner byteflows/144cdecl/36CP boundaries');passed=True")
 one("if bundle:bundle.close();bundle.entries.clear();bundle.bundles.clear()", "# Aggregate retains and closes the one shared capture exactly once.\n        bundle=None")
 one("original_game_FS_observations=6,allocator_FS_frames_literal_only=True,scope='Literal mixed constructor prefix including MFC, two nested FS frames, balanced initialized Lockit and797 genuine narrow provider instructions from untouched phase BEFORE. Four actual HeapAlloc initial/volatile inputs and two actual CS API volatile/output observations are finite external inputs; no source postRET or AFTER memory seed.'", "original_game_FS_observations=36,allocator_FS_frames_literal_only=False,scope='All24 current original130 literal formatter4 prefixes from each untouched whole46-page BEFORE/current64CRT pages, actual initial allocator backings/finite Win32 volatile inputs; six mixed balancedCP/nestedFS paths. Separate no-growth registry cursor/vector relation from genuine preceding BEFORE and literal two stores; full registration provider CPU remains outside this prefix proof.'")
 one("reader_closed=True", "reader_scope='Borrowed one authenticated current-original130 session; aggregate closure required'")
 one("if __name__=='__main__':main(sys.argv[1])", "if __name__=='__main__':raise SystemExit('Use current_source.py for one shared reader')")
 # Authored indentation change is explicit: sequence/root loop has two levels,
 # and every original body operation remains within the same root block.
 new.write_text(body)
 out=R/'reports/m4-startup130-original/format-source-preparation-r1';need(not out.exists(),'Fresh output');out.mkdir(parents=True);pins={str(p.resolve()):sha(p)for p in [old,new,Path(__file__)]};p=out/'hunks.json';p.write_text(json.dumps(hunks,indent=2)+'\n');pins[str(p.resolve())]=sha(p)
 report=dict(passed=True,scope='Unexecuted current-original13024prefix literal comparer; one sharedreader only',files=pins,hunks=len(hunks),capture_reader_opened=False,executed=False);p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(p))))
if __name__=='__main__':main()
