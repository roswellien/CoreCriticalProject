"""Additional ROOT-executable owner translation/native tail controls; no reader/main."""
import copy
def run(base,owner_api_fs,refused):
 owners=base['Lockit-private-owners.json']
 wrong=copy.deepcopy(base);rows=wrong['Lockit-private-owners.json'];target=next(r for r in rows if any(w['source_value']==r['original_meta'][7]for owner in rows if(owner['level'],owner['sequence'])==(r['level'],r['sequence'])for w in owner['source_writes']))
 target['native_record'][16]^=4
 refused('owner-typed-pointer-translation',lambda:owner_api_fs(wrong))
 wrong=copy.deepcopy(base);row=wrong['Lockit-private-owners.json'][0];raw=bytearray.fromhex(row['native_initial_hex']);assert len(raw)==32;raw[31]^=1;row['native_initial_hex']=raw.hex()
 refused('owner-native-untouched-tail',lambda:owner_api_fs(wrong))
