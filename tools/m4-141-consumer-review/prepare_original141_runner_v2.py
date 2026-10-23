"""Immutable original138 runner derivative; no run or reader."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[2]
def main():
 out=R/'reports/m4-original141/runner-preparation-r2';out.mkdir();p=R/'tools/m4-startup138-original/run_realloc_v1.py';s=p.read_text();deltas=[]
 def edit(a,b,n=1):
  nonlocal s
  assert s.count(a)==n,(a,s.count(a));s=s.replace(a,b);deltas.append(dict(old=a,new=b,count=n))
 edit("BASE=R/'reports/m4-startup138-original'","BASE=R/'reports/m4-original141'")
 edit("R/'reports/m4-startup138-original/build-r5/build.json'","R/'reports/m4-original141/build-r1/build.json'")
 edit('da5e20d9dfbfbaf70e8ad59b94dce328c22eb5330507ebb22cb38c6ef6508676','088e5dfbe970baee5e8187edbfbb5f06eafd217d2b1f5554e344ed55b836d79b')
 edit(" if preflight.resolve()!=R/'reports/m4-138-validation-review/original138-observer-prelaunch-r1/report.json' or preflight_digest!='eeab0505853554e353c389a6cae857f6b2c5696c0c2044e406880234b9f37e0c':raise ValueError('Only independently reviewed current realloc observer is admitted')"," if preflight.resolve()!=R/'reports/m4-original141/root-capture-admission-r1/report.json':raise ValueError('Only ROOT final current original141 capture preflight is admitted')")
 edit('(138,828,356992)','(141,846,356992)')
 edit('9bd1ef9049eccaeb9f87e81f38e001d0d1c805f077c75a8563fc08ec0e67b161','7c1acf0bb08043cf8a371a6b31d7fc3f4071771dae936a748abad66969c8cbd8',2)
 edit("R/'reports/m4-startup138-original/preparation-r8/report.json'","R/'reports/m4-original141/source-preparation-r2/report.json'")
 anchor=" for p,h in q['files'].items():pin(p,h)"
 edit(anchor,""" if q['original141_writer_admitted'] is not True or q['original141_validator_admitted'] is not True:raise ValueError('Explicit ROOT current writer AND strict validator admission required')
 if q['files'].get(str(Path(__file__).resolve()))!=sha(Path(__file__).resolve()):raise ValueError('Actual runner physically belongs to current ROOT admission')
 validator=R/'tools/m4-141-consumer-review/validate_original141_v5.py'
 if q['files'].get(str(validator))!='6d626f34694f31b7ff14f30f69c03b667323d1b709c1c0d8a693ce0cea3a2307':raise ValueError('Exact retained strict original141 validator required')
 if b['sequences']!=6 or b['pages']!=43 or b['external_pages']!=26 or b['combined_pages']!=69 or b['constructor_global_extra_page_bytes']!=4096:raise ValueError('Exact original141 source/CRT/global geometry')
 for p,h in q['files'].items():pin(p,h)""")
 edit("STORAGE_ROOT/'reports/m4-startup138-original'","STORAGE_ROOT/'reports/m4-original141'")
 # Diagnostic/report scope only; inherited timeout/storage/process/staging guards remain exact.
 edit('full138','full141',5)
 edit('original138','original141',1)
 edit('Only exact final preparation8 is admitted','Only exact actually compiled preparation2 is admitted')
 reverse=s
 for d in reversed(deltas):assert reverse.count(d['new'])==d['count'];reverse=reverse.replace(d['new'],d['old'])
 assert reverse==p.read_text();q=Path(__file__).with_name('run_original141_v2.py');assert not q.exists();ast.parse(s);q.write_text(s,encoding='utf-8')
 d=out/'runner-deltas.json';d.write_text(json.dumps(deltas,indent=2)+'\n',encoding='utf-8');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 inputs=[p,q,d,Path(__file__),R/'reports/m4-original141/validator-preparation-r5/report.json',R/'reports/m4-original141/source-stack-preparation-r2/report.json',R/'reports/m4-original141/build-r1/build.json']
 report=dict(passed=True,prepared_only=True,exact_runner_inverse=True,deltas=len(deltas),timeout_seconds_unchanged=300,storage_limits_unchanged=True,ROOT_final_admission_required=True,ROOT_final_admission_path=str(R/'reports/m4-original141/root-capture-admission-r1/report.json'),required_admission_fields=['passed','original141_writer_admitted','original141_validator_admitted','files actualrunner/currentvalidator/build/linkedworker + all dependencies'],worker_launched=False,reader_opened=False,initializer_credit=0,files={str(x.resolve()):sha(x)for x in inputs},invocation_template='C:/Python314/python.exe tools/m4-141-consumer-review/run_original141_v2.py D:/Projects/MW34Recomp/reports/m4-original141/build-r1/build.json 088e5dfbe970baee5e8187edbfbb5f06eafd217d2b1f5554e344ed55b836d79b D:/Projects/MW34Recomp/reports/m4-original141/root-capture-admission-r1/report.json <ROOT-final-preflight-SHA> <fresh-execution-name>')
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(sha(p))
if __name__=='__main__':main()
