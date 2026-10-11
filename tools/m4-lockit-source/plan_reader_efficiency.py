"""Read-only code/manifest accounting; no capture payload or reader is opened."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/m4-lockit-source/reader-efficiency-plan-r1'
assert not OUT.exists();OUT.mkdir()
files={}
def pin(path):
 path=Path(path).resolve();files[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest();return path
def evidence(path,needles):
 path=pin(path);lines=path.read_text().splitlines();result=[]
 for meaning,needle in needles:
  found=[i+1 for i,line in enumerate(lines)if needle in line]
  assert found,(path,needle)
  result.append(dict(meaning=meaning,lines=found,source=needle))
 return dict(path=str(path),sha256=files[str(path)],evidence=result)
sources=[evidence(ROOT/'tools/m4-crt-allocation-root/run_v2.py',[
 ('DirectSet whole-part caller pin','path = pin(self.path.parent / name, part[\'sha256\'])'),
 ('CaptureBundle construction','reader = CaptureBundle(path, part[\'sha256\'])'),
 ('DirectSet reads every entry again merely to total bytes','part_bytes += len(reader.read_bytes(logical))'),
 ('Directory inventory closure','{p.name for p in self.path.parent.iterdir()} == physical')]),
 evidence(ROOT/'tools/m4-pipeline/capture_bundle.py',[
 ('Windows open shares read only','str(path), 0x80000000, 1, None, 3, 0x80, None'),
 ('Whole mapped bundle SHA','hashlib.sha256(self._map).hexdigest() != expected_sha256'),
 ('Pinned index SHA','hashlib.sha256(raw_index).digest() != index_sha'),
 ('Exact canonical index bytes','_json(index) != raw_index'),
 ('Every entry eagerly read at constructor end','self.read_bytes(name)'),
 ('Each logical access copies and hashes payload','data = self._map[start:start + size]'),
 ('Per-access digest check','hashlib.sha256(data).hexdigest() != digest')]),
 evidence(ROOT/'tools/m4-joint-startup124/run_v2.py',[
 ('Current pin always hashes the file','p=Path(p).resolve();v=sha(p)'),
 ('Second stage receives previously generated current-level captures as watched inputs','inputs=[p for p in pins if p not in inherited_archives]'),
 ('One stability wholehash per current pin after each level',"if p not in inherited_archives:assert sha(p)==h")]),
 evidence(ROOT/'tools/m4-pipeline/stages.py',[
 ('Stage watched inputs before command','watched = {str(Path(p).absolute()): sha(p) for p in inputs}'),
 ('Stage watched inputs after command','current[path] = sha(path) if Path(path).is_file() else None'),
 ('verify_stage rehashes final watched inputs','for path, expected in value[\'final_input_sha256\'].items():')]),
 evidence(ROOT/'tools/m4-pipeline/manifests.py',[
 ('Final full physical dependency hashing',"actual = hashlib.file_digest(stream, 'sha256').hexdigest()"),
 ('Final verifier rejects metadata-only cache claims','metadata_only_cache_used=False')]),
 evidence(ROOT/'tools/m4-pipeline/paths.py',[
 ('Workspace path checks every existing ancestor','reject_reparse(cursor)'),
 ('Reparse rejection','getattr(info, \'st_file_attributes\', 0) & 0x400')])]
levels=[]
for level in ('O0','O2'):
 p=pin(ROOT/'reports/m4-joint-startup124-root/execution-r2'/level/'transport.json');d=json.loads(p.read_bytes())
 bundle=sum(part['bundle_bytes']for part in d['parts']);payload=d['payload_bytes'];indexes=sum(part['index_bytes']for part in d['parts'])
 assert bundle==payload+indexes+48*len(d['parts'])
 levels.append(dict(level=level,manifest=str(p),parts=len(d['parts']),logical_files=d['logical_files'],payload_bytes=payload,bundle_bytes=bundle,index_bytes=indexes,mandatory_DirectSet_open_hash_bytes=2*bundle+2*payload,mandatory_DirectSet_open_payload_copy_bytes=2*payload))
native_report=pin(ROOT/'reports/m4-joint-startup124-root/execution-r2/report.json')
assert files[str(native_report)]=='e0ca3ce031afbcde80ff84c0968d30850972625d2f6d8e2a8c8934386a2e7732'
total_open=sum(r['mandatory_DirectSet_open_hash_bytes']for r in levels)
root_run_native_hash_bytes=6*levels[0]['bundle_bytes']+2*levels[0]['payload_bytes']+3*levels[1]['bundle_bytes']+2*levels[1]['payload_bytes']
accounting=dict(formula='For each current DirectSet open: 2*A + 2*P SHA input bytes and 2*P eager Python payload copies, where A is complete bundle bytes and P is logical payload bytes; semantic read_bytes calls add further copies/hashes.',both_native_levels_one_consumer_open_hash_bytes=total_open,both_native_levels_one_consumer_open_hash_GiB=total_open/2**30,three_native_consumers_open_hash_bytes=3*total_open,three_native_consumers_open_hash_GiB=3*total_open/2**30,root_structural_native_hash_bytes_from_code=root_run_native_hash_bytes,root_structural_native_hash_GiB_from_code=root_run_native_hash_bytes/2**30,root_structural_formula='O0: 6*A0+2*P0 (two opening wholehashes, three O2-stage watch/verify wholehashes, two after-level stability wholehashes counted with opening gives six); O2: 3*A2+2*P2 (two opening wholehashes plus final stability).',root_structural_count_note='The total includes DirectSet pin plus CaptureBundle wholehash, eager constructor/DirectSet logical hashing, stage2 before/after/verify input hashing of prior O0 parts, and after-level pin stability. It excludes worker writing, metadata receipts, native semantic accesses, original lane captures and final acceptance dependency hashing.',physical_disk_IO_measured=False,elapsed_speedup_measured=False)
# Clarify wholehash arithmetic independently: O0 opening2 + stability2 + stage2 watch/verify3 =7.
accounting['root_structural_native_hash_bytes_from_code']=7*levels[0]['bundle_bytes']+2*levels[0]['payload_bytes']+3*levels[1]['bundle_bytes']+2*levels[1]['payload_bytes']
accounting['root_structural_native_hash_GiB_from_code']=accounting['root_structural_native_hash_bytes_from_code']/2**30
accounting['root_structural_formula']='O0: 7*A0+2*P0 (opening2 + after-level stability2 + O2 stage watch/verify3); O2: 3*A2+2*P2 (opening2 + final stability1).'
doc='''# Capture-reader efficiency proposal for the next batch

The existing reader proves more than the semantic consumer needs at opening time, then proves the same bytes repeatedly. For each part it performs a caller whole-file SHA, a second whole-file SHA inside CaptureBundle, a full logical payload scan inside CaptureBundle, and another full logical payload scan in DirectSet merely to sum lengths. Every later semantic read copies and hashes the requested entry again. The small planning receipt contains exact code anchors and manifest-derived byte counts. These are code-derived SHA input bytes, not measured disk I/O or a runtime speedup.

The current124 consumers and their acceptance rules remain unchanged. Prototype an additive lazy canonical reader for the next batch, authorized by one exact pinned successful structural execution receipt and the matching transport manifest. Keep the full physical archive SHA in final acceptance. This is deferred physical sealing, not a metadata cache or a new source of native execution credit.

1. Validate the exact receipt, successful worker stage/build/code associations, capture path, transport digest, part names/digests/index digests/extents/counts and expected complete directory inventory. Historical source/header/API inputs retain their existing exact pins. An unpinned or unsuccessful receipt falls back to the existing eager reader or fails closed.
2. Open each part once with a read-only handle that shares read only and retain the handle through final sealing. Reject reparse ancestors, ADS/UNC/ambiguous paths and duplicate physical part identities. Record the fresh volume/file ID, resolved handle path, size and attributes. If a new structural receipt records these identities, require a match; legacy receipts lack them and must not be advertised as proving historical file identity. Identity/size/timestamps alone never justify byte equivalence.
3. On the held object, validate the 48-byte header and expected index SHA, exact canonical JSON, exact schema/types/bounds, sorted normalized unique names, contiguous extents, all per-entry SHA strings, no trailing payload, disjoint cross-part logical union and exact directory closure. Sum the validated entry sizes without reading payload bytes. This removes DirectSet's unnecessary payload scan and the constructor's eager logical scan. The complete expected index cryptographically fixes every entry digest before use.
4. Each data/words call copies the addressed bytes from the held mapping into immutable bytes and checks its exact entry SHA before exposing them to the source/observer. Do not memoize validation based on a name, mtime or file size. Initial prototype needs no payload cache. Names/counts/extents alone carry no payload authenticity claim.
5. Treat semantic results as provisional until each held part has a final complete SHA equal to the exact prior expected digest, handles/identities/namespace remain consistent, manifests/receipts are unchanged, and final full dependency verification passes. Bind the final seal and all per-access verification counters into the consumer receipt; consumers and acceptance reject an unsealed receipt. Final acceptance continues its full manifest hash check. If shared final hashing is later introduced, bind it to the exact continuously held objects and all consumer receipts; merely copying a prior passed flag is insufficient.
6. Close mappings/handles and clear both DirectSet and bundle indexes at level/case boundaries after sealing. Preserve current serial canonical-reader scheduling. The lazy reader should expose the same canonical data/words interface so the source model, native State/CPU/FX/page comparisons and owner proofs remain unchanged.

Fresh identity is a namespace/ownership observation, not a substitute for a digest. A changed unread payload may remain undetected while unrelated verified records are consumed; final sealing must reject it before any acceptance credit or downstream irreversible action. A writable mapping or out-of-band writer can defeat assumptions about ordinary share locks, so per-access digests plus the full final hash remain mandatory. Immutable returned copies protect an already verified semantic input from later mapped-file changes.

Required mutation controls on private test copies: consumed payload bit flip with unchanged size/restored timestamps; unread payload corruption caught only at final seal; same-size/index-hash-recomputed substitution rejected by the prior expected index pin; bad header/index digest/schema/types/counts/offsets/trailing bytes; duplicate logical names across parts and duplicate physical part IDs; extra/missing/replaced directory entries; reparse/ADS/UNC path substitutions; stale/wrong/failed structural receipts; write/delete/rename attempts while handles are held; pre-existing writer conflict; truncation or identity changes; and tampering between consumers. Demonstrate fail-closed behavior for each and reject any provisional/unsealed consumer receipt. Avoid modifying any frozen124 artifacts.

Benchmark only after a prototype exists: use the same exact next-batch capture, preserve all semantic derivation outputs and final fullhash results, compare old/new reader opening, per-access hashing, semantic work, final sealing and peak memory separately with monotonic timings. Record SHA input bytes, copied payload bytes, number of verified records, fullhash count and cache conditions. Use serialized runs and report sample order; do not claim cold-cache timing without evidence. Measure broad provider and narrower source/paired consumers separately. The reduction in redundant SHA bytes does not establish an equal reduction in elapsed time.

One adjacent coordinator cost is independent of the reader change: current run_v2 puts all accumulated nonhistorical pins into the second worker stage's watched inputs, which includes generated O0 capture parts. That triggers additional O0 wholehashes before/after the O2 worker and during verify_stage, although the worker argument vector names only its O2 output. A later explicit immutable input/output closure can avoid treating unrelated generated captures as second-worker inputs while retaining final full capture verification. This needs a separate provenance review and must not be silently changed in the current124 run.
'''
(OUT/'proposal.md').write_text(doc,encoding='utf-8');pin(OUT/'proposal.md');pin(__file__)
report=dict(passed=True,scope='Read-only code and small manifest accounting/planning only; no capture payload read, no reader opened, no implementation or measured speedup, no current124 consumer changes',native_executed=False,initializer_credit=False,levels=levels,accounting=accounting,code_evidence=sources,proposal=str(OUT/'proposal.md'),files=files)
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(passed=True,report=str(OUT/'report.json'),sha256=hashlib.sha256((OUT/'report.json').read_bytes()).hexdigest(),accounting=accounting),indent=2))
