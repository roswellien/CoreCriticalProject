"""Freeze only passed current138 raw/source/policy review identities."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]

def sha(path):
    with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def need(value,label):
    if not value:raise ValueError(label)

def main(source,aggregate,original_review,loaded,policy_report,preflight,name):
    out=ROOT/'reports/m4-startup138-paired'/name;need(not out.exists(),'Fresh final current pairing configuration');out.mkdir(parents=True)
    files={};values={};config=dict(scope='current138-paired-frozen-gates')
    def gate(label,path,expected=None):
        path=Path(path).resolve();need(path.suffix.lower()not in('.mwb','.mwi','.zip')and path.name!='transport.json','Configuration opens no archives');digest=sha(path);need(expected is None or digest==expected,'Exact current known gate');report=json.loads(path.read_bytes());need(report['passed'],'Only successful current gate '+label);files[str(path)]=digest;values[label]=report;config[label]=dict(path=str(path),sha256=digest);return report
    gate('native_execution',ROOT/'reports/m4-joint-startup138-root/execution-r3/report.json','2203162c6c12c3f4c4b35009c39f2ddaaf52bea3abca9a8823d36237d7f0a4f6')
    native=gate('native_source',source,'40822c09a868ff39de882a4d70dbe7aa5b0949f8e2c4cf4bf8253d3bf4f92052');need(native['reader_closed']and native.get('paired_export_readers_closed')and len(native['paired_exports'])==3,'All source/export streams sealed and three branches exported')
    combined=gate('original_combined_source',aggregate,'7024af25138f109143adfd72db01b58f3bd58e9a22d8c772fda0e983d18d3eb4');need(combined['reader_closed']and not combined['capture_archive_opened'],'Current ordinary inherited original proof closed');og=gate('original_validation',combined['raw_export_report_path'],'02ea1ce07ac3e5aa5dff6e20813b956117383784ae4f5e1ffd6aa1822f603f5f');need(combined['raw_export_report_sha256']==config['original_validation']['sha256']and og['reader_closed'],'Exact current independent original producer');oe=next(r for r in og['paired_exports']if r['branch']=='original');ne=next(r for r in native['paired_exports']if r['branch']=='original');need(all(oe[k]==ne[k]for k in('transport_sha256','index_sha256','payload_sha256','logical_files','payload_bytes'))and Path(oe['transport_path']).resolve()==Path(ne['transport_path']).resolve(),'Independent current producers share exact original transport/index/payload/geometry')
    cases=[r for r in combined['cases']if r['kind']=='old4'];need(len(cases)==1,'One independently fresh old4 receipt');gate('original_old4_source',cases[0]['receipt'],cases[0]['sha256'])
    gate('original_compiled_review',ROOT/'reports/m4-138-validation-review/original138-observer-prelaunch-r1/report.json','eeab0505853554e353c389a6cae857f6b2c5696c0c2044e406880234b9f37e0c')
    gate('original_combined_review',original_review,'8b3056e286e82bad611875ee6c4ac04fc040a4a082fe8a4cf14e5980ee94bc6a');need(values['original_combined_review']['original_combined_source_sha256']==config['original_combined_source']['sha256'],'Independent exact current inherited source review')
    gate('original_new_MFC_source',ROOT/'reports/m4-startup138-original/mfc-source-r2/report.json','6a4e28040c31aebbc108904cb6a574d964aa28f045ff446f1362deaedd260801')
    relation=gate('loaded_inputs',loaded,'379e86517363d5abf25830b3805bb41ff5fe8b104a9e2349131e045c4a5cacec');need(relation['native_execution_sha256']==config['native_execution']['sha256']and relation['native_source_sha256']==config['native_source']['sha256']and relation['original_validation_sha256']=='02ea1ce07ac3e5aa5dff6e20813b956117383784ae4f5e1ffd6aa1822f603f5f','Fresh whole loaded-page relation binds both current executions/source')
    pg=gate('paired_policy',policy_report);need(pg['comparer_preparation_sha256']=='e44982fcb1cdc7938c89ea0c65ce3aff66b9ceeb13d01931c0f87b8db638ecc6'and pg['current138_complete_typed_domain_policy_reviewed']is True,'Root independent current comparer6 complete policy seal');need(pg['policy_sha256']==sha(ROOT/'reports/m4-startup138-paired/comparer-preparation-r6/policy-preparation.json')and Path(pg['policy']).resolve()==(ROOT/'reports/m4-startup138-paired/comparer-preparation-r6/policy-preparation.json').resolve(),'Exact current physical policy declaration')
    gate('comparer_preparation',ROOT/'reports/m4-startup138-paired/comparer-preparation-r6/report.json','e44982fcb1cdc7938c89ea0c65ce3aff66b9ceeb13d01931c0f87b8db638ecc6')
    gate('paired_preflight',preflight);need(values['paired_preflight']['comparer_preparation_sha256']==config['comparer_preparation']['sha256'],'Independent exact current comparer preflight');need(values['paired_preflight']['current138_complete_typed_domain_policy_reviewed']is True and values['paired_preflight'].get('independent_review')is True,'Independent complete current domain reviewer required');gate('original_widget_source',ROOT/'reports/m4-startup138-original/widget-complete-source-r1/report.json','4f9e1d0a8fc80f4780bf9e6ce50fe5bf1df3dcc02b42581fa369fe0c6e889684');gate('original_widget_source_review',ROOT/'reports/m4-138-validation-review/current-widget-policy-review-r1/report.json','6e980830a01cf6a4b04ff4e7abcf6faff78c9c4b478da694a64c671da6f79c46');ir=gate('CRT_import_independent_review',ROOT/'reports/m4-startup138-paired/CRT-import-independent-r1/report.json','3ae59486055ce3d0ad21ff48075248fe3544d4c2ef3dbbe7d82181874a0c36a3');need(ir['finite_144_import_cell_policy_reviewed']is True,'Independent physical all144 import policy reviewed')
    for label in('comparer_preparation','paired_preflight','paired_policy','CRT_import_independent_review'):
        for path,digest in values[label]['files'].items():
            need(Path(path).suffix.lower()not in('.mwb','.mwi','.zip')and Path(path).name!='transport.json','No archive hashing for local configuration');need(str(Path(path).resolve())not in files or files[str(Path(path).resolve())]==digest,'Stable shared physical dependency');need(sha(path)==digest,'Whole current code/preparation identity');files[str(Path(path).resolve())]=digest
    files[str(Path(__file__).resolve())]=sha(__file__)
    path=out/'configuration.json';path.write_text(json.dumps(config,indent=2)+'\n');files[str(path.resolve())]=sha(path)
    report=dict(passed=True,scope='All15 exact current successful raw-source/compiled/policy/preflight gates frozen for full paired execution; no equality target opened',configuration=str(path.resolve()),configuration_sha256=sha(path),files=files,capture_archive_opened=False,paired_executed=False,initializer_credit=0)
    q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(q),configuration_sha256=sha(path))))
if __name__=='__main__':main(*sys.argv[1:])
