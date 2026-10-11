"""Replay every finite MFC paired derivation over sealed raw targets."""
from pathlib import Path
import collections,importlib.util,json,sys
R=Path(__file__).resolve().parents[2]
def compare(paired_path,paired,source_path,source,pin):
    def read(p,h=None):return json.loads(pin(p,h).read_bytes())
    def output(p,report,n):
        q=(p.parent/n).resolve();return read(q,report['files'][str(q)])
    def load(p,n):
        s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
    helper=load(R/'tools/m4-startup131-paired/mfc_relations_v2.py','root131_finite_MFC_pair')
    E=load(R/'tools/m4-startup131-original/export_reader.py','root131_raw_target_reader')
    J=load(R/'tools/m4-joint-startup27-review/observe.py','root131_actual_numeric_projection');model,_,_,_=J.models()
    original_path=R/'reports/m4-startup131-original/source-r2/report.json'
    old=read(original_path,'203d63def625e83cab7b2bebb274747825e888f0a2bc3b5f1331a4560055e910')
    validation_path=R/'reports/m4-startup131-original/validation-r2/report.json'
    validation=read(validation_path,'9f3dc23c2b4f4eb5375882bb143d09f7caeb233a1d08d7b57373c606361ba07f')
    original=output(original_path,old,'source-derivations.json');actual=output(validation_path,validation,'fresh-MFC-observations.json')
    native=output(source_path,source,'MFC-source-derivations.json');observed=output(paired_path,paired,'MFC-paired-source-relations.json')
    inputs=read(R/'reports/m4-joint-startup131/preparation-r1/report.json','2985c7af9372ca342ccea8a294d7dd829aba4dffe81eb8ab1ad4a01095ffac25')['inputs']
    totals=collections.Counter();ori=None;target=None
    try:
        ori=E.ExportReader(source_path,paired['native_source_report_sha256'],'original',pin)
        for level in('O0','O2'):
            target=E.ExportReader(source_path,paired['native_source_report_sha256'],level,pin)
            for seq in range(6):
                oldcase=next(r for r in original if r['sequence']==seq);rawcase=next(r for r in actual if r['sequence']==seq)
                newcase=next(r for r in native if(r['level'],r['sequence'])==(level,seq))
                counts,row=helper.compare(oldcase,rawcase,newcase,inputs,ori,target,model.hardwarefx)
                assert row==next(r for r in observed if(r['level'],r['sequence'])==(level,seq)),'Every full paired MFC derivation independently reproduced from exact current raw targets and two source branches'
                totals.update(counts)
            target.close();target=None
        ori.close();ori=None
    finally:
        if target is not None:target.close()
        if ori is not None:ori.close()
    for key,value in totals.items():assert paired['counts'][key]==value,('Current paired MFC counter',key)
    for module in(J,model):
        for p,h in getattr(module,'PINS',{}).items():pin(p,h if isinstance(h,str)else h['sha256'])
    pin(__file__);totals['independent_full_MFC_paired_derivations']=12
    return totals
