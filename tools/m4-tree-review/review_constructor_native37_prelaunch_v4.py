"""Independently admit the finite constructor FS repair and current whole link.

No worker or archive reader is opened by this review.
"""
from pathlib import Path
import hashlib, json, struct, sys
sys.dont_write_bytecode = True


def review_finite_constructor_FS(pin, read, base, sp, physical, counts):
    old = base / 'service-preparation-r4'
    current = base / 'service-preparation-r5'
    frames = [(0x459b80, 0x5b2d88, 0x459d9d),
              (0x4bf910, 0x5b7898, 0x4bfb82),
              (0x4c0310, 0x5b7978, 0x4c0506),
              (0x4c0570, 0x5b7998, 0x4c0766),
              (0x58aec0, 0x5ba08b, 0x58afd2)]
    contracts = json.loads(pin(current / 'constructor-FS-contracts.json').read_bytes())
    wanted = [dict(entry=e, read=e+7, install=e+14, handler=h, restore=r)
              for e, h, r in frames]
    assert contracts['frames'] == wanted
    assert contracts['roots'] == [0x4103f0, 0x410440, 0x459b40]
    for e, handler, restore in frames:
        assert physical(e, 2) == b'\x6a\xff'
        assert physical(e+2, 5) == b'\x68' + struct.pack('<I', handler)
        assert physical(e+7, 7) == b'\x64\xa1\0\0\0\0\x50'
        assert physical(e+14, 7) == b'\x64\x89\x25\0\0\0\0'
        assert physical(restore, 7) == b'\x64\x89\x0d\0\0\0\0'
        counts['whole_physical_constructor_FS_frame_forms'] += 1

    cases = ''.join('case 0x%x:handler=0x%x;break;' % (e+14, h)
                    for e, h, _ in frames)
    expected = [('locale_batch.hpp',
                 'bool fs_admitted_{};',
                 'bool fs_admitted_{};unsigned constructor_source_root_{};')]
    before = ' if(install==source_accesses_.rend()||install->pc<0x78000000||!instruction(install->pc)||\n     runtime.memory().load<unsigned>({head+4})!=0x7800ef03)\n   deny("Only an accepted original CRT normal frame may nest the owned guest FS chain",head);'
    after = ''' bool constructor_frame=false;
  if(install!=source_accesses_.rend()&&(constructor_source_root_==0x4103f0||constructor_source_root_==0x410440||constructor_source_root_==0x459b40)){
   unsigned handler{};switch(install->pc){''' + cases + '''default:break;}
   if(handler&&head>=0x20001000&&std::uint64_t(head)+12<=0x20002000){
    std::array<std::byte,12>actual{};runtime.memory().read({head},actual);
    constructor_frame=runtime.memory().load<unsigned>({head+4})==handler&&
     std::equal(actual.begin(),actual.end(),upper_expected_.begin()+head-0x20001000);
   }
  }
  if(!constructor_frame&&(install==source_accesses_.rend()||install->pc<0x78000000||!instruction(install->pc)||
     runtime.memory().load<unsigned>({head+4})!=0x7800ef03))
   deny("Only an accepted original CRT or exact current constructor source frame may nest the owned guest FS chain",head);'''
    expected.append(('fs_operations.inc', before, after))
    expected += [
        ('fs_operations.inc',
         ' const auto native_input=fs_native_input_;const auto admitted=fs_admitted_;',
         ' const auto native_input=fs_native_input_;const auto admitted=fs_admitted_;const auto constructor_root=constructor_source_root_;'),
        ('fs_operations.inc',
         '||native_input!=fs_native_input_||admitted!=fs_admitted_)',
         '||native_input!=fs_native_input_||admitted!=fs_admitted_||constructor_root!=constructor_source_root_)'),
        ('session_impl.inc',
         '  constructor_active_root_=entering?root:0;constructor_prior_read_={};constructor_prior_root_=0;++constructor_access_epoch_;',
         '''  require(binding->constructor_source_root_==(entering?0:root)&&binding->fs_expected_==m4_runtime::Runtime::seh_end&&r.memory().load<unsigned>(r.fs_base())==m4_runtime::Runtime::seh_end,"Exact restored source FS sentinel at balanced constructor scope endpoints");
  constructor_active_root_=entering?root:0;binding->constructor_source_root_=constructor_active_root_;constructor_prior_read_={};constructor_prior_root_=0;++constructor_access_epoch_;'''),
        ('session_impl.inc',
         ' void clear_constructor_scope()noexcept{constructor_active_root_=0;',
         ' void clear_constructor_scope()noexcept{binding->constructor_source_root_=0;constructor_active_root_=0;'),
        ('session_impl.inc',
         'binding->expected_store(address,raw.data(),bytes);',
         'binding->expected_store(address,raw.data(),bytes);if(address==r.fs_base().value){require(bytes==4,"Whole constructor FS source DWORD witness");binding->source_accesses_.push_back({pc,address,value,bytes,1});}'),
        ('session_impl.inc',
         '  sink("constructor-source-mirror-accesses.bin",std::as_bytes(std::span(constructor_accesses_)),user);',
         '  sink("constructor-source-mirror-accesses.bin",std::as_bytes(std::span(constructor_accesses_)),user);const std::array<unsigned,2> constructor_fs_scope{constructor_active_root_,b.constructor_source_root_};sink("constructor-FS-source-scope.bin",std::as_bytes(std::span(constructor_fs_scope)),user);')]
    delta = json.loads(pin(current / 'constructor-FS-deltas.json').read_bytes())
    assert delta == [dict(file=f, before=a, after=b) for f, a, b in expected]
    assert len(delta) == 8
    changed = set()
    for row in sp['source_relations']:
        parent = pin(row['parent'], row['parent_sha256'])
        child = pin(row['child'], row['child_sha256'])
        assert parent.parent == old and child.parent == current
        assert parent.name == child.name
        before_bytes, after_bytes = parent.read_bytes(), child.read_bytes()
        if row['unchanged']:
            assert before_bytes == after_bytes
            counts['whole_unchanged_finite_FS_service_inputs'] += 1
        else:
            changed.add(child.name)
            text = parent.read_text()
            for filename, a, b in expected:
                if filename == child.name:
                    assert text.count(a) == 1
                    text = text.replace(a, b, 1)
            assert text == child.read_text()
            counts['whole_exact_finite_FS_service_deltas'] += 1
    assert changed == {'locale_batch.hpp', 'fs_operations.inc', 'session_impl.inc'}
    assert counts['whole_unchanged_finite_FS_service_inputs'] == 71
    assert not sp['source_after_seed'] and not sp['native_executed']
    assert sp['actual_first_failure_sha256'] == 'ac147e114599064caa909c6949d381cfd3bd122dbf9823143a957604407e4555'
    failure = base.parents[0] / 'm4-tree-review/constructor-native37-failure-r1/report.json'
    d = json.loads(pin(failure, sp['actual_first_failure_sha256']).read_bytes())
    assert d['passed'] and d['reader_closed']
    for name in ('locale-fault.bin', 'locale-fault-reason.bin'):
        q = failure.parent / 'sequence-0/selected' / name
        pin(q, d['files'][str(q.resolve())])
    before_dir, after_dir = base / 'fixture-preparation-r3', base / 'fixture-preparation-r4'
    for q in before_dir.iterdir():
        if q.is_file() and q.suffix in ('.cpp', '.s', '.inc', '.hpp'):
            assert pin(q).read_bytes() == pin(after_dir / q.name).read_bytes()
            counts['whole_unchanged_constructor_fixture_sources'] += 1


