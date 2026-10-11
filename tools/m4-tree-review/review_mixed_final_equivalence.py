"""Physical mixed-control/current130 library applicability; no capture reads."""
from pathlib import Path
import difflib, hashlib, json, re, struct, subprocess, sys
sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[2]
NATIVE = '1f704ba8254433b9ae7387a53322c33b4db536b99eb79363ff71e54169cb65f3'
OLD_METADATA = '68498a9eaaf924205e11bbf30fbaa355380afc528b892c6739f9a1d199731d06'
def sha(p):
 with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def need(v, message):
 if not v: raise ValueError(message)
def main(name):
 out = R / 'reports/m4-tree-review' / name
 need(not out.exists(), 'Fresh independent applicability receipt')
 out.mkdir(parents=True)
 pins, rows, declarations = {}, [], []
 def pin(p, expected=None):
  p = Path(p).resolve(); actual = sha(p)
  need(expected is None or actual == expected, 'Physical input identity: ' + str(p))
  need(str(p) not in pins or pins[str(p)] == actual, 'Stable physical input')
  pins[str(p)] = actual
  return p
 def read(p, expected=None): return json.loads(pin(p, expected).read_bytes())
 cbp = R / 'reports/m4-tree-review/mixed-controls-build-r5/build.json'
 fbp = R / 'reports/m4-joint-startup130/build-r2/build.json'
 cep = R / 'reports/m4-tree-review/mixed-controls-execution-r3/report.json'
 cb = read(cbp, '3975da7bc33a214275bf997d0bfafdf2bcc60e376dc8cadfc17223ff1f682ab9')
 fb = read(fbp, '1a51ee4bbba62c9505eb1ffae7dee2538cc68297708119a1fa3485769a1cde53')
 ce = read(cep, '90e014b6d7018513452dfdc6d941f492e37fe45f9edfa290de259a0bbe3c2b9f')
 cp = read(cb['preparation'], cb['preparation_sha256'])
 fp = read(fb['preparation'], fb['preparation_sha256'])
 native = read(fp['native_preparation'], NATIVE)
 need(cb['passed'] and fb['passed'] and ce['passed'], 'Actual current builds and controls writers passed')
 need(cp['native_preparation_sha256'] == fp['native_preparation_sha256'] == ce['native_preparation_sha256'] == NATIVE, 'Exact corrected19 library lineage')
 need(ce['build_sha256'] == sha(cbp), 'Actual controls executed this compiled build')
 source = Path(native['native_library']).resolve()
 native_dir = Path(native['native_include']).resolve()
 need(Path(cp['native_library']).resolve() == Path(fp['native_library']).resolve() == source, 'Same actual compiled library source')
 for p, h in native['files'].items():
  if Path(p).resolve().parent == native_dir: pin(p, h)
 cdir, fdir = Path(cp['connected_include']), Path(fb['preparation']).parent
 ch = pin(cdir / 'registration_contract.hpp').read_bytes()
 fh = pin(fdir / 'registration_contract.hpp').read_bytes()
 need(ch == fh and b'array<unsigned,101>' in ch and b'array<unsigned,29>' in ch, 'Whole101-root/29-extra-page registration header exact')
 cprotocol = pin(cdir / 'joint_protocol.hpp').read_text()
 fprotocol = pin(fdir / 'joint_protocol.hpp').read_text()
 packed = lambda x: x.split('#pragma pack(push,1)', 1)[1].split('#pragma pack(pop)', 1)[0]
 need(packed(cprotocol) == packed(fprotocol), 'Whole packed fixed native ABI exact')
 c_entries = next(l for l in cprotocol.splitlines() if ' entries{' in l)
 f_entries = next(l for l in fprotocol.splitlines() if ' entries{' in l)
 cent = [int(v, 16) for v in re.findall(r'0x[0-9a-f]+', c_entries)]
 fent = [int(v, 16) for v in re.findall(r'0x[0-9a-f]+', f_entries)]
 need(cent == cp['selected_roots'] == [0x4df610,0x4e0710,0x4e0810,0x4e1ca0] and len(fent) == 130 and set(cent) <= set(fent), 'Actual selected4 is exact current130 subset')
 expected_protocol = cprotocol.replace(c_entries, f_entries).replace('void cosine(m4_runtime::Runtime &);void sincos', 'void cosine(m4_runtime::Runtime &);void compound_cosine(m4_runtime::Runtime &);void sincos')
 need(expected_protocol == fprotocol, 'Only exact selected-table and compound-cosine declaration protocol differences')
 cm = pin(cdir / 'native_main.cpp').read_text(); fm = pin(fdir / 'native_main.cpp').read_text()
 entry = lambda s: next(l for l in s.splitlines() if 'static void registration_entry(' in l)
 need(entry(cm) == entry(fm), 'Exact real Runtime callback synchronizes full CPU/State/FX at same library entry')
 replacements = [('phase==4&&r_.calls().size()==4&&r_.translation_count()==130','phase==130&&r_.calls().size()==133&&r_.translation_count()==131'),('records.reserve(125)','records.reserve(130)'),('{1,6,125,750,17,sizeof(Native)}','{1,6,130,780,17,sizeof(Native)}'),('records.size()==125','records.size()==130'),('seq==6&&total==750','seq==6&&total==780'),('total==750','total==780'),('125-root','130-root'),('750native','780native'),('125','130')]
 normalized = cm
 for old, new in replacements: normalized = normalized.replace(old, new)
 need(normalized == fm, 'Complete frontend difference is finite selected count/diagnostic schedule; no source guard differences')
 diff = out / 'frontend-declarations.diff'
 diff.write_text(''.join(difflib.unified_diff(cm.splitlines(True),fm.splitlines(True),str(cdir/'native_main.cpp'),str(fdir/'native_main.cpp')))+''.join(difflib.unified_diff(cprotocol.splitlines(True),fprotocol.splitlines(True),str(cdir/'joint_protocol.hpp'),str(fdir/'joint_protocol.hpp'))))
 pin(diff)
 ninja = pin('C:/Program Files/Microsoft Visual Studio/18/Community/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe')
 def linked(graph, folder, exe):
  line = next(l for l in graph.splitlines() if l.startswith('build '+exe+': CXX_EXECUTABLE_LINKER'))
  tokens = line.split(' ',3)[3].split(' |')[0].split()
  return {str((folder/Path(t.replace('$:',':').replace('$ ',' '))).resolve()).casefold() for t in tokens if t.endswith(('.obj','.lib'))}
 def object_node(graph, folder):
  token = str(source).replace(':','$:')
  line = next(l for l in graph.splitlines() if ': CXX_COMPILER_' in l and token in l)
  node = line[6:].split(': CXX_COMPILER_',1)[0]; i = graph.index(line)
  block = graph[i:graph.index('\nbuild ',i+1)]
  flags = next(l.strip() for l in block.splitlines() if l.strip().startswith('FLAGS ='))
  defines = next(l.strip() for l in block.splitlines() if l.strip().startswith('DEFINES ='))
  return node, pin(folder/node), flags, defines
 for level in ('O0','O2'):
  cw = pin(cb['workers'][level]['path'], cb['workers'][level]['sha256'])
  fw = pin(fb['workers'][level]['path'], fb['workers'][level]['sha256'])
  cg = pin(cw.parent/'build.ninja').read_text(); fg = pin(fw.parent/'build.ninja').read_text()
  co_inputs, fo_inputs = cp['objects'][level], fp['objects'][level]
  need(co_inputs == cb['workers'][level]['literal_objects'] and fo_inputs == fb['workers'][level]['objects'], 'Exact manifest/current link literal lists')
  need(len(co_inputs) == len(set(co_inputs)) == 396 and len(fo_inputs) == len(set(fo_inputs)) == 397 and set(co_inputs) < set(fo_inputs), '396 controls literal objects are exact397 final subset')
  added = list(set(fo_inputs)-set(co_inputs)); need(len(added) == 1 and 'm4-cosine-native' in added[0], 'Only new compound-cosine literal object outside controls')
  cl, fl = linked(cg,cw.parent,cw.name), linked(fg,fw.parent,fw.name)
  for q in fo_inputs:
   p = pin(q, fb['sources'][str(Path(q).resolve())]); need(struct.unpack_from('<H',p.read_bytes())[0] == 0x8664, 'AMD64 current literal object')
   need(str(p).casefold() in fl, 'Current literal actually linked')
   if q in co_inputs:
    need(cb['sources'][str(p)] == sha(p) and str(p).casefold() in cl, 'Same exact literal physically consumed by controls/final links')
  cn, co, cf, cd = object_node(cg,cw.parent); fn, fo, ff, fd = object_node(fg,fw.parent)
  need(cd == fd, 'Actual library compiler ISA macros exact')
  def alias(flags, expected):
   values = re.findall(r'/FI(\S+)',flags)
   need(len(values) == 1 and Path(values[0]).resolve() == expected.resolve(), 'Actual single forced registry header path')
   return flags.replace(values[0],'<byte-identical-level-registry-header>')
  cforced, fforced = cdir/level/'registry_build_bindings.hpp', fdir/level/'registry_build_bindings.hpp'
  need(pin(cforced).read_bytes() == pin(fforced).read_bytes(), 'Whole actually forced registry header exact; no metadata mask')
  need(alias(cf,cforced) == alias(ff,fforced), 'Actual compiler flags exact after byte-identical forced-header path alias')
  need(str(co).casefold() in cl and str(fo).casefold() in fl, 'Whole actual library COFF input linked into controls/final worker')
  cr, fr = co.read_bytes(), fo.read_bytes(); need(len(cr) == len(fr) >= 20, 'Whole library object extent')
  chead, fhead = struct.unpack_from('<HHIIIHH',cr), struct.unpack_from('<HHIIIHH',fr)
  different = [i for i,(x,y) in enumerate(zip(cr,fr)) if x != y]
  need(chead[0] == fhead[0] == 0x8664 and chead[1] == fhead[1] and chead[3:] == fhead[3:] and chead[5] == 0, 'Complete standard COFF header identity outside timestamp')
  need(set(different) <= set(range(4,8)) and cr[:4] == fr[:4] and cr[8:] == fr[8:], 'Every code/data/relocation/symbol byte exact; only TimeDateStamp4:8 may differ')
  dependencies = []
  for label, folder, node, header in [('controls',cw.parent,cn,cforced),('final130',fw.parent,fn,fforced)]:
   result = subprocess.run([str(ninja),'-t','deps',node],cwd=folder,capture_output=True,timeout=20,creationflags=0x08000000)
   need(result.returncode == 0, 'Actual recorded compiler dependency inventory')
   target = out/f'{level}-{label}-consumed-dependencies.txt'; target.write_bytes(result.stdout+result.stderr); pin(target)
   paths = [Path(l.strip()) for l in result.stdout.decode().splitlines()[1:] if l.strip()]
   need(paths and len(paths) == len(set(paths)), 'Distinct complete actual compiler dependency paths')
   actual = {str(pin(p)).casefold():sha(p) for p in paths}
   need(str(source).casefold() in actual and str(header.resolve()).casefold() in actual, 'Actual compiler consumed current native19 and exact forced header')
   dependencies.append({('<byte-identical-level-registry-header>' if p == str(header.resolve()).casefold() else p):h for p,h in actual.items()})
  need(dependencies[0] == dependencies[1], 'Every actual consumed library dependency physically equal with one header alias')
  # Frontend provenance fields are retained explicitly, separate from the exact
  # forced library header. They do not choose an older compiled library.
  cib = pin(cdir/level/'registration_bindings.inc').read_text()
  fib = pin(fdir/level/'registration_bindings.inc').read_text()
  need(cib.count('"Isolated literal formatter root"') == 4 and cib.count(OLD_METADATA) == 4, 'Only four frontend origin descriptions/preparation identities differ')
  need(cib.replace('"Isolated literal formatter root"','"Selected literal formatting/mixed initializer"').replace(OLD_METADATA,NATIVE) == fib, 'Entire frontend binding difference is four exact metadata pairs; target/ABI/root/body hashes exact')
  changed = [(i+1,c,f) for i,(c,f) in enumerate(zip(cib.splitlines(),fib.splitlines())) if c != f]
  need(len(changed) == 4, 'Exactly four declaration metadata rows')
  declarations.append(dict(level=level,source=str(cdir/level/'registration_bindings.inc'),target=str(fdir/level/'registration_bindings.inc'),differing_rows=[dict(line=i,controls=c,final=f) for i,c,f in changed]))
  rows.append(dict(level=level,controls_object=str(co),controls_object_sha256=sha(co),final_object=str(fo),final_object_sha256=sha(fo),whole_object_bytes=len(cr),actual_differing_offsets=different,only_permitted_difference=[4,8],all_non_timestamp_bytes_equal=True,code_data_relocation_symbol_bytes_equal=True,actual_compiler_dependencies=len(dependencies[0]),linked_common_literals=396,linked_final_literals=397,final_only_literal=added[0],compiler_flags_after_header_alias=alias(cf,cforced),ISA_defines=cd))
 pin(__file__)
 report = dict(passed=True,scope='Fresh physical corrected19 mixed-control to broad130 library/source/header/literal equivalence; controls byte validation and full semantic130 acceptance remain separate',controls_execution_sha256=sha(cep),controls_build_sha256=sha(cbp),bound_final_build_sha256=sha(fbp),bound_final_preparation_sha256=sha(fb['preparation']),native_preparation_sha256=NATIVE,levels=rows,frontend_metadata_differences=declarations,controls_roots=4,broad_roots=130,registration_roots=101,full_extra_page_header_count=29,linked_common_literal_COFFs_per_level=396,linked_final_literal_COFFs_per_level=397,level_registration_headers_byte_identical=True,full_registration_headers_byte_identical=True,fixed_ABI_byte_identical=True,actual_registration_callback_source_byte_identical=True,complete_library_consumed_dependencies_equal=True,whole_library_COFF_non_timestamp_equal=True,only_permitted_COFF_difference=[4,8],finite_frontend_metadata_rows_per_level=4,controls_capture_validation_claimed=False,whole_worker_binary_equal_claimed=False,full130_fault_history_claimed=False,capture_payload_read=False,initializer_credit=0,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),physical_inputs=len(pins),levels=rows)))
if __name__ == '__main__': main(sys.argv[1])
