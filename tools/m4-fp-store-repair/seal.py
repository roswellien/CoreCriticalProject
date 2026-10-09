"""Additive physical closure of successes, meaningful failures and controls."""
from pathlib import Path
import hashlib
import json
import shutil
import sys
ROOT=Path(__file__).resolve().parents[2]
def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def require(ok,why):
    if not ok:raise ValueError(why)
def main():
    out=Path(sys.argv[1]).resolve();require(out.is_relative_to(ROOT/'reports/m4-fp-directed') and not out.exists(),'Fresh private author closure required')
    files={};reports=[];replacements=[]
    def physical(path,expected=None):
        path=Path(path).resolve();actual=sha(path);require(expected is None or actual==expected,'Physical binding changed: '+str(path));files[str(path)]=actual
    positive_builds=[
        'reports/m4-fp-native/first-native-r2/build.json',
        'reports/m4-fp-directed/baseline-r3/build.json',
        'reports/m4-fp-store-repair/repaired-r1/build.json',
        'reports/m4-fp-store-repair/sticky-r1/build.json',
        'reports/m4-fp-store-repair/accumulated-r1/build.json',
        'reports/m4-fp-store-controls/context-r2/build.json']
    for relative in positive_builds:
        path=ROOT/relative;meta=json.loads(path.read_text());require(meta['passed'],'Required actual recipe failed: '+relative)
        for p,h in meta['bindings'].items():physical(p,h)
        physical(path);reports.append({'path':str(path),'sha256':sha(path),'scope':meta['scope']})
    for relative in ('reports/m4-fp-native/lift-r1/pins.json','reports/m4-fp-startup/run-r1/closure/pins.json',
                     'reports/m4-fp-native/independent-first-r1/supplement-pins.json',
                     'reports/m4-fp-directed/accumulated-comparison-r1/report.pins.json'):
        path=ROOT/relative;meta=json.loads(path.read_text());mapping=meta.get('files',meta.get('bindings'))
        require(isinstance(mapping,dict),'Ancestor physical map schema differs')
        for p,h in mapping.items():physical(p,h)
        physical(path)
    # Failed recipes are retained with the literal source actually consumed.
    for relative in ('reports/m4-fp-native/first-native-r1/build.json','reports/m4-fp-directed/baseline-r1/build.json',
                     'reports/m4-fp-directed/baseline-r2/build.json','reports/m4-fp-store-controls/context-r1/build.json'):
        path=ROOT/relative;meta=json.loads(path.read_text());require(not meta['passed'],'Retained failure unexpectedly marked passed')
        for p,h in meta['bindings'].items():
            source=Path(p)
            if sha(source)==h:physical(source,h);continue
            require(p in meta['sources'],'Only explicitly preserved authored source may replace a historical live path')
            copy=path.parent/'sources'/source.relative_to(ROOT)
            if not copy.exists():copy=path.parent/source.name
            physical(copy,h);replacements.append({'historical_path':p,'historical_sha256':h,'physical_literal':str(copy)})
        physical(path)
    leaves=[
        'reports/m4-fp-native/first-observation-r1','reports/m4-fp-directed/baseline-comparison-r1',
        'reports/m4-fp-directed/repaired-comparison-r1','reports/m4-fp-directed/sticky-comparison-r1',
        'reports/m4-fp-directed/accumulated-comparison-r1','reports/m4-fp-directed/original-baseline-r2',
        'reports/m4-fp-directed/original-baseline-normal-r1','reports/m4-fp-directed/observer-controls-r1',
        'reports/m4-fp-directed/worker-controls-O0-r1','reports/m4-fp-directed/worker-controls-O2-r1',
        'reports/m4-fp-directed/worker-controls-original-normal-r1']
    for relative in leaves:
        for file in (ROOT/relative).rglob('*'):
            if file.is_file():physical(file)
    final=json.loads((ROOT/'reports/m4-fp-directed/accumulated-comparison-r1/report.json').read_text())
    require(final['passed_observed_domain'] and final['native_comparisons']==4032 and final['original_records']==2016,'Final observed domain incomplete')
    failure_counts={}
    for label,relative in (('baseline','baseline-comparison-r1'),('C1-only','repaired-comparison-r1'),('FSTP-sticky-only','sticky-comparison-r1')):
        metadata=json.loads((ROOT/'reports/m4-fp-directed'/relative/'report.json').read_text());require(not metadata['passed_observed_domain'],'Retained semantic failure was relabelled')
        failure_counts[label]={level:meta['observed_mismatches'] for level,meta in metadata['comparisons'].items()}
    out.mkdir();sources=[]
    for relative in ('tools/m4-fp-native','tools/m4-fp-directed','tools/m4-fp-store-repair','tools/m4-fp-store-controls','tests/m4-fp-directed'):
        for source in (ROOT/relative).iterdir():
            if not source.is_file():continue
            physical(source);copy=out/'sources'/source.relative_to(ROOT);copy.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,copy);physical(copy,files[str(source)])
            sources.append({'path':str(source),'literal':str(copy),'sha256':files[str(source)]})
    controls=json.loads((ROOT/'reports/m4-fp-directed/observer-controls-r1/report.json').read_text());require(controls['passed'] and len(controls['controls'])==30,'Observer controls incomplete')
    for name in ('O0-r1','O2-r1','original-normal-r1'):
        c=json.loads((ROOT/'reports/m4-fp-directed'/('worker-controls-'+name)/'report.json').read_text());require(c['passed'] and len(c['controls'])==5 and not c['additional_original_guest_bodies_executed'],'Actual worker denials incomplete')
    report={'passed_authored_observed_domain':True,'scope':'First complete FP initializer,42authored float inputs/12maskedCW/emptyTOP0,7/two repeats; independent final review remains separate',
        'original_records':2016,'native_comparisons':4032,'observed_mismatches':0,'observer_corruptions':30,'actual_worker_denials':15,
        'compiled_repaired_context_controls_per_level':8,'sources':sources,'actual_builds':reports,'historical_source_replacements':replacements,
        'retained_failed_comparisons':failure_counts,
        'defined_vs_observed':'C0/C2/C3 and dead raw x87 register bytes are observed storage, not architectural defined-data claims; actual hardware FX metadata is separate from legacy State metadata',
        'limitations':final['limitations']+['No initial occupied x87/other hardware/unmasked traps/connected ordering admission','Actual installed input20 fixed-case review is a separate smaller gate'],
        'full_M4_complete':False}
    path=out/'report.json';path.write_text(json.dumps(report,indent=2)+'\n');physical(path)
    (out/'pins.json').write_text(json.dumps({'files':files},indent=2,sort_keys=True)+'\n')
    print(json.dumps({'report':str(path),'sha256':sha(path),'bindings':len(files),'literal_sources':len(sources),'historical_source_replacements':len(replacements)}))
if __name__=='__main__':main()
