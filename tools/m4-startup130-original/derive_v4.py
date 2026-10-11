from pathlib import Path
p=Path(__file__).resolve().parent;s=(p/'prepare_v3.py').read_text()
a="    (out/'reference.cpp').write_text(ref)"
b="""    typed='''            bool format_import_byte=false;for(unsigned iat=0;iat<3;++iat)if(format_iats[iat]<=pc&&pc<format_iats[iat]+4){const unsigned relative=pc-format_iats[iat];require(actual[byte]==static_cast<unsigned char>(format_targets[iat]>>(8*relative)),\"Exact restored named formatting IAT byte\");format_import_byte=true;}if(format_import_byte)continue;
'''
    ref=one(ref,'            bool fs_byte=false;',typed+'            bool fs_byte=false;')
    (out/'reference.cpp').write_text(ref)"""
assert a in s;s=s.replace(a,b)
s=s.replace('format_IAT_and_return_hooks_restored_each_sequence=True,','format_IAT_and_return_hooks_restored_each_sequence=True,format_final_protected_IAT_bytes_use_exact_named_targets=True,')
(p/'prepare_v4.py').write_text(s)
