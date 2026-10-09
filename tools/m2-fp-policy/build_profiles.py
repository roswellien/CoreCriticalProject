"""Recover authored exact domains from frozen protocol constants, without changes."""
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OUT=ROOT/'reports/m2-fp-policy'


def array(text,name):
    match=re.search(r'\b'+re.escape(name)+r'\s*\{(.*?)\};',text,re.S)
    if not match:raise ValueError('Missing frozen domain '+name)
    body=re.sub(r'//[^\n]*','',match[1])
    return [int(x.removesuffix('ULL'),0) for x in re.findall(r'0x[0-9a-fA-F]+ULL|\b0\b',body)]


def signed_pairs(words):
    if len(words)%2:raise ValueError('Invalid pair table')
    return [[words[i]|sa,words[i+1]|sb] for i in range(0,len(words),2)
            for sa,sb in ((0,0),(0,1<<63),(1<<63,0),(1<<63,1<<63))]


def build():
    paths=[ROOT/'tools/x87-c1/protocol.hpp',ROOT/'tools/x87-store-c1/protocol.hpp',ROOT/'tools/x87-range/protocol.hpp']
    conversion,arithmetic,ranges=(p.read_text() for p in paths)
    basic=[[0x3ff0000000000000|sa,((1023-power)<<52)|sb]
           for power in (30,54,24,53,64) for sa,sb in ((0,0),(0,1<<63),(1<<63,0),(1<<63,1<<63))]
    finite=signed_pairs(array(arithmetic,'finite_magnitude_pairs'))
    special=signed_pairs(array(arithmetic,'special_magnitude_pairs'))
    special += [pair for n in array(arithmetic,'single_nan_vectors') for pair in ([n,0x3ff0000000000000],[0x3ff0000000000000,n])]
    range_pairs=signed_pairs(array(ranges,'range_magnitude_pairs'))
    conversions=[[v,0] for v in array(conversion,'conversion_vectors')]
    profiles={}
    for name,code,domain,mask,contract in (
        ('numeric-add-sub','dd01dc4108dc21dd1ac3',basic,0x38ff,'x87-numeric'),
        ('spill64','dd01dc4108dd5a08dd4208dc21dd1ac3',basic,0x38ff,'x87-c1'),
        ('fistp32','dd01db1ac3',conversions,0x3aff,'x87-c1'),
        ('mul64','dd01dc4908dd1ac3',finite,0x3aff,'x87-store-c1'),
        ('div64','dd01dc7108dd1ac3',finite,0x3aff,'x87-store-c1'),
        ('mul-special','dd01dc4908dd1ac3',special,0x3aff,'x87-store-c1'),
        ('div-special','dd01dc7108dd1ac3',special,0x3aff,'x87-store-c1'),
        ('mul-range','dd01dc4908dd1ac3',range_pairs,0x3aff,'x87-range'),
        ('div-range','dd01dc7108dd1ac3',range_pairs,0x3aff,'x87-range')):
        profiles[name]={'fixture_hex':code,'vectors':domain,'vectors_per_CW':len(domain),'cases':12*len(domain),
                        'entry_status_mask':mask,'exit_status_mask':mask,'contract':'docs/'+contract+'-contract.md',
                        'entry_stack':'empty','entry_status':'clean','state':'accepted_bounded_profile'}
    expected=(20,20,32,96,96,40,40,160,160)
    if tuple(len(p['vectors']) for p in profiles.values())!=expected:raise ValueError('Frozen domain count changed')
    payload={'schema_version':1,'control_words':[0x7f|pc<<8|rc<<10 for pc in (0,2,3) for rc in range(4)],'profiles':profiles,
             'source_hashes':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    HERE.mkdir(parents=True,exist_ok=True);(HERE/'profiles.json').write_text(json.dumps(payload,indent=2)+'\n')
    OUT.mkdir(parents=True,exist_ok=True)
    print('profiles_sha256',hashlib.sha256((HERE/'profiles.json').read_bytes()).hexdigest())


if __name__=='__main__':build()
