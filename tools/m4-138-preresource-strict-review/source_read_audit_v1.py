"""Strict source/cold-import read policy, no metadata-based payload fallback."""
from pathlib import Path
import os,sys
class Reads:
 def __init__(self,declared,out):
  self.declared={str(Path(p).resolve()):h for p,h in declared.items()};self.out=Path(out).resolve();self.verified_raw={};self.hashing=set();self.reads=set();self.pyc_refusals=set()
 def audit(self,event,args):
  if event!='open'or not args or not isinstance(args[0],(str,bytes,os.PathLike)):return
  p=Path(os.fsdecode(args[0])).resolve();mode=args[1]if len(args)>1 else None;flags=args[2]if len(args)>2 else 0
  reading=isinstance(mode,str)and'r'in mode or mode is None and isinstance(flags,int)and not(flags&3)
  if not reading:return
  if p.suffix.lower()=='.pyc':self.pyc_refusals.add(str(p));raise FileNotFoundError('Cached bytecode refused; exact declared .py required: '+str(p))
  if p.suffix.lower()in('.mwb','.mwi','.zip')or p.name in('transport.json','bundle.json'):raise PermissionError('No archive/transport read')
  if str(p)not in self.declared and str(p)not in self.verified_raw and str(p)not in self.hashing and not p.is_relative_to(self.out):raise PermissionError('Undeclared direct read/import: '+str(p))
  self.reads.add(str(p))
 def install(self):sys.addaudithook(self.audit)
 def begin_hash(self,p,expected):
  p=Path(p).resolve();key=str(p)
  if key in self.declared and self.declared[key]!=expected:raise ValueError('Root ordinary declaration identity differs')
  # For raw inputs, caller establishes exact same-case streamed declaration
  # before granting this hash-only open. No analysis runs during file_digest.
  self.hashing.add(key)
 def end_hash(self,p,expected,actual):
  key=str(Path(p).resolve());self.hashing.discard(key)
  if actual!=expected:raise ValueError('Whole physical hash mismatch')
  if key not in self.declared and not Path(p).resolve().is_relative_to(self.out):self.verified_raw[key]=actual
