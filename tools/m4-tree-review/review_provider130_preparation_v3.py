"""Final overlap-complete prepared consumer review, supplementing exact v4 proof."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];P={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');v=sha(p);assert h is None or h==v,(p,h,v);P[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def main(name):
 out=R/'reports/m4-tree-review'/name;assert not out.exists();out.mkdir(parents=True)
 old=read(R/'reports/m4-tree-review/provider130-preparation-r1/report.json','2e654d0a91da2cbbf844dbbef00b71d4fc342a7b023dc96f72931f7e42db01e9');assert old['passed']and old['bootstrap_calls']==1 and old['planned_phases']==1560
 for p,h in old['files'].items():pin(p,h)
 prep_path=R/'reports/m4-formatting-source/provider130-preparation-r8/report.json';prep=read(prep_path,'ad08192d0f78ebcaa654b8809fd2568e56a910de347a5bcd4785462766c3c063');assert prep['passed']and prep['domain']==[0x78145000,0x78147000]and not prep['capture_reader_opened']and not prep['executed']
 for p,h in prep['files'].items():pin(p,h)
 pre=read(R/'reports/m4-formatting-source/provider130-preflight-r4/report.json','b50869b5af5beae7db10c9996d5b88601ffd6fde9c3e57031b47ae43812a313b');assert pre['passed']and pre['physical_source_rows']==4637 and pre['source_callback_PC_count']==195
 base=R/'tools/m4-formatting-source';v5=pin(base/'compare_provider130_v5.py').read_text();v6=pin(prep['tool']).read_text()
 a='if 0x78145000<=r[1]and r[1]+r[3]<=0x78147000';b='if r[1]<0x78147000 and r[1]+r[3]>0x78145000';assert v5.count(a)==v6.count(b)==2;expected=v5.replace(a,b);a="pin(ROOT/'tools/m4-formatting-source/prepare_provider130_v7.py');";assert expected.count(a)==1;expected=expected.replace(a,a+"pin(ROOT/'tools/m4-formatting-source/prepare_provider130_v8.py');");assert expected==v6
 assert 'F.finish(machine,responses,expected_callbacks,G);provider_scope_rows.append' in v6
 assert "bootstrap_provider_pages={str(p):before['memory'][p].hex()for p in(0x7810a000,0x78145000,0x78146000)}"in v6
 assert "source_RW_IAT_operands=[dict(source_access_index=i,PC=r[0],address=r[1],value=r[2],width=r[3],write=r[4])"in v6
 assert "provider_API_transports=[list(r)for r in machine.transports"in v6
 assert v6.count('B2.bootstrap(')==1 and 'R.EXPECTED_LOCKIT_CALLS=36'in v6 and 'need(READS<=set(PINS)'in v6
 source=read(R/'reports/m4-formatting-source/native130-provider-r1/report.json','1ac217828913db6c1efe91cb6a1b3c410b946bac883064856311e2845e7fdbfd');assert source['passed']and source['files'][str(Path(prep['tool']).resolve())]==sha(prep['tool'])and source['executed_lineage']['native_preparation_sha256']=='1f704ba8254433b9ae7387a53322c33b4db536b99eb79363ff71e54169cb65f3'
 pin(__file__);pin(R/'tools/m4-tree-review/review_provider130_preparation_v2.py')
 result={k:v for k,v in old.items()if k!='files'};result.update(scope='Independent final prepared v6 source/provider code review: inherited exact private chronology remains fixed, additive bounded complete page/overlap export after complete source equality, exact current consumer identity bound; actual proof and physical read closure separate',preparation_sha256=sha(prep_path),previous_independent_preparation_review_sha256='2e654d0a91da2cbbf844dbbef00b71d4fc342a7b023dc96f72931f7e42db01e9',source_provider_sha256=sha(R/'reports/m4-formatting-source/native130-provider-r1/report.json'),overlap_complete_source_and_API_transport_domain=True,exact_overlap_filter_extensions=2,physical_source_rows=4637,source_callback_PC_rows=195,files=P)
 p=out/'report.json';p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(p))))
if __name__=='__main__':main(sys.argv[1])
