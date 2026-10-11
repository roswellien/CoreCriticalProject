"""Seal the completed bounded human review of startup124 documentation."""
from pathlib import Path
import hashlib,json,re,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def main(name):
    out=ROOT/'reports/m4-lockit-review'/name;assert not out.exists();out.mkdir(parents=True)
    files={}
    def pin(relative):
        path=(ROOT/relative).resolve();raw=path.read_bytes();assert len(raw)<=4*1024*1024;files[str(path)]=hashlib.sha256(raw).hexdigest();return raw
    documents={path:pin(path).decode('utf-8')for path in(
        'docs/m4-progress-startup124.md','docs/m4-execution-plan-r10.md','docs/project-milestones-r10.md',
        'README.md','docs/project-milestones.md','docs/m4-lockit-native-candidate124.md')}
    spot=json.loads(pin('reports/m4-lockit-review/acceptance-spotcheck-r1/report.json'))
    assert spot['passed']and spot['counts']['accepted_inventory_roots']==124 and spot['counts']['remaining_inventory_roots']==20
    accepted=json.loads(pin('reports/m4-joint-startup124-root/acceptance-r1/report.json'))
    assert accepted['passed']and not accepted['whole_M4_complete']and not accepted['native_game_launch_complete']
    progress=documents['docs/m4-progress-startup124.md'];plan=documents['docs/m4-execution-plan-r10.md'];candidate=documents['docs/m4-lockit-native-candidate124.md']
    assert '**124/144' in progress and '**20 inventory roots remaining**'in progress and '86.1% of the initializer inventory'in progress
    assert 'Across both native levels'in progress and 'twelve sequences'in progress and '96 Lockit'in progress
    assert 'Stored callbacks are not executed'in progress and 'Native MSVCP'in progress and 'DllMain, lazy initialization, contention and Sleep paths remain outside'in progress
    assert 'before its\nepilogue'in progress and 'pre-RET'in progress and 'without a blanket cross-branch equality claim'in progress
    assert '78 live ordinary owners'in progress and 'five real critical sections'in progress and '392' in progress
    assert 'Full M4'in progress and 'native\nTraining remain open'in progress
    assert 'nine register-import'in candidate and 'nine registration-import'not in candidate
    accounting=json.loads(pin('reports/m4-lockit-source/reader-efficiency-plan-r2/report.json'))['accounting']
    assert accounting['both_native_levels_one_consumer_open_hash_bytes']==109321435608 and accounting['three_native_consumers_open_hash_bytes']==327964306824
    assert f"{accounting['both_native_levels_one_consumer_open_hash_GiB']:.2f} GiB"in plan and f"{accounting['three_native_consumers_open_hash_GiB']:.2f} GiB"in plan
    assert 'calculated hash-input bytes, not measured disk traffic'in plan and 'elapsed speedup'in plan and 'mutation controls'in plan and 'complete final sealing'in plan
    assert 'no unsupported completion date'in plan and 'Initializer percentage is not a whole-project completion'in plan
    main=documents['docs/project-milestones.md']
    for token in ('Vulkan','normal maps','Mipmaps and texture filtering','Anti-aliasing','Optional resolution upscaling','motion vectors','VRAM'):
        assert token in main
    reviewed_local_links=0
    for relative,text in documents.items():
        for target in re.findall(r'\]\(([^)]+)\)',text):
            if target.startswith(('http:','https:','app:','codex:','#')):continue
            path=(ROOT/relative).parent/target.split('#',1)[0]
            assert path.exists(),('Existing local documentation link',relative,target)
            reviewed_local_links+=1
    report=dict(passed=True,scope='Independent bounded documentation/count/scope review after sealed124-root acceptance; scoped README/main milestone diffs reviewed and graphics workstream unchanged',
        counts=dict(accepted_inventory_roots=124,remaining_inventory_roots=20,total_inventory_roots=144,acceptance_gates=39,acceptance_predicates=324,
                    combined_native_Lockit_pairs=96,callbacks_per_sequence=96,MFC_owners_per_sequence=58,ordinary_owners_per_sequence=78,
                    whole_source_pages=43,actual_linked_inputs_per_level=392,reviewed_document_files=6,reviewed_existing_local_links=reviewed_local_links),
        inventory_percentage_is_project_completion=False,whole_M4_complete=False,native_game_launch_complete=False,
        native_DllMain_credit=False,callback_execution_credit=False,volatile_original_API_equivalence_claimed=False,
        reader_hash_input_accounting_calculated=True,reader_speedup_measured=False,
        native_capture_archive_opened=False,original_capture_archive_opened=False,physical_dependency_closure_rehashed=False,
        concrete_wording_correction_applied='96 Lockit/FS/publication pairs and288 carries are combined across twelve O0/O2 sequences',
        graphics_content_review='The main M7 row and complete sampling/mipmap/AA/upscaling/asset workstream are unchanged in the scoped Git diff; cinematic and widescreen documents are outside these edits.',files=files)
    path=out/'report.json';raw=(json.dumps(report,indent=2)+'\n').encode();path.write_bytes(raw);print(json.dumps(dict(passed=True,report_sha256=hashlib.sha256(raw).hexdigest(),counts=report['counts'])))
if __name__=='__main__':main(sys.argv[1])
