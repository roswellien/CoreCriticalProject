"""Fix only the emitted member-ledger reference inside SessionImpl::dump."""
from pathlib import Path
h=Path(__file__).resolve().parent;p=h/'prepare_service.py';s=p.read_text()
a='std::span(i.constructor_accesses_)';b='std::span(constructor_accesses_)'
if s.count(a)!=1:raise ValueError('One exact member-scope export correction')
s=s.replace(a,b,1).replace('pin(__file__);report=dict(',"pin(__file__);pin(R/'tools/m4-constructor-native/prepare_service.py');report=dict(",1)
exec(compile(s,str(p),'exec'),globals())
