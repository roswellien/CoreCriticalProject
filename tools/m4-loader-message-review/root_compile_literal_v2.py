"""Four admitted c-only commands, fresh build outputs; no link/load/evaluation."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,sys,traceback
R=Path(__file__).resolve().parents[2]
PREP_SHA='3f132e4b76ec369a7b1a88157882d6d1025de81003a7c3c62d43c1035df6a5f0'
RECIPE_SHA='140001697ccf04aed0b8a043de6155ab514ff9ef47954367a19e95d2804e86f4'
def main(admission,admission_sha,name):
 assert name.startswith('literal-code-build-r')and Path(name).name==name
 out=R/'reports/m4-loader-message-review'/name;assert not out.exists();out.mkdir();pins={};runs=[];passed=False
 def sha(p):
  with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip');v=sha(p);assert h is None or h==v,(p,h,v);assert pins.setdefault(str(p),v)==v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 try:
  admission=pin(admission,admission_sha);a=read(admission);assert a['passed']is True and a['scope_identity']=='message_literal_compile_only'and a['preparation_sha256']==PREP_SHA
  for p,h in a['files'].items():pin(p,h)
  folder=R/'reports/m4-loader-message-review/persistent-code-preparation-r2';prep=read(folder/'report.json',PREP_SHA)
  for p,h in prep['files'].items():pin(p,h)
  recipe=read(folder/'ROOT-compile-and-admission-recipe.json',RECIPE_SHA)
  cl=pin(shutil.which('cl.exe'));assert cl==Path(recipe['compiler']).resolve()and a['files'].get(str(cl))==sha(cl),'Exact reviewed current compiler/environment'
  table=R/'reports/m4-loader-message-review/native-preparation-r1/source_table.hpp';old=read(table.parent/'report.json','de099653af14f330b58d4e4a9753b9e4ab4712f4c18fbd147a7393a396406f16');pin(table,old['files'][str(table)])
  inverse=pin(folder/'native_provider_literal_v1.cpp').read_text()
  for d in reversed(read(folder/'exact-native-source-inverse.json')):assert inverse.count(d['after'])==1;inverse=inverse.replace(d['after'],d['before'])
  assert inverse==pin(R/'tools/m4-loader-message-review/native_provider.cpp').read_text()
  objects=recipe['literal_link_inputs'];assert set(objects)=={'O0','O2'}
  for rows in objects.values():
   assert {x['body']for x in rows}=={'f_10001000','f_10001740'}
   for v in rows:pin(v['path'],v['sha256'])
  # Commands retain every exact reviewed recipe argument except fresh /Fo and
  # add dependency metadata. There is no linker or executed artifact command.
  for level in('O0','O2'):
   dst=out/level;dst.mkdir()
   for original in recipe['compile_commands'][level]:
    assert original[0]==recipe['compiler']and '/c'in original and '/LD'not in original and '/link'not in original
    source=Path(original[-1]);pin(source);stem=source.stem;obj=dst/(stem+'.obj');deps=dst/(stem+'.dependencies.json')
    command=[str(cl)]+[('/Fo'+str(obj))if x.startswith('/Fo')else x for x in original[1:]]+['/sourceDependencies',str(deps)]
    result=subprocess.run(command,cwd=R,capture_output=True,timeout=120)
    stdout=dst/(stem+'.stdout');stderr=dst/(stem+'.stderr');stdout.write_bytes(result.stdout);stderr.write_bytes(result.stderr);pin(stdout);pin(stderr)
    runs.append(dict(level=level,command=command,exit_code=result.returncode,stdout=str(stdout),stderr=str(stderr)))
    assert result.returncode==0,(level,stem,result.returncode)
    pin(obj);dependency=read(deps);data=dependency['Data'];assert Path(data['Source']).resolve()==source.resolve()
    headers=data['Includes'];assert headers and all(type(p)is str and Path(p).is_absolute()for p in headers);assert not data['ImportedModules']and not data['ImportedHeaderUnits']
    for p in headers:pin(p)
    if stem=='native_provider_literal_v1':assert table.resolve()in{Path(p).resolve()for p in headers}
    assert (folder/'literal_owner_v1.hpp').resolve()in{Path(p).resolve()for p in headers}
    runs[-1].update(object=str(obj),object_sha256=sha(obj),dependency_json=str(deps),dependency_count=len(headers),compiler_dependencies=headers)
  assert len(runs)==4
  pin(__file__);pin(Path(__file__).with_suffix('.ps1'));pin(sys.executable)
  for p,h in pins.items():assert sha(p)==h
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  q=out/'report.json';q.write_text(json.dumps(dict(passed=passed,scope='ROOT-admitted four existing MSVC compile-only objects; literal objects pinned, no linking or execution',preparation_sha256=PREP_SHA,recipe_sha256=RECIPE_SHA,commands=runs,compile_commands_completed=len(runs),complete_parent_source_inverse=True if passed else False,full_actual_header_dependencies_pinned=True if passed else False,linker_invoked=False,DLL_loaded=False,source_evaluator_invoked=False,worker_executed=False,canonical_reader_opened=False,new_lift=False,new_install=False,initializer_credit=0,accepted_function_credit=0,files=pins),indent=2)+'\n');print(sha(q))
 if not passed:raise SystemExit(1)
if __name__=='__main__':main(Path(sys.argv[1]),sys.argv[2],sys.argv[3])
