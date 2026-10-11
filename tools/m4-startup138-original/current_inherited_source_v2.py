"""Current138 inherited source comparisons from sealed raw export only."""
from pathlib import Path
import collections, hashlib, importlib.util, json, sys, time, traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
PINS={}
VALIDATION_SHA='74d444a5c9cfef4af293a0340af5bdfe6e6891d848b4ac16f9d1f8e562fa6181'
def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def need(value,label):
    if not value:raise ValueError(label)
def pin(path,digest=None):
    path=Path(path).resolve();need(path.suffix.lower()!='.mwb','No archive opened in current138 source lane');actual=sha(path)
    need(digest is None or digest==actual,'Exact current dependency '+str(path));need(str(path)not in PINS or PINS[str(path)]==actual,'Stable physical input');PINS[str(path)]=actual;return path
def read(path,digest=None):return json.loads(pin(path,digest).read_bytes())
def load(path,name):
    path=pin(ROOT/path);spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def main(name,export_report,export_sha):
    out=ROOT/'reports/m4-startup138-original'/name;need(not out.exists(),'Fresh current source proof');out.mkdir(parents=True)
    counts=collections.Counter();cases=[];format_rows=[];trees=[];reader=None;passed=False;started=time.perf_counter()
    try:
        validation_path=ROOT/'reports/m4-startup138-original/original-validation-r2/report.json';validation=read(validation_path,VALIDATION_SHA);need(validation['passed']and validation['counts']['phases']==828 and validation['record_bytes']==356992 and validation['combined_pages']==69 and validation['callbacks']==108 and validation['original_executed'] and not validation['native_executed'],'Current genuine131 six-domain process')
        prep_path=ROOT/'reports/m4-startup138-original/inherited-source-preparation-r1/report.json';prep=read(prep_path);need(prep['passed']and not prep['capture_reader_opened'],'Exact additive raw-source preparation')
        for path,digest in prep['files'].items():pin(path,digest)
        E=load('tools/m4-startup138-original/export_reader.py','current138_export_reader');reader=E.ExportReader(export_report,export_sha,'original',pin)
        need(reader.path==Path(validation['original_capture']).resolve(),'Current original branch capture identity carried by exporter')
        formatter=load('tools/m4-startup138-original/format_source_v4.py','current138_formatter4');formatter.PINS=PINS;formatter.main(name+'-formatter4',reader)
        path=out.parent/(name+'-formatter4')/'report.json';receipt=read(path);need(receipt['passed'],'Fresh24literal formatter prefixes');counts.update(receipt['counts']);source=path.parent/'source-derivations.json';format_rows=read(source,receipt['files'][str(source.resolve())]);need(len(format_rows)==24,'Four current roots by six domains');cases.append(dict(kind='formatter4',receipt=str(path.resolve()),sha256=sha(path)))
        tree=load('tools/m4-startup138-original/tree_source.py','current138_tree');tree.PINS=PINS;tree.SHARED_READER=reader
        for sequence in range(6):
            case=name+'-tree-'+str(sequence);tree.main(case,ROOT/'tools/m4-tree-source/game_model_v4.py',sequence);path=out.parent/case/'report.json';receipt=read(path);need(receipt['passed'],'Fresh literal tree domain');counts.update(receipt['counts']);source=path.parent/'source-derivations.json';derived=read(source,receipt['files'][str(source.resolve())]);need(derived['phase']==83,'Current physical tree phase after new nonregistering MFC')
            trees.append(dict(sequence=sequence,phase=83,source=derived,receipt=str(path.resolve()),sha256=sha(path)));cases.append(dict(kind='tree',sequence=sequence,receipt=str(path.resolve()),sha256=sha(path)))
            print(json.dumps(dict(tree_sequence=sequence,passed=True)),flush=True)
        reader.close();reader.entries.clear();reader.bundles.clear();reader=None;tree.SHARED_READER=None
        old=load('tools/m4-startup138-original/old4_source.py','current138_old4');old.PINS=PINS;old.main(name+'-old4')
        path=out.parent/(name+'-old4')/'report.json';receipt=read(path);need(receipt['passed']and receipt['original_validation_sha256']==VALIDATION_SHA,'Fresh complete old4 source/buffer carry gate');counts.update(receipt['counts']);cases.append(dict(kind='old4',receipt=str(path.resolve()),sha256=sha(path)))
        mfc_path=ROOT/'reports/m4-startup138-original/mfc-source-r1/report.json';mfc=read(mfc_path,'e320179826dc0d0ab6033e98502eb5706186afa235222dd906d67c7d9605180f');need(mfc['passed']and mfc['counts']['literal_source_instructions']==852 and mfc['counts']['ordered_source_operands']==678,'Independent genuine current six-domain MFC proof')
        counts['literal_new_MFC_instructions']=852;counts['literal_new_MFC_operands']=678
        cases.append(dict(kind='new_MFC',receipt=str(mfc_path.resolve()),sha256=sha(mfc_path)))
        for label,value in [('original-Formatting-source-derivations.json',format_rows),('original-Tree-source-derivations.json',trees)]:
            path=out/label;path.write_text(json.dumps(value,indent=2)+'\n');pin(path)
        need(len(trees)==6 and counts['literal_constructor_prefixes']==24 and counts['literal_original_new_root_prefixes']==24,'Complete current original bounded families')
        pin(__file__);passed=True
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        if reader is not None:reader.close();reader.entries.clear();reader.bundles.clear();reader=None
        if 'tree'in locals():tree.SHARED_READER=None
        report=dict(passed=passed,scope='Fresh current138 original literal formatter4/tree/old4 and independently sealed new-MFC family proofs. Every prefix starts from current own whole BEFORE and finite actual API/allocator facts; byteflows and whole owner/page carries derive from literal source. Prior130 literal corpus retained under exact current physical-source/observer review. No capture archive reopened.',original_validation_path=str(validation_path)if'validation_path'in locals()else None,original_validation_sha256=VALIDATION_SHA,raw_export_report_path=str(Path(export_report).resolve()),raw_export_report_sha256=export_sha,counts=dict(counts),cases=cases,files=PINS,reader_closed=True,capture_archive_opened=False,archive_sessions_opened=0,elapsed_seconds=time.perf_counter()-started,candidate_AFTER_machine_seed=False,original_postRET_observed=False,original_postRET_source_derived=True,formatter_full_registration_provider_CPU_executed_by_model=False,initializer_credit=0)
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,reader_closed=True,report_sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(sys.argv[1],sys.argv[2],sys.argv[3])
