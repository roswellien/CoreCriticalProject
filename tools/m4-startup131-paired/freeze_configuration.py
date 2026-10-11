"""Freeze only passed current131 raw/source/policy review identities."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]

def sha(path):
    with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def need(value,label):
    if not value:raise ValueError(label)

def main(source,aggregate,original_review,loaded,preflight,name):
    out=ROOT/'reports/m4-startup131-paired'/name;need(not out.exists(),'Fresh final current pairing configuration');out.mkdir(parents=True)
    files={};values={};config=dict(scope='current131-paired-frozen-gates')
    def gate(label,path,expected=None):
        path=Path(path).resolve();need(path.suffix.lower()!='.mwb','Configuration opens no archives');digest=sha(path);need(expected is None or digest==expected,'Exact current known gate');report=json.loads(path.read_bytes());need(report['passed'],'Only successful current gate '+label);files[str(path)]=digest;values[label]=report;config[label]=dict(path=str(path),sha256=digest);return report
    gate('native_execution',ROOT/'reports/m4-joint-startup131-root/execution-r1/report.json','e250499a23537e21a206989f1dc9f1db2e40faae57840daa3b7cd4bb8d3a7a57')
    native=gate('native_source',source);need(native['reader_closed']and native.get('paired_export_readers_closed')and len(native['paired_exports'])==3,'All source/export streams sealed and three branches exported')
    combined=gate('original_combined_source',aggregate);need(combined['reader_closed']and not combined['capture_archive_opened']and combined['raw_export_report_sha256']==config['native_source']['sha256'],'Inherited current original proof joins exact producer')
    cases=[r for r in combined['cases']if r['kind']=='old4'];need(len(cases)==1,'One independently fresh old4 receipt');gate('original_old4_source',cases[0]['receipt'],cases[0]['sha256'])
    gate('original_compiled_review',ROOT/'reports/m4-tree-review/original131-prelaunch-r4/report.json','e5a09a7c7771c0c7f99cc907000ca999903e21b87d1342160684f237452608ed')
    gate('original_combined_review',original_review);need(values['original_combined_review']['original_combined_source_sha256']==config['original_combined_source']['sha256'],'Independent exact current inherited source review')
    gate('original_new_MFC_source',ROOT/'reports/m4-startup131-original/source-r2/report.json','203d63def625e83cab7b2bebb274747825e888f0a2bc3b5f1331a4560055e910')
    relation=gate('loaded_inputs',loaded);need(relation['native_execution_sha256']==config['native_execution']['sha256']and relation['native_source_sha256']==config['native_source']['sha256']and relation['original_validation_sha256']=='9f3dc23c2b4f4eb5375882bb143d09f7caeb233a1d08d7b57373c606361ba07f','Fresh whole loaded-page relation binds both current executions/source')
    gate('paired_policy',ROOT/'reports/m4-startup131-paired/preparation-r1/report.json','eb9956db02af6a36757c198f4331dcc048272d0c88708b0eecac6ef42a74ef8c')
    gate('comparer_preparation',ROOT/'reports/m4-startup131-paired/comparer-preparation-r2/report.json','20f5156a55099292b90ff03c3ea0c13a5e604bf604eed4c515eaa961506d2cdd')
    gate('paired_preflight',preflight);need(values['paired_preflight']['comparer_preparation_sha256']==config['comparer_preparation']['sha256'],'Independent exact current comparer preflight')
    for label in('comparer_preparation','paired_preflight'):
        for path,digest in values[label]['files'].items():
            need(Path(path).suffix.lower()!='.mwb','No archive hashing for local configuration');need(str(Path(path).resolve())not in files or files[str(Path(path).resolve())]==digest,'Stable shared physical dependency');need(sha(path)==digest,'Whole current code/preparation identity');files[str(Path(path).resolve())]=digest
    files[str(Path(__file__).resolve())]=sha(__file__)
    path=out/'configuration.json';path.write_text(json.dumps(config,indent=2)+'\n');files[str(path.resolve())]=sha(path)
    report=dict(passed=True,scope='All11 exact current successful raw-source/compiled/policy/preflight gates frozen for full paired execution; no equality target opened',configuration=str(path.resolve()),configuration_sha256=sha(path),files=files,capture_archive_opened=False,paired_executed=False,initializer_credit=0)
    q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(q),configuration_sha256=sha(path))))
if __name__=='__main__':main(*sys.argv[1:])
