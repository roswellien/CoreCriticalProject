"""Admit the exact additive lower-address tail and truthful52-body fixture.

Every whole-link, service, caller, guard and physical source check from v7 is
retained. The only new body is the previously captured68-row normal JMP tail.
"""
from pathlib import Path
import hashlib, sys
sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[2]
parent = R / 'tools/m4-tree-review/review_widget6_prelaunch_v7.py'
assert hashlib.sha256(parent.read_bytes()).hexdigest() == '69b1bb5cb2766299fb0361a496621cefbb275c8337682d13c44b42393d4eb262'
text = parent.read_text()
for old, new in {
 '209b73cd3d16280ca4173ec3f0ac0186681b4415a2b8b81c79aa46a634e96abb':'58c6d615dfc5c23acf56bd3f62b8635f5647831e623c956154b78986af0e5401',
 '004b2a21b58d1ac10d3b96a8726e092b8ada0fac2855f8ef358b16cea0f087bb':'036d33c85494a29c358a4d7e2016606bbdb9290316be52ac2ae32b07f96a3d98',
 '69a29eddf46f6c189edc462e5f5734a96e3d98c2c1f37778a54d36c0fd62eae5':'714a5f0093a62e68911f78c93a07d34e4bd9f4b39e79e0931a4812bee6877ed9',
 '9c053306dbf44a3a65ac1945dd4c2b0949ef064842004e05bf2e6cc29a22fada':'7bba3319abef8202d154229ba4243dadd6e2693381c86abcbd41bf41007d20bf',
 'fixture-preparation-r12':'fixture-preparation-r16',
 'fixture-build-r11':'fixture-build-r13',
 "base / 'preparation-r3/":"base / 'preparation-r6/",
 "base / 'build-r5/":"base / 'build-r7/",
 "comp['literal_bodies'] == 51":"comp['literal_bodies'] == 52",
 'assert len(literal) == 51':'assert len(literal) == 52',
 'run_fixture_v4.py':'run_fixture_v5.py',
 '5d64892010fb6c9f44b22800ec2c2e91561df90664a4aac9c024410bdbbb198a':'dc4ee2bf790c826855a520d54870073e4255d9ea7acced122f2e5b997db3795b',
}.items():
    assert old in text, old
    text = text.replace(old, new)
old = "            assert current==prior"
new = """            if leaf == 'fixture.cpp':
                marker = b'status{1,unsigned(!failed),6,51,unsigned(r.poisoned())'
                assert prior.count(marker) == 1
                prior = prior.replace(marker, b'status{1,unsigned(!failed),6,52,unsigned(r.poisoned())')
            assert current==prior"""
assert text.count(old) == 1; text = text.replace(old, new)
old = "        assert comp['literal_epilogue_read_operands'] == 18"
new = old + """
        old_component = receipt(base / 'preparation-r3/report.json','69a29eddf46f6c189edc462e5f5734a96e3d98c2c1f37778a54d36c0fd62eae5')
        assert comp['prior_component_sha256'] == '69a29eddf46f6c189edc462e5f5734a96e3d98c2c1f37778a54d36c0fd62eae5'
        assert comp['lower_tail_entry'] == 0x5a4590 and comp['whole_prior_IRs_unchanged'] == 51
        assert comp['component_cpp_unchanged'] and comp['contracts_json_unchanged']
        assert comp['changed_generated_files'] == ['literals.hpp','bridges.inc']
        assert comp['new_bridge_symbols'] == ['extern "C" std::uint8_t mw34_widget_game_f_5a4590_undefined_8(){return 0;}']
        for relation in comp['prior_copy_relations']:
            assert pin(relation['prior_path'],relation['prior_sha256']).read_bytes() == pin(relation['current_path'],relation['current_sha256']).read_bytes()
            counts['whole_retained_prior_component_inputs'] += 1
        lower = next(row for row in comp['namespace_relations'] if row['entry'] == 0x5a4590)
        assert len(lower['instructions']) == 68
        prior_header = pin(base/'preparation-r3/literals.hpp').read_text()
        current_header = pin(base/'preparation-r6/literals.hpp').read_text()
        declaration = 'extern "C" void* mw34_widget_game_f_5a4590_body(mw34::State*,std::uint32_t,void*);'
        dispatch = 'case 0x5a4590:return mw34_widget_game_f_5a4590_body(state,pc,memory);'
        assert current_header.count(declaration) == current_header.count(dispatch) == 1
        assert current_header.replace(declaration+'\\n','').replace(dispatch+'\\n','') == prior_header
        prior_bridge = pin(base/'preparation-r3/bridges.inc').read_text()
        current_bridge = pin(base/'preparation-r6/bridges.inc').read_text()
        bridge = comp['new_bridge_symbols'][0]
        assert current_bridge.count(bridge) == 1 and current_bridge.replace(bridge+'\\n','') == prior_bridge
        assert pin(base/'fixture-preparation-r16/contiguous-registration-spans.json').read_bytes() == pin(base/'fixture-preparation-r12/contiguous-registration-spans.json').read_bytes()
        pin(parent)
"""
assert text.count(old) == 1; text = text.replace(old, new)
exec(compile(text, str(parent), 'exec'), globals())
