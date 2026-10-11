"""Strengthen the immutable compile-only component before any execution."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2];p=Path(__file__).parent
base=p/'component.cpp';manifest=json.loads((R/'reports/m4-widget-native/preparation-r1/report.json').read_text());assert hashlib.sha256(base.read_bytes()).hexdigest()==manifest['files'][str(base.resolve())]
s=base.read_text()
s=s.replace('FS_cursor{},generation{}','FS_cursor{},operand_cursor{},generation{}')
old='else require(v.projected&&v.projected==services.resolve_import(v),"Current caller-owned registry/CRT import resolution");'
new='else if(k==4)require(v.projected==0x78004a36&&v.projected==services.resolve_import(v),"Exact current accepted CRT onexit provider route");else require(v.projected==v.raw,"Unused cold import stays raw and is never admitted");'
assert s.count(old)==1;s=s.replace(old,new)
old='void access(unsigned pc,unsigned a,std::uint64_t value,unsigned width,bool writing){require(width&&width<=4&&accesses.size()<300000,"Finite widget source scalar/access extent");accesses.push_back({pc,a,value,width,unsigned(writing)});}'
new='''void access(unsigned pc,unsigned a,std::uint64_t value,unsigned width,bool writing){require(width&&width<=4&&accesses.size()<300000&&operand_cursor<root->operand_count,"Finite widget source scalar/access extent");const auto&e=literal::operands[root->operand_begin+operand_cursor];const auto expected=e.role==1?unsigned(std::int64_t(root_frame)+e.offset):e.role==2?r.fs_base().value:unsigned(e.offset);require(pc==e.pc&&a==expected&&width==e.width&&writing==e.writing,"Exact causal source PC/address role/offset/width/direction order; no value oracle");accesses.push_back({pc,a,value,width,unsigned(writing)});++operand_cursor;}'''
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace('n==4&&a==s.gpr.rsp.dword&&value==pc+literal::instruction(pc)->size','n==4&&a==s.gpr.rsp.dword-4&&value==pc+literal::instruction(pc)->size')
s=s.replace('for(unsigned k=3;k<6;++k)if(target==input.imports[k].projected){','for(unsigned k=3;k<6;++k)if(target==input.imports[k].projected){require(k==4&&!tail,"Only genuine source onexit import is admitted; unused imports remain cold");')
s=s.replace('GDI_cursor=virtual_cursor=FS_cursor=0;','GDI_cursor=virtual_cursor=FS_cursor=operand_cursor=0;')
s=s.replace('FS_cursor==root->FS_count,"Complete actual root','FS_cursor==root->FS_count&&operand_cursor==root->operand_count,"Complete actual root')
s=s.replace('require(!active&&!cleaned,"Serial explicit owned-font cleanup");','require((!active||failed)&&!cleaned,"Serial explicit owned-font cleanup");')
s=s.replace('dump("manual-font-cleanup/row.bin",row.data(),sizeof(row));dump("manual-font-cleanup/hardware.bin",&hardware,sizeof(hardware));','const auto stem="manual-font-cleanup/"+std::to_string(it->generation);dump(stem+"-row.bin",row.data(),sizeof(row));dump(stem+"-hardware.bin",&hardware,sizeof(hardware));')
s=s.replace('std::string p(stem);auto c=cpu(s);','std::string p=(root?"root-"+std::to_string(root->root)+"/":"bootstrap/")+std::string(stem);auto c=cpu(s);')
s=s.replace('s.gpr.rcx.dword==instance,"Exact ordered virtual','s.gpr.rcx.dword==instance,"Exact ordered virtual')
(p/'component_v2.cpp').write_text(s)
print(hashlib.sha256(s.encode()).hexdigest())
