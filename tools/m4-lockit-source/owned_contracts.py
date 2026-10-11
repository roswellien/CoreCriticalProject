"""Exact static affine owner/publication contracts of four normal constructors.

This is a source-only dataflow pass over exact original bytes. The admitted
header-null path follows each literal allocator return, global reload and
instance publication. No candidate AFTER, owner alias or native guard is read.
"""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];PINS={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);assert h is None or h==v;PINS[str(p)]=v;return p
def main(name):
 out=ROOT/'reports/m4-lockit-source'/name;assert not out.exists();out.mkdir(parents=True);source=json.loads(pin(ROOT/'reports/m4-lockit-source/recovery-r1/instruction-contracts.json','c102e277742f2cd6e2a352f9e40f44f7d7d2ea1107d8bde242d103b586e75f25').read_bytes());rows={r['pc']:r for r in source['instructions']};owned=[];pubs=[];traces=[];static_fields=[]
 for root in source['roots']:
  entry=root['entry'];obj=root['objects'][0]['address'];header=root['header_global'];counter=root['header_counter'];frame=root['normal_FS'];alloc={r['CALL_pc']:r for r in source['allocations']if r['root']==entry};regs={'ecx':('static',obj)};memory={('static',header):0,('static',counter):0};provenance={};local=[]
  def address(op):
   if op['kind']!='memory' or op['segment']=='fs':return None
   if not op['terms']:return ('static',op['displacement'])
   if len(op['terms'])==1 and op['terms'][0]['scale']==1:
    token=regs.get(op['terms'][0]['register'])
    if isinstance(token,tuple):return token[:-1]+(token[-1]+op['displacement'],)
   return None
  def value(op):
   if op['kind']=='register':return regs.get(op['register'])
   if op['kind']=='immediate':return op['value']
   if op['kind']=='memory':return memory.get(address(op))
  for pc in sorted(p for p in rows if frame['entry']<=p<=frame['ret']):
   r=rows[pc];op=r['mnemonic'];args=r['decoded_operands'];before=dict(regs)
   if op=='call':
    if pc in alloc:regs['eax']=('owner',pc,0);provenance[pc]=dict(kind='literal_allocator_return',CALL_pc=pc,requested=alloc[pc]['requested'])
    else:regs.pop('eax',None)
    regs.pop('ecx',None);regs.pop('edx',None)
   elif op=='mov':
    dest,src=args;v=value(src)
    if src['kind']=='memory':
     a=address(src)
     if a and a[0]=='owner':raise ValueError('Unexpected new-root owned source read '+hex(pc))
    if dest['kind']=='register':regs[dest['register']]=v
    elif dest['kind']=='memory':
     a=address(dest)
     if a:
      if a[0]=='owner':
       _,call,offset=a;request=alloc[call]['requested'];assert 0<=offset and offset+dest['bits']//8<=request;item=dict(root=entry,pc=pc,write=True,bytes=dest['bits']//8,owner_root=entry,owner_CALL_pc=call,owner_offset=offset,source_operand=dest,source_value=v,source_register_bindings=before);owned.append(item);local.append(item)
      if a[0]=='static':
       addr=a[1]
       if isinstance(v,tuple)and v[0]=='owner'and v[2]==0 and addr in(header,obj+4):
        call=v[1];assert addr==(header if alloc[call]['conditional']else obj+4);pubs.append(dict(root=entry,CALL_pc=call,requested_size=alloc[call]['requested'],object=obj,publication=addr,publication_PC=pc,publication_owner=None,owner_root=0,owner_CALL_pc=0,owner_offset=0,source_register_bindings=before))
       if obj<=addr<obj+16 or addr in(header,counter):static_fields.append(dict(root=entry,pc=pc,address=addr,write=True,bytes=dest['bits']//8,source_value=v))
      memory[a]=v
   elif op=='xor'and len(args)==2 and args[0]==args[1]and args[0]['kind']=='register':regs[args[0]['register']]=0
   elif op=='lea'and args[0]['kind']=='register':regs[args[0]['register']]=address(args[1])
   elif op in('add','sub','inc','dec')and args and args[0]['kind']=='register':
    name=args[0]['register'];old=regs.get(name);amount=value(args[1])if len(args)>1 else 1
    if isinstance(old,int)and isinstance(amount,int):regs[name]=old+amount*(1 if op in('add','inc')else -1)
    else:regs.pop(name,None)
   elif op=='pop'and args and args[0]['kind']=='register':regs.pop(args[0]['register'],None)
  assert len(local)==8 and len([p for p in pubs if p['root']==entry])==2
  traces.append(dict(root=entry,body=frame['entry'],ret=frame['ret'],object=obj,header=header,counter=counter,initial_header_null_required=True,initial_header_counter_zero_required=True,allocation_calls=list(alloc),affine_owner_accesses=local,final_symbolic_header=memory[('static',header)],final_symbolic_object_sentinel=memory[('static',obj+4)],final_symbolic_object_count=memory[('static',obj+12)],final_symbolic_header_counter=memory[('static',counter)]))
 assert len(owned)==32 and len(pubs)==8 and all(r['write']and r['bytes']==4 for r in owned)
 # These tuples map directly to the frozen native struct field order. No
 # wildcard root, PC, width, generation, requested offset or publication exists.
 fsowned=[{k:r[k]for k in('root','pc','write','bytes','owner_root','owner_CALL_pc','owner_offset')}for r in owned]
 fsinputs=[{k:r[k]for k in('root','CALL_pc','requested_size','object','publication','publication_PC','publication_owner','owner_root','owner_CALL_pc','owner_offset')}for r in pubs]
 decl='constexpr FsOwnedAccess lockit_owned_accesses[]{\n'+''.join('{'+','.join(str(int(r[k]))for k in('root','pc','write','bytes','owner_root','owner_CALL_pc','owner_offset'))+'},\n'for r in fsowned)+'};\nconstexpr FsInput lockit_fs_inputs[]{\n'+''.join('{'+','.join(str(int(r[k]))for k in('root','CALL_pc','requested_size','object','publication','publication_PC','owner_root','owner_CALL_pc','owner_offset'))+'},\n'for r in fsinputs)+'};\n'
 def emit(name,value):
  p=out/name;p.write_text(json.dumps(value,indent=2)+'\n');pin(p)
 emit('shared-owner-accesses.json',fsowned);emit('allocation-inputs.json',fsinputs);emit('affine-source-derivations.json',traces);emit('static-field-writes.json',static_fields);p=out/'native-declarations.inc';p.write_text(decl);pin(p);pin(__file__);report=dict(passed=True,scope='Exact affine static normal owner-access/publication contracts from original bytes and admitted source header-null inputs; no candidate state/guard used',owned_accesses=32,publications=8,owner_reads=0,cross_root_owner_accesses=0,all_requested_offset_bounds_checked=True,all_publications_static=True,new_MfcRootInput_publication_must_be_zero=True,native_struct_field_order=dict(FsOwnedAccess=['root','pc','write','bytes','owner_root','owner_CALL_pc','owner_offset'],FsInput=['root','CALL_pc','requested_size','object','publication','publication_PC','owner_root','owner_CALL_pc','owner_offset']),actual_original_prefix_confirmation_pending=True,initializer_credit=False,files=PINS);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),owned_accesses=32,publications=8)))
if __name__=='__main__':main(sys.argv[1])