p = Path(__file__).with_name('review_constructor_native37_prelaunch_v3.py')
scope = {'__file__': str(p), '__name__': 'materialize_constructor_finite_FS_review'}
exec(compile(p.read_text(), str(p), 'exec'), scope)
t = scope['t']


def one(a, b):
    global t
    assert t.count(a) == 1, a
    t = t.replace(a, b, 1)


for a, b in [
    ('5507c72aef7bcf8afdd7c2b6fe3a906f3c65da58e69cc555f0671670cf289ad9', 'fa3783ea0dd32723e8d2b7917d7847e5b1951408d699fc3d82e77af0364c404d'),
    ('8eacf3dfadf4d69f420683ad5abee7bdc4db645516e720ecd422f7310ec5f56e', '97d32f7dbf5003f3ec0c79d95b8cfa02729b099cf2f03288ff69a69f6be9efe4'),
    ('ccd92f92048563db7fe9de82d694179d5f43bec42b9e4ad32ff733934cbd74e5', '61d3107f4003741e07c9c31b3c9b0b9c3911563fc4370df71743ae63e0e3e761'),
    ('3ea775399bf76f6dc32f23f2f2610a73718a03e06c840536a6c1fa4703fd4e3a', 'edf6b8acdb6f957005d35ee972073f837ff1773228fb2651bff1d6fb4febbfee'),
    ('fixture-preparation-r3', 'fixture-preparation-r4'),
    ('fixture-build-r7', 'fixture-build-r8'),
    ('service-preparation-r4', 'service-preparation-r5'),
    ('service-build-r4', 'service-build-r5')]:
    assert a in t, a
    t = t.replace(a, b)
one("  for row in sp['source_relations']:",
    "  old_sp=read(base/'service-preparation-r4/report.json','ccd92f92048563db7fe9de82d694179d5f43bec42b9e4ad32ff733934cbd74e5')\n  for row in old_sp['source_relations']:")
one('  rows = re.findall(',
    '  review_finite_constructor_FS(pin,read,base,sp,physical,counts)\n  rows = re.findall(')
one("or n in asm_names or n == 'main'",
    "or n.startswith(('?fs_guard@Binding@m4_crt_locale_batch@','?fs_hook@Binding@m4_crt_locale_batch@','?guard@Binding@m4_crt_locale_batch@','?expected_store@Binding@m4_crt_locale_batch@')) or n in asm_names or n == 'main'")
one("   for prefix in ['?invoke@Impl@Component@',",
    "   for prefix in ['?fs_guard@Binding@m4_crt_locale_batch@','?fs_hook@Binding@m4_crt_locale_batch@','?expected_store@Binding@m4_crt_locale_batch@','?invoke@Impl@Component@',")
one("  pin(R/'tools/m4-tree-review/review_constructor_native37_prelaunch_v2.py');",
    "  pin(R/'tools/m4-tree-review/review_constructor_native37_prelaunch_v3.py');pin(R/'tools/m4-constructor-native/prepare_service_v6.py');pin(R/'tools/m4-tree-review/review_constructor_native37_prelaunch_v2.py');")
exec(compile(t, str(Path(__file__)), 'exec'), globals())
