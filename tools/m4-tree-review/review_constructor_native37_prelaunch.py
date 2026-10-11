"""Physical/source/link admission for the frozen bounded constructor37 workers.

No worker or capture reader is opened here. This review grants a bounded run,
not source equivalence or additional accepted initializers.
"""
from pathlib import Path
import collections, hashlib, importlib.util, json, re, struct, sys, traceback
sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[2]
PH = '5507c72aef7bcf8afdd7c2b6fe3a906f3c65da58e69cc555f0671670cf289ad9'
BH = '8eacf3dfadf4d69f420683ad5abee7bdc4db645516e720ecd422f7310ec5f56e'

def main(name):
 out = R/'reports/m4-tree-review'/name
 assert not out.exists()
 out.mkdir()
 pins, links, counts = {}, [], collections.Counter()
 passed = False
 def pin(p, expected=None):
  p = Path(p).resolve()
  assert p.suffix.lower() not in ('.mwb', '.zip')
  with p.open('rb') as f: digest = hashlib.file_digest(f, 'sha256').hexdigest()
  assert expected is None or digest == expected, (str(p), expected, digest)
  assert str(p) not in pins or pins[str(p)] == digest
  pins[str(p)] = digest
  return p
 def read(p, expected):
  d = json.loads(pin(p, expected).read_bytes())
  assert d['passed']
  for q, h in d['files'].items(): pin(q, h)
  return d
 def load(p, name):
  spec = importlib.util.spec_from_file_location(name, pin(p))
  m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
  return m
 try:
  base = R/'reports/m4-constructor-native'
  p = read(base/'fixture-preparation-r3/report.json', PH)
  b = read(base/'fixture-build-r7/build.json', BH)
  c = read(base/'preparation-r7/report.json', 'd291ae395b5ee16243f160daba61d360a08142188c84291f4c7458bc86693384')
  cb = read(base/'build-r5/build.json', '10441be38276c3f199119665eaf2d236726e87597a0bcd3eac77630cf5fbf271')
  sp = read(base/'service-preparation-r4/report.json', 'ccd92f92048563db7fe9de82d694179d5f43bec42b9e4ad32ff733934cbd74e5')
  sb = read(base/'service-build-r4/build.json', '3ea775399bf76f6dc32f23f2f2610a73718a03e06c840536a6c1fa4703fd4e3a')
  read(base/'store-operands-r1/report.json', '56acaf9dffcf68355d6a68bcd28ef841e084208e9f10724a8a14d3d06ed63d33')
  read(base/'store-timing-all-r1/report.json', '1a15354021d7f68f2f6bee48b8502b63de64d7c2a0882db8cea0834f3d83c968')
  read(R/'reports/m4-tree-review/constructor37-outcomes-r1/report.json', 'bb570f3a1210990840eb50f8cd5ea2cfbf3f027c14b9ee9d6837a5d9b88604f5')
  assert b['preparation_sha256'] == PH and len(p['selected_order']) == 37
  assert p['selected_phases'] == 222 and p['Runtime_translations'] == 135 and p['Runtime_calls_per_sequence'] == 37
  assert p['current_callbacks'] == 25 and p['ordinary_pages'] == 46
  assert not p['source_AFTER_seed'] and not p['per_phase_reseed'] and not p['native_executed'] and not b['native_executed']
  assert c['roots'] == [0x4103f0, 0x410440, 0x459b40] and c['literal_bodies'] == 33 and c['physical_rows'] == 1401
  for row in c['namespace_relations']:
   before = pin(row['original_IR'], row['original_sha256']).read_bytes()
   after = pin(row['component_IR'], row['component_sha256']).read_bytes()
   assert before.replace(b'mw34_onexit_game_', b'mw34_constructor_game_') == after
   counts['whole_namespace_only_IR_relations'] += 1
  assert counts['whole_namespace_only_IR_relations'] == 33
  for row in sp['source_relations']:
   before = pin(row['parent'], row['parent_sha256']).read_bytes()
   after = pin(row['child'], row['child_sha256']).read_bytes()
   if row['unchanged']:
    assert before == after; counts['whole_unchanged_service_inputs'] += 1
   else:
    assert Path(row['child']).name in ('session.hpp', 'session_impl.inc')
    counts['explicit_constructor_service_extensions'] += 1
  assert counts['whole_unchanged_service_inputs'] == 70 and counts['explicit_constructor_service_extensions'] == 2
  api = pin(base/'service-preparation-r4/session_impl.inc').read_text()
  component = pin(base/'preparation-r7/component.cpp').read_text()
  fixture = pin(base/'fixture-preparation-r3/fixture.cpp').read_text()
  for token in ['constructor_active_root_==root', 'constructor_prior_root_==root?&constructor_prior_read_:nullptr', 'm4_constructor_store_source::guard(s,pc,address,bytes,value,constructor_access_epoch_', 'a->expected.size()==a->mapped_bytes', 'actual==a->expected&&!std::memcmp(a->native,a->expected.data(),a->extent)', 'view.requested', 'binding->expected_store(address,raw.data(),bytes)', 'after.guest==view.guest&&after.generation==view.generation&&after.native==view.native', 'a->extent==((argument+15)&~15U)', 'ret==site+5', 'argument==wanted', 'private source operand epoch']:
   assert token in api, token
  for token in ['a==s.gpr.rsp.dword-4&&v==pc+row.size', 'session.constructor_scope(s,root,true)', 'session.constructor_scope(s,root,false)', 'session.constructor_owner_read(s,root,pc,a,n,v)', 'session.constructor_source_write(s,root,pc,a,n,v)', 'word(vptr+0x18)==0x40a850', 'nodes==count+1&&matches==1', 'frames.empty()&&FS_frames.empty()', 'const auto outer=r.cpu()', 'r.cpu()=outer', 'pc!=0x56fea0']:
   assert token in component, token
  assert fixture.count('registry_->bootstrap();') == 1 and fixture.count('seed(r_,repeat,cw,top);') == 1
  assert 'if(!c->constructor_component_)' in fixture and 'cc::HostBoundary hardware;' in fixture
  assert 'phase==37&&r_.calls().size()==37&&r_.translation_count()==135' in fixture
  assert '!ledger.completed()&&!ledger.failed()' in fixture and 'records.reserve(37)' in fixture
  assert fixture.index('context.registry().finish()') < fixture.index('Registry actual owner cleanup incomplete')
  assert 'Bounded37 cleanup only; no replay' in fixture
  assert 'AFTER' not in fixture
  S = load(R/'tools/analysis/pe.py', 'constructor_native_source_pe')
  game = S.PEImage(pin(R/'MW3/Mech3.exe', '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
  def physical(a, n): return game.read(game.rva_range(a-game.image_base, n)[0], n)
  rows = re.findall(r'\{(\d+),(\d+),(\d+),(true|false),(true|false),\{([0-9,]+)\}\}', pin(base/'preparation-r7/literals.hpp').read_text())
  assert len(rows) == 1401
  for a, n, pop, call, ret, raw in rows:
   opcode = bytes(int(x) for x in raw.split(','))
   assert len(opcode) == int(n) and physical(int(a), int(n)) == opcode
   counts['whole_physical_source_instruction_rows'] += 1
  for row in p['selected_order']:
   assert physical(row['slot'], 4) == struct.pack('<I', row['entry'])
   counts['actual_selected_ledger_slots'] += 1
  assert [x['slot'] for x in p['selected_order']] == sorted(x['slot'] for x in p['selected_order'])
  for pc, thunk, slot, raw in [(0x58af12,0x5abd26,0x5bb4bc,0x80000337),(0x58af6a,0x5abd26,0x5bb4bc,0x80000337),(0x58af9a,0x5abd1a,0x5bb4c8,0x80000339),(0x58f2a2,0x5abd26,0x5bb4bc,0x80000337),(0x45b80e,0x5abd26,0x5bb4bc,0x80000337)]:
   call = physical(pc,5)
   assert call[0] == 0xe8 and pc+5+struct.unpack_from('<i',call,1)[0] == thunk
   assert physical(thunk,6) == b'\xff\x25'+struct.pack('<I',slot) and physical(slot,4) == struct.pack('<I',raw)
   counts['actual_constructor_MFC_call_thunk_IAT_relations'] += 1
  C = load(R/'tools/m4-tree-review/amd64_coff.py', 'constructor_native_coff')
  PE = load(R/'tools/m4-tree-review/review_mfc1168_native_prelaunch_v4.py', 'constructor_native_image')
  N = load(R/'tools/m4-tree-review/review_hypot_c1_controls_prelaunch_v2.py', 'constructor_native_directories')
  asm_names = {'mw34_constructor_hardware_call','mfc_connected_hardware_call'}
  for level, worker in b['workers'].items():
   image = PE.AMD64Image(pin(worker['path'],worker['sha256']).read_bytes())
   wd = Path(worker['path']).parent
   objects = [pin(x['path'],x['sha256']) for x in cb['levels'][level]['objects']]
   objects += [pin(sb['levels'][level]['object'],sb['levels'][level]['object_sha256']),pin(wd/'fixture.obj'),pin(wd/'mfc_component.obj'),pin(wd/'connected_hardware_boundary.obj')]
   definitions = {}
   for q in objects:
    sy,se = C.parse(q.read_bytes())
    for s in sy.values():
     if s['name'] in asm_names and s['section'] > 0: s['type'] = 32
    for s in sy.values():
     n = s['name']
     if s['section'] <= 0 or s['type'] != 32: continue
     selected = n.startswith('mw34_constructor_') or '@Component@m4_constructor_native@mw34@@' in n and not n.startswith('??$') or '@literal@m4_constructor_native@mw34@@' in n or '@m4_constructor_store_source@mw34@@' in n or '@SessionImpl@m4_onexit@mw34@@' in n and not n.startswith('??$') or '@Context@m4_mixed@mw34@@' in n and not n.startswith('??$') or n in asm_names or n == 'main' or n.startswith(('?growth_and_cleanup@','?constructor_sink@','?projection@DirectPhaseWriter@','?image@DirectPhaseWriter@','mfc_connected_invoke_guarded'))
     if not selected: continue
     assert n not in definitions, (level,n,q)
     raw, rels = C.function(sy,se,n); definitions[n] = (q,raw,rels,se)
   candidates = {}
   for n,(q,raw,rels,se) in definitions.items():
    assert all(4<=x['type']<=9 or x['type']==11 and x['symbol']['section']>0 for x in rels),(level,n)
    matches = C.linked_candidates(image,raw,[dict(x,type=4) for x in rels])
    assert matches,(level,n,len(raw)); candidates[n] = matches
   for n,(q,raw,rels,se) in definitions.items():
    matches = candidates[n]
    for x in rels:
     target = x['symbol']['name']
     if 4<=x['type']<=9 and target in candidates:
      dest = {a for a,_ in candidates[target]}
      matches = [(a,z) for a,z in matches if a+x['offset']+4+x['type']-4+struct.unpack_from('<i',z,x['offset'])[0] in dest]
      assert matches,(level,n,target); counts['actual_linked_symbol_target_joins'] += 1
    candidates[n] = matches
    for address, actual in matches:
     for x in rels:
      if x['type'] != 11: continue
      sym = x['symbol']; assert se[sym['section']]['bytes'][sym['value']:sym['value']+8] == bytes(8)
      offset = struct.unpack_from('<i',actual,x['offset'])[0]-struct.unpack_from('<i',raw,x['offset'])[0]-sym['value']
      d = N.directories(image)[9]
      start,end,_,_,zero,_ = struct.unpack('<4Q2I',N.image_bytes(image,image.image_base+d[0],40))
      assert offset>=0 and offset+sym['value']+8<=end-start+zero and N.image_bytes(image,start+offset+sym['value'],8)==bytes(8)
      counts['actual_initialized_TLS_cells'] += 1
    links.append(dict(level=level,object=str(q),symbol=n,whole_bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),addresses=[a for a,_ in matches]))
    counts['whole_linked_current_functions'] += 1
   assert sum(bool(re.fullmatch('mw34_constructor_game_f_[a-f0-9]+_body',n)) for n in definitions) == 33
   for prefix in ['?invoke@Impl@Component@','?dispatch@Impl@Component@','?borrow_constructor_mfc@SessionImpl@','?constructor_source_write@SessionImpl@','?constructor_owner_read@SessionImpl@','?constructor_scope@SessionImpl@','?invoke_selected_body@Context@','?constructor_entry@Context@']:
    assert any(n.startswith(prefix) for n in definitions), (level,prefix)
   for q,n in [(objects[34],'mw34_constructor_hardware_call'),(objects[-1],'mfc_connected_hardware_call')]:
    sy,se = C.parse(q.read_bytes()); symbols=[s for s in sy.values() if s['name']==n]
    assert len(symbols)==1 and symbols[0]['section']==1 and symbols[0]['value']==0
    raw=se[1]['bytes']; assert len(candidates[n])==1
    address=candidates[n][0][0]; d=N.directories(image)[3]
    actual=[e for e in struct.iter_unpack('<3I',N.image_bytes(image,image.image_base+d[0],d[1])) if image.image_base+e[0]==address]
    assert len(actual)==1 and image.image_base+actual[0][1]==address+len(raw)
    unwind=se[4]['bytes']; assert N.image_bytes(image,image.image_base+actual[0][2],len(unwind))==unwind
    counts['whole_native_ASM_unwind_relations'] += 1
   commands=[x for x in b['commands'] if any('lld-link' in a for a in x['argv']) and str(wd) in ' '.join(x['argv'])]
   assert len(commands)==1 and commands[0]['exit_code']==0
   args={str(Path(x)).resolve().as_posix().casefold() for x in commands[0]['argv'] if not x.startswith('/')}
   for q in p['levels'][level]['objects']+[p['levels'][level]['component_library'],p['levels'][level]['service_library']]:
    assert Path(q).resolve().as_posix().casefold() in args
    counts['current_linker_selected_inputs'] += 1
   for role,paths in worker['compiler_dependencies'].items():
    for q in paths:
     assert str(pin(q)) in b['files']; counts['actual_consumed_compiler_headers'] += 1
   assert str(pin(sb['levels'][level]['forced_registry_header'])) in sb['levels'][level]['actual_header_dependencies']
   print(json.dumps(dict(level=level,whole_functions=len(definitions))),flush=True)
  pin(__file__);pin(sys.executable);pin(R/'tools/m4-constructor-native/run_fixture.py')
  for q,h in list(pins.items()): pin(q,h)
  passed=True
 except BaseException:
  (out/'failure.txt').write_text(traceback.format_exc()); raise
 finally:
  d=dict(passed=passed,scope='Independent whole physical/source/link admission for exactly two bounded constructor37 workers; captures, literal equivalence, refusal controls and carried144 acceptance remain separate',preparation_sha256=PH,build_sha256=BH,counts=dict(counts),whole_linked_functions=links,worker_or_reader_opened=False,initializer_credit=0,files=pins)
  q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=passed,path=str(q),sha256=hashlib.sha256(q.read_bytes()).hexdigest())))
if __name__=='__main__':main(sys.argv[1])
