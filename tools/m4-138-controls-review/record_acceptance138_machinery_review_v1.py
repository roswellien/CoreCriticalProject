"""Bounded author audit notes and source pins, not an independent ROOT seal."""
from pathlib import Path
import ast,hashlib,json,sys
R=Path(__file__).resolve().parents[2];T=Path(__file__).parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
baseline=R/'reports/m4-joint-startup131-root/configuration-r1/configuration.json';old=json.loads(baseline.read_bytes());assert len(old['gates'])==33 and sum(len(g['equal'])for g in old['gates'].values())==841
for leaf in ('acceptance138_v3.py','configure_acceptance138_v3.py','acceptance138_criteria_v1.py'):ast.parse((T/leaf).read_text())
out=R/'reports/m4-138-controls-review/acceptance138-machinery-author-audit-r1';assert not out.exists();out.mkdir()
notes=out/'review-notes.md';notes.write_text('''# Acceptance138 machinery author audit

Scope: bounded source/configuration-schema review and synthetic criterion data tests. This is not an independent ROOT seal, completed39-gate configuration review, physical-union execution, or acceptance receipt.

## Concrete defect preserved and repaired additively

`acceptance138_v2.py:baseline_criteria` authenticated841 baseline field-name coverage but did not bind baseline expected values or prohibit many-to-one current-field mappings. `configure_acceptance138_v2.py:main` silently froze actual current values and supplied an unearned default “independently reviewed” reason. Therefore coverage alone did not prove retention of841 predicates. Existing v2 artifacts remain intact.

`acceptance138_v3.py` and `configure_acceptance138_v3.py` use `acceptance138_criteria_v1.py`. All33 baseline gates and841 actual baseline fields must have exact baseline field and typed expected value, exact current field and typed configured value, and distinct target paths within each gate. Default identity requires the same path/type/value. Finite changes require explicit old/current typed values, named physical domain, substantive causality reason, and exact separately sealed ROOT-review allowances. Boolean acceptance invariants cannot flip; non-success predicates cannot map to `passed`. Every changed path/value must be expressly admitted; no default count/hash change exists. Physical count/domain correctness remains the independent reviewer's substantive obligation; synthetic allowance examples are no actual138 domain evidence.

The checker requires the independent review to bind the criteria module, checker, storage-v2, semantic-v3 and final configuration. The review must include `criteria_delta_allowances` matching all-and-only finite deltas in the configuration, with recursively exact types and values. The config review specification prints this required object for separate assessment; emitting it is not review admission.

## Retained mechanisms checked

The additive preparation exactly inverse-restores the prior checker and configurator. The entire current semantic-v3 body, storage-v2/base storage bodies, both proof expansion utilities,39 gate labels, whole-source/widget extent predicates and current source6 pin remain unchanged. The source6 semantics require12 persistent chains/1656 phases/114264 BEFORE and AFTER pages, forbid per-phase BEFORE and candidate AFTER machine seeds, and retain lineage/resource/lifecycle restrictions.

`ScopedFiles` stores receipt-path-scoped edges; `has` queries only that scoped receipt map. It has no global-union fallback. The streamed controls report and its sibling pins have different scopes. Conflict checks are per receipt. Storage tests already preserved own-edge success and cross-report/wrong-hash refusals. Current semantic edge calls and additional controls raw/GDI/current-link joins retain exact scoped evidence ownership.

Fullraw completion requires actual10691866 raw outputs and3547696 retry equalities, closed durable proof DB and real current-controls lineage. `expand_proof_inventory.py` authenticates closed SQLite/report identities, exact schemas/columns/counts and16 cases, then freshly whole-byte hashes every physical row and refuses omitted/unmeasured/changed rows. No metadata replaces hashing. The fresh acceptance union also absorbs the entire accepted131 files map and all current dependencies, checks conflicting declarations, whole-byte rehashes every unique row, then closes/hashes its SQLite proof. The direct accepted138 files map cannot replace that inventory. `expand_accepted138_union.py` must be used by any future141 acceptance to freshly expand/re-hash every old union row; its existence alone does not enforce a future caller's use.

## Bounded evidence and unresolved admission

The strict preflight validates all841 actual baseline criterion data identities, then13 positive/adverse controls: explicit delta plus exact independent allowance, and refusals for missing/inexact allowance, mutated old expected value, duplicate-success mapping, silent value freeze, empty/generic reason/domain, type mutation, invariant flip and single success collapse. No actual current report configuration, archive, worker, physical union or acceptance was run. Current fullraw receipt and paired/current bindings remain mandatory unresolved inputs until ROOT supplies completed sealed identities and independently reviews all finite deltas.

Verified accepted count remains131/144. No new credit is claimed.
''')
paths=[Path(__file__),notes,baseline,R/'tools/m4-joint-startup131/acceptance.py',R/'reports/m4-joint-startup131-root/acceptance-r1/report.json']+[T/x for x in ('acceptance138_v2.py','acceptance138_v3.py','configure_acceptance138_v2.py','configure_acceptance138_v3.py','acceptance138_criteria_v1.py','acceptance138_semantics_v3.py','acceptance138_storage_v2.py','acceptance138_storage.py','expand_proof_inventory.py','expand_accepted138_union.py')]+[R/'reports/m4-138-controls-review'/x/'report.json'for x in ('acceptance138-strict-criteria-preparation-r1','acceptance138-strict-criteria-preflight-r1','acceptance138-machinery-preflight-r3','proof-expansion-independent-review-r1')]+[Path(sys.executable)]
report=out/'report.json';report.write_text(json.dumps(dict(passed=True,scope='Bounded author audit of exact retention/explicit-delta schema, scoped provenance and full physical-union source; not independent ROOT approval',baseline_gates=33,baseline_predicates=841,current_gates=39,strict_adverse_controls=13,source_inverse_checked=True,actual_current_configuration_reviewed=False,physical_union_executed=False,acceptance_executed=False,archive_reader_opened=False,worker_executed=False,initializer_credit=0,files={str(p.resolve()):sha(p)for p in paths}),indent=2)+'\n');print(json.dumps(dict(path=str(report),sha256=sha(report),notes_sha256=sha(notes))))
