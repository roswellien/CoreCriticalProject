"""Retain accepted131 independent inherited review at the current physical schedule."""
from pathlib import Path
import ast,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
 with p.open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def main():
 out=ROOT/'reports/m4-startup138-paired/inherited-review-preparation-r1';assert not out.exists();out.mkdir()
 parent=ROOT/'tools/m4-tree-review/review_original131_combined_v2.py';original=parent.read_text();text=original;hunks=[]
 replacements=[
  ('reports/m4-startup131-original/validation-r2/fresh-cdecl.json','reports/m4-startup138-original/original-validation-r3/fresh-cdecl.json'),
  ('tools/m4-startup131-original/format_source_v4.py','tools/m4-startup138-original/format_source_v4_r5.py'),
  ('tools/m4-startup131-original/current_inherited_source_v2.py','tools/m4-startup138-original/current_inherited_source_v2_r6.py'),
  ('tools/m4-startup131-original/tree_source.py','tools/m4-startup138-original/tree_source_r5.py'),
  ('reports/m4-startup131-original/preparation-r4/format_observer_x86.asm','reports/m4-startup138-original/preparation-r8/format_observer_x86.asm'),
  ('tree_phase==79','tree_phase==83'),
  ("case['phase']==79 and s['phase']==79","case['phase']==83 and s['phase']==83"),
  ('asserted79','asserted83'),
  ('current original131','current original138'),
 ]
 for old,new in replacements:
  assert old in text,old
  while old in text:
   position=text.index(old);hunks.append(dict(position=position,old=old,new=new));text=text[:position]+new+text[position+len(old):]
 restored=text
 for row in reversed(hunks):
  p=row['position'];assert restored[p:p+len(row['new'])]==row['new'];restored=restored[:p]+row['old']+restored[p+len(row['new']):]
 assert restored==original;ast.parse(text)
 tool=ROOT/'tools/m4-startup138-paired/review_inherited_current.py';assert not tool.exists();tool.write_text(text)
 pins={str(p):sha(p)for p in (parent,tool,Path(__file__).resolve(),Path(sys.executable))}
 p=out/'hunks.json';p.write_text(json.dumps(hunks,indent=2)+'\n');pins[str(p)]=sha(p)
 p=out/'report.json';p.write_text(json.dumps(dict(passed=True,exact_inverse_restores_accepted131_reviewer=True,scope='Only current physical cdecl/source/observer paths, tree phase83 and scope text changed; inherited131 continuity retained as historical proof, new widget review separate',hunks=len(hunks),reviewer_executed=False,capture_archive_opened=False,initializer_credit=0,files=pins),indent=2)+'\n');print(sha(p))
if __name__=='__main__':main()
