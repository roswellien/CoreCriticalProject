"""Read-only physical PE export verification; no GetProcAddress/API execution."""
import hashlib
from pathlib import Path
import re
import struct


def need(value, why):
    if not value: raise ValueError(why)


def terminated(raw, encoding='ascii'):
    text=raw.decode(encoding)
    value,separator,tail=text.partition('\0')
    need(separator and all(c=='\0' for c in tail),'Complete bounded native export-proof string')
    return value


class PhysicalExports:
    def __init__(self, add):self.add=add;self.cache={}
    def get(self,path,digest,name):
        path=Path(path).absolute();need(re.fullmatch('[0-9a-f]{64}',digest),'Exact native image SHA256 spelling')
        self.add(path,digest);key=str(path).casefold(),digest
        if key not in self.cache:
            data=path.read_bytes();need(hashlib.sha256(data).hexdigest()==digest,'Native image physical digest')
            def u16(p):need(0<=p and p+2<=len(data),'Native PE word bounds');return struct.unpack_from('<H',data,p)[0]
            def u32(p):need(0<=p and p+4<=len(data),'Native PE DWORD bounds');return struct.unpack_from('<I',data,p)[0]
            pe=u32(0x3c);need(data[:2]==b'MZ' and data[pe:pe+4]==b'PE\0\0' and u16(pe+4)==0x8664,'Native physical AMD64 PE')
            opt=pe+24;need(u16(opt)==0x20b and u16(pe+20)>=120,'Native PE32+ export directory')
            sections=[]
            for i in range(u16(pe+6)):
                p=opt+u16(pe+20)+40*i;rva,length,fileoff=u32(p+12),u32(p+16),u32(p+20)
                need(fileoff+length<=len(data),'Native raw section physical bounds');sections.append((rva,length,fileoff))
            def at(rva,size=1):
                hits=[off+rva-start for start,length,off in sections if start<=rva and rva+size<=start+length]
                need(len(hits)==1,'Unique physical native export RVA');return hits[0]
            def text(rva):
                p=at(rva);ends=[p+min(4096,start+length-rva) for start,length,off in sections if start<=rva<start+length]
                need(len(ends)==1,'One bounded native export string extent');end=data.find(b'\0',p,ends[0])
                need(end>=p,'Terminated physical native export string');return data[p:end].decode('ascii')
            directory,length=u32(opt+112),u32(opt+116);p=at(directory,40)
            count,names,functions,name_table,ordinals=(u32(p+x) for x in (20,24,28,32,36))
            need(0<count<=65536 and 0<names<=65536,'Bounded physical native export tables');exports={}
            for i in range(names):
                title=text(u32(at(name_table+4*i,4)));index=u16(at(ordinals+2*i,2))
                need(index<count and title not in exports,'Unique physical export name/ordinal')
                rva=u32(at(functions+4*index,4));exports[title]=(rva,text(rva) if directory<=rva<directory+length else '')
            self.cache[key]=exports,u32(opt+56)
        exports,size=self.cache[key];need(name in exports and exports[name][0]!=0,'Exact physical requested native export')
        rva,forwarder=exports[name];return rva,forwarder,size

    def proof(self,raw,name,identity):
        need(len(raw)==4624,'Complete4624B native requested/owner export proof')
        version,namedbase,target,namedresolved,owner,ownerresolved=struct.unpack_from('<6Q',raw)
        requested=terminated(raw[48:80]);forwarder=terminated(raw[80:336]);alias=terminated(raw[336:400])
        namedsha=raw[400:464].decode('ascii');ownersha=raw[464:528].decode('ascii')
        namedpath=Path(terminated(raw[528:2576],'utf-16-le'));ownerpath=Path(terminated(raw[2576:4624],'utf-16-le'))
        actual,named,actualowner,ownernamed=struct.unpack_from('<4Q',identity)
        digest=identity[72:136].decode('ascii');physicalowner=Path(terminated(identity[136:],'utf-16-le'))
        need(version==1 and namedbase!=0 and requested==name and target==namedresolved==ownerresolved==actual==named==ownernamed and owner==actualowner,
             'Native proof binds same requested and full-width resolved/owner target')
        need(namedpath.name.casefold()=='kernel32.dll' and ownerpath==physicalowner and ownersha==digest,'Requested Kernel32 and same actual physical owner')
        namedrva,physicalforwarder,namedsize=self.get(namedpath,namedsha,name)
        ownerrva,ownerforwarder,ownersize=self.get(ownerpath,ownersha,alias)
        need(forwarder==physicalforwarder and not ownerforwarder and owner+ownerrva==target and owner<=target<owner+ownersize<=2**64,
             'Exact physical requested forwarder and direct owner alias/RVA')
        if name=='HeapAlloc':
            need(forwarder=='NTDLL.RtlAllocateHeap' and alias=='RtlAllocateHeap' and ownerpath.name.casefold()=='ntdll.dll' and owner!=namedbase,
                 'Admitted exact HeapAlloc Kernel32-to-NTDLL forwarder chain')
        else:
            need(name=='HeapFree' and not forwarder and alias==name and owner==namedbase and ownerpath==namedpath and ownersha==namedsha and target==namedbase+namedrva,
                 'Exact direct Kernel32 HeapFree export')
        need(namedbase+namedsize<=2**64,'Full-width requested native module image range')
        return dict(name=name,target=target,owner=owner,path=str(ownerpath),sha256=ownersha,export_RVA=ownerrva,
                    requested_module_base=namedbase,requested_path=str(namedpath),requested_sha256=namedsha,
                    requested_export_RVA=namedrva,forwarder=forwarder,owner_export=alias)
