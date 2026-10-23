"""UNEXECUTED complete7 adapter; ROOT admission/terminal join required.

Reuses exact ROOT four-facet, whole-body and initialized-TLS proofs. No new
physical occurrence annotations, current8 substitution, raw/evaluator reader.
The final composer still must fully rehash/reproduce all actual24 inputs.
"""
from pathlib import Path
import collections, hashlib, json, re, sys
R=Path(__file__).resolve().parents[2]
FOUR='7979b6e0423debf0cb7972cf28f315207dcb56f54e7e0fb09b4e12dad382d73c'
PREP='8a322602c066931f5dd3ced2b9319f6907b0b01413828e2d72dd482c5ce09b2c'
BUILD='9a65633f858e7c06c5ca09a8191a41051321cf2848c1a25b4318bd4c61c08a9f'
PREFIX='c86c8082f396b517b805e182c4ea4a9b4396a9e19b290bf8fc098d172e9478bb'
FIELD='cb1d8b5fd4eae31ba3c062289b54de5e1f2c1ef4245a1b911652a45da0f7ff10'
LEDGER='8d94a0409f3ee13480fc5cf1f28b11b11ce2b471ac94da3d845fd6c996c4095d'
TERMINAL='d3f4c2352cbf957088d885f2a8f5d21268cf86efc002556994b6a71c4d42e8c9'
MANIFEST='6e7bf035598fad79a4b6b67eb030ffc9825158c85856255975d5dd47a083da16'
def need(v,s):
 if not v:raise ValueError(s)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(admission,admission_sha,name):
 p=Path(admission).resolve();need(sha(p)==admission_sha,'Exact ROOT complete7 admission');A=json.loads(p.read_bytes());need(A['passed']is True and A['legacy_complete7_adapter_admitted']is True,'Independent ROOT code/physical review before execution');files={}
 def read(path,h=None):
  path=Path(path).resolve();need(str(path)in A['files']and path.drive.casefold()in('c:',R.drive.casefold())and path.suffix.lower()not in('.mwb','.mwi','.mwc','.zip'),'Exact ordinary input admitted before open');need(path.stat().st_size<32*1024*1024,'No giant report or payload input');v=sha(path);need(v==A['files'][str(path)]and(h is None or v==h),'Whole current admitted identity');files[str(path)]=v;return json.loads(path.read_bytes())
 def absorb(gate):
  for path,h in gate['files'].items():need(A['files'].get(path)==h,'Underlying whole physical proof must be ROOT-admitted');need(files.setdefault(path,h)==h,'Exact underlying proof collision')
 need(A['files'][str(Path(__file__).resolve())]==sha(__file__),'Actual complete7 code admitted');files[str(Path(__file__).resolve())]=sha(__file__)
 four=read(R/'reports/m4-controls-terminal-composite/root-four-physical-r1/report.json',FOUR);prefix=read(R/'reports/m4-138-preresource-root-review/root-review-r1/report.json',PREFIX);fields=read(R/'reports/m4-138-criteria-frontier/root-current-controls-field-review-r1/report.json',FIELD);prep=read(R/'reports/m4-138-preresource-controls/preparation-r3/report.json',PREP);build=read(R/'reports/m4-138-preresource-controls/build-r4/build.json',BUILD)
 for gate in(four,prefix,fields,prep,build):need(gate['passed']is True,'Actual independently retained physical proof');absorb(gate)
 need(four['legacy_preparation_sha256']==PREP and four['legacy_build_sha256']==BUILD and four['whole_source_inverse']is True and four['whole_O0_CALL_and_O2_inline_physical_join']is True and four['whole_four_named_fields_physically_reviewed']is True and four['all_seven_named_fields_physically_reviewed']is False,'Exact four source/compiled facets, not four user annotations')
 counts=dict(four['counts']);need(counts==dict(whole_intended_protected_IAT_mutation_repairs=2,whole_diagnostic_only_delta=1,whole_true_source_entry_observer=1,entry_observer_inlined_in_whole_MFC_entry=1),'Original four domains unchanged')
 links=read(R/'reports/m4-138-preresource-root-review/root-review-r1/links.json',prefix['files'][str(R/'reports/m4-138-preresource-root-review/root-review-r1/links.json')]);TLS=[(i,row)for i,row in enumerate(links)if row.get('kind')=='initialized_TLS_SECREL'];owners=[row for row in links if row.get('actual_typed_call_owner')is True];need(len(owners)==1 and owners[0]['level']=='O0'and owners[0]['symbol']=='?owner@m4_mfc1168_connected@mw34@@YA@PEAX@Z','Exact separate initialized owner-bridge supplement')
 need(TLS and TLS[0][0]<links.index(owners[0])and TLS[0][1]['symbol']=='?current@Impl@Component@m4_mfc1168_connected@mw34@@2PEAU1234@EA','Actual first owner TLS occurrence precedes exact owner join')
 for index,row in TLS:need(row['runtime_address_claim']is False and type(row['section_offset'])is int and row['section_offset']>=0 and row['template_start']+row['section_offset']+8<=row['template_end'],'Actual initialized source TLS template cell; no Runtime64 substitution')
 # Preserve the ROOT source block's explicit separate owner-TLS counter domain:
 # it proves first owner_TLS then restores the old counter, so retain57 rows
 # but count only the remaining56 normal literal/adapter occurrences.
 normal_TLS=TLS[1:];need(len(normal_TLS)==prefix['counts']['actual_compiler_TLS_cells']==56 and prefix['counts']['actual_bridge_owner_TLS_cells']==1,'Exact original occurrence-domain projection, no unique-cell dedup');counts['actual_compiler_TLS_cells']=len(normal_TLS)
 ledger=read(R/'reports/m4-138-criteria-frontier/root-current-controls-field-review-r1/legacy7-whole-body-ledger.json',LEDGER);expected={'O0':('main','?mfc_mutate@@','?mfc_retry_snapshot@@','?mfc_control_entry@@'),'O2':('main','?mfc_mutate@@','?mfc_retry_snapshot@@')};seen=set()
 for row in ledger:
  key=row['level'],row['symbol'];need(key not in seen,'Exact unique whole-body key');seen.add(key);need(row['level']in expected and any(row['symbol']==v if v=='main'else row['symbol'].startswith(v)for v in expected[row['level']]),'Only original whole7 control domain')
  w=build['workers'][row['level']];need(row['object_path']==w['object']and row['object_sha256']==w['object_sha256']and row['worker_path']==w['path']and row['worker_sha256']==w['sha256'],'Actual same legacy12 object/worker, not current8');need(type(row['whole_bytes'])is int and row['whole_bytes']>0 and len(row['COFF_whole_sha256'])==len(row['linked_whole_sha256'])==64,'Whole physical body hashes/extent');need(row['relocations']==len(row['relocations_complete']),'Entire typed relocation ledger retained')
 need(len(seen)==7 and collections.Counter(level for level,symbol in seen)=={'O0':4,'O2':3}and fields['legacy7_whole_linked_control_functions']==7,'Whole7 functions distinct from15 CALL joins');counts['whole_linked_control_functions']=len(seen)
 sourcepath=R/'reports/m4-138-preresource-controls/preparation-r3/controls_main.cpp';need(A['files'][str(sourcepath)]==sha(sourcepath),'Actual authored legacy12 source');source=sourcepath.read_text();start=source.index('static void mfc_mutate(');end=source.index('static void mfc_retry_snapshot(',start);modes=[int(v)for v in re.findall(r'\bcase\s+(\d+)\s*:',source[start:end])];need(len(modes)==12 and sorted(modes)==list(range(1,13)),'Exact twelve authored public faults')
 manifest=read(R/'reports/m4-138-preresource-strict-review/root-aggregate-admission-r1/aggregate-manifest.json',MANIFEST);cases=manifest['strict_cases'];need(len(cases)==24 and{(r['level'],r['mode'])for r in cases}=={(level,mode)for level in('O0','O2')for mode in modes},'All24 measured strict case bindings cover exact same authored12')
 # No rehash/reopen of giant aggregate here. ROOT must provide its physically
 # authenticated terminal projection in THIS admission. Composer later fully
 # streams/rehashes that actual aggregate, everycase and all ordinary outputs.
 terminal=A['actual_legacy24_terminal'];need(terminal['report_sha256']==TERMINAL and terminal['passed']is True and terminal['case_count']==24 and terminal['strict_case_manifest_sha256']==MANIFEST and terminal['whole_physical_report_rehashed_by_ROOT']is True,'Exact actual terminal, not historical aggregate admission');need(terminal['counts']['actual_precise_denials']==terminal['counts']['actual_unchanged_poisoned_retries']==terminal['counts']['entryframe64_checked']==24,'Actual full terminal denial/retry/entry-frame domain')
 counts['whole_authored_public_faults']=len(set(modes));need(len(counts)==7 and all(type(v)is int and v>0 for v in counts.values()),'Exactly seven independently named finite fields')
 need(re.fullmatch('[A-Za-z0-9_-]{1,90}',name),'Simple namespace');out=R/'reports/m4-controls-terminal-composite'/name;need(not out.exists(),'Fresh output');out.mkdir();derivation=dict(four_source_receipt_sha256=FOUR,normal_TLS_occurrences=[dict(source_row=index,physical=row)for index,row in normal_TLS],separate_owner_TLS_occurrence=TLS[0][1],whole7_body_rows=ledger,authored_source_modes=modes,strict_case_bindings=cases,actual_terminal_projection=terminal)
 (out/'seven-field-derivations.json').write_text(json.dumps(derivation,indent=2)+'\n');files[str(out/'seven-field-derivations.json')]=sha(out/'seven-field-derivations.json');files[str(p)]=admission_sha
 report=dict(passed=True,physical_domain_derivation_schema='legacy12-complete7-source-derived-v1',legacy_preparation_sha256=PREP,legacy_build_sha256=BUILD,legacy_four_source_sha256=FOUR,legacy_prefix_ROOT_review_sha256=PREFIX,legacy_whole7_ledger_sha256=LEDGER,legacy24_terminal_sha256=TERMINAL,counts=counts,all_seven_named_fields_physically_reviewed=True,current8_used_as_legacy_proof=False,giant_aggregate_opened=False,giant_aggregate_current_byte_rehash_claim=False,terminal_content_revalidation_by_composer_still_required=True,canonical_reader_opened=False,worker_executed=False,accepted_function_credit=0,files=files);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main(*sys.argv[1:])
