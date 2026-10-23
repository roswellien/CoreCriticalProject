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
    original_path=R/'reports/m4-startup138-original/mfc-source-r2/report.json'
    old=read(original_path,'6a4e28040c31aebbc108904cb6a574d964aa28f045ff446f1362deaedd260801')
    validation_path=R/'reports/m4-startup138-original/original-validation-r3/report.json'
    validation=read(validation_path,'02ea1ce07ac3e5aa5dff6e20813b956117383784ae4f5e1ffd6aa1822f603f5f')
    original=output(original_path,old,'source-derivations.json');actual=output(validation_path,validation,'fresh-MFC-observations.json')
    native=output(source_path,source,'MFC-source-derivations.json');observed=output(paired_path,paired,'MFC-paired-source-relations.json')
    inputs=read(R/'reports/m4-joint-startup138/preparation-r4/report.json','a392e9d80e88a3779cc37247b681eeea5e3012aa90304564290d5283f7f73a2a')['inputs']
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
