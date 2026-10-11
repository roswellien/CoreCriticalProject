"""Additive correction: version object is PE virtual zero-fill, not file backing."""
from pathlib import Path
import hashlib,sys
p=Path(__file__).with_name('prepare_v1.py')
assert hashlib.sha256(p.read_bytes()).hexdigest()=='860400189deb99ea0b0176e25f3982b0ede90dfeccb05b3b177ad6cbeb6c604c'
s=p.read_text()
old="object_before=physical(0x60b198,60)[0];need(len(object_before)==60,'Whole physical 60-byte object')"
new="""object_rva=0x60b198-pe.image_base
  owners=[v for v in pe.sections if v['virtual_address']+v['raw_size']<=object_rva and object_rva+60<=v['virtual_address']+v['virtual_size']]
  need(len(owners)==1 and owners[0]['readable']and owners[0]['writable'],'Whole source object is actual PE virtual zero-fill')
  object_before=bytes(60)"""
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace('physical_BEFORE_hex=object_before.hex(),source_constructor_zeroes=60','PE_initial_zero_fill_hex=object_before.hex(),backing="PE virtual zero-fill; runtime BEFORE remains independently observed",source_constructor_zeroes=60')
s=s.replace('pin(__file__);pin(R/',"pin(__file__);pin(Path(__file__).with_name('prepare_v1.py'),'860400189deb99ea0b0176e25f3982b0ede90dfeccb05b3b177ad6cbeb6c604c');pin(R/",1)
exec(compile(s,str(p),'exec'),globals())
