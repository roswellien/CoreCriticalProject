"""Bind connected refusals to the exact positive persistent source component."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def main(name):
    out=R/'reports/m4-tree-review'/name;assert not out.exists();out.mkdir(parents=True)
    files={}
    def pin(p,h=None):
        p=Path(p).resolve();v=hashlib.sha256(p.read_bytes()).hexdigest();assert h is None or v==h;assert str(p)not in files or files[str(p)]==v;files[str(p)]=v;return p
    def receipt(p,h):
        d=json.loads(pin(p,h).read_bytes());assert d['passed'];return d
    positive=receipt(R/'reports/m4-joint-startup131/preparation-r1/report.json','2985c7af9372ca342ccea8a294d7dd829aba4dffe81eb8ab1ad4a01095ffac25')
    controls=receipt(R/'reports/m4-mfc1168-native/connected-controls-preparation-r6/report.json','0a45415c36b76ae10669f9ecbb8289fac4878b9e564f33212128a5c22ac12136')
    native_review=receipt(R/'reports/m4-tree-review/joint131-prelaunch-r2/report.json','20245da873b39e5a7a029f7fc5e20ffe0995ff88962b21917387678523491568')
    control_review=receipt(R/'reports/m4-tree-review/mfc1168-controls-prelaunch-r9/report.json','5d00fed2edf454249336fe29dd61592d3e7ab8cbce82003347dae0cbdf8a0527')
    assert positive['inputs']==controls['inputs'],'Exact same source/role/pointer/CRT/TIB contract'
    assert positive['selected_order'][:14]==controls['selected_order']
    assert controls['selected_order'][13]==dict(entry=0x5ae3e4,slot=0x5e0040)
    assert positive['component_preparation']==controls['component_preparation']
    component_path=Path(positive['component_preparation']).resolve()
    assert positive['files'][str(component_path)]==controls['files'][str(component_path)]
    component=receipt(component_path,positive['files'][str(component_path)])
    common=[]
    for p,h in component['files'].items():
        assert positive['files'].get(p)==controls['files'].get(p)==h
        pin(p,h);common.append(p)
    assert common
    shared=0
    for level in('O0','O2'):
        assert positive['objects'][level]==controls['objects'][level] and len(positive['objects'][level])==410
        for p in positive['objects'][level]:
            assert positive['files'][p]==controls['files'][p]
            pin(p,positive['files'][p]);shared+=1
    # Both separately reviewed linked workers retain this identical component,
    # and all typed input projections remain identical despite full-schedule
    # versus refusal harness bookkeeping.
    for leaf in('connected_component.hpp','connected_component.cpp','connected_entry.hpp'):
        p=component_path.parent/leaf;key=str(p)
        assert native_review['files'][key]==control_review['files'][key]==positive['files'][key]==controls['files'][key]
        pin(p,positive['files'][key])
    pin(__file__)
    for p,h in files.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
    r=dict(passed=True,scope='Exact full131 and actual connected-control shared literal component/caller/input contract and first14 schedule; all820 inherited compiled objects identical. Each actual link is independently admitted. No invented control coverage outside finite current source domain.',counts=dict(shared_component_physical_files=len(common),shared_inherited_objects=shared,identical_prefix_roots=14,exact_new_phase=13),files=files,capture_archives_opened=0,worker_executed=False,initializer_credit=0)
    f=out/'report.json';f.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=hashlib.sha256(f.read_bytes()).hexdigest(),counts=r['counts'])))
if __name__=='__main__':main(sys.argv[1])
