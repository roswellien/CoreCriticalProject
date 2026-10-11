"""Retain first-writer physical checks with the measured-capacity repair."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def main(name):
    out=R/'reports/m4-tree-review'/name;assert not out.exists();out.mkdir(parents=True)
    p=R/'tools/m4-tree-review/review_widget6_prelaunch_v5.py';text=p.read_text();changes=[]
    def change(a,b,count=1):
        nonlocal text
        assert text.count(a)==count,(a,text.count(a));text=text.replace(a,b);changes.append(dict(before=a,after=b,count=count))
    change('0dc60d24b135d33b11d336db0ccce7a37c0a07ee676d63742f3413d722861a54','209b73cd3d16280ca4173ec3f0ac0186681b4415a2b8b81c79aa46a634e96abb',2)
    change('4c4c5210af1388dc4721c39e4b70cc7505205863bd5015d6d89bd00fb5da1f76','004b2a21b58d1ac10d3b96a8726e092b8ada0fac2855f8ef358b16cea0f087bb',2)
    n=text.count('fixture-preparation-r10');change('fixture-preparation-r10','fixture-preparation-r12',n)
    n=text.count('fixture-build-r10');change('fixture-build-r10','fixture-build-r11',n)
    change("        for row in service['source_relations']:", "        for row in service['source_relations']:")
    marker="        component = pin(base / 'preparation-r3/component.cpp').read_text()"
    extra='''        corrected = receipt(base / 'service-preparation-r3/report.json', '3fdc66a791fd81437fe56500b2d3a8340e45149fd97a4980add749135a9845fd')
        old_guard = 'require(allocation&&allocation->guest==begin&&allocation->native&&allocation->mapped&&next>=begin&&std::uint64_t(next)+4<=std::uint64_t(begin)+allocation->capacity,"Current owned source producer callback capacity");'
        new_guard = 'require(allocation&&allocation->guest==begin&&allocation->native&&allocation->mapped&&!allocation->pending&&next>=begin&&std::uint64_t(next)+4<=std::uint64_t(begin)+allocation->extent,"Current live producer full-byte extent before literal msize");'
        old_publication = 'require(r.memory().load<unsigned>({0x7803788c})==begin&&r.memory().load<unsigned>({0x78037888})==next+4&&r.memory().load<unsigned>({next})==callback,"Actual source-owned registry publication and complete capacity carry");'
        new_publication = 'require(binding->allocation_for(begin)==allocation&&allocation->native&&allocation->mapped&&!allocation->pending&&allocation->capacity&&allocation->extent==allocation->capacity&&std::uint64_t(next)+4<=std::uint64_t(begin)+allocation->capacity&&r.memory().load<unsigned>({0x7803788c})==begin&&r.memory().load<unsigned>({0x78037888})==next+4&&r.memory().load<unsigned>({next})==callback,"Actual literal msize capacity and source-owned registry publication");'
        for relation in corrected['source_relations']:
            before=pin(relation['parent'],relation['parent_sha256']).read_text();after=pin(relation['child'],relation['child_sha256']).read_text()
            if Path(relation['child']).name=='session_impl.inc':
                assert before.count(old_guard)==before.count(old_publication)==1
                assert before.replace(old_guard,new_guard).replace(old_publication,new_publication)==after
            else:assert before==after
            counts['whole_corrected_service_source_relations']+=1
        assert corrected['changed_files']==['session_impl.inc']and corrected['unchanged_files']==70
        assert corrected['extra_provider_API_calls']==0 and corrected['actual_literal_msize_capacity_required_after_provider']
        assert prep['service_preparation_sha256']=='3fdc66a791fd81437fe56500b2d3a8340e45149fd97a4980add749135a9845fd'
        add=add.replace(old_guard,new_guard).replace(old_publication,new_publication)
'''
    change(marker,extra+marker)
    change('?A0x948FD806','?A0xB08EDCB8',2)
    change('run_fixture_v3.py','run_fixture_v4.py')
    change('fb3bd548344283e7478467eca613c0d8cf69df4e9d54cd3f5e088784cf37bb78','5d64892010fb6c9f44b22800ec2c2e91561df90664a4aac9c024410bdbbb198a')
    ast.parse(text);q=R/'tools/m4-tree-review/review_widget6_prelaunch_v6.py';assert not q.exists();q.write_text(text)
    files={str(x.resolve()):hashlib.sha256(x.read_bytes()).hexdigest()for x in(p,q,Path(__file__))}
    r=dict(passed=True,scope='Unexecuted additive current widget first-writer reviewer: exact two guarded service changes, new physical worker hashes and finite compiled TLS namespace; all linked-function/ASM/unwind and contiguous source-span checks retained',changes=changes,files=files,capture_reader_opened=False,worker_executed=False,initializer_credit=0)
    f=out/'report.json';f.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=hashlib.sha256(f.read_bytes()).hexdigest())))
if __name__=='__main__':main(sys.argv[1])
