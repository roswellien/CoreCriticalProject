"""Preserve r1 failure; distinguish original contract and compiled interface."""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
path = Path(__file__).with_name('accept.py'); source = path.read_text()
old = "        need(rows['original_source']['source_contract_sha256'] == old_interface['contracts_sha256'] and has(rows['original_source'], old_interface['contracts'], old_interface['contracts_sha256']), 'Fresh old-owner source proof shares authentic accepted interface')"
new = """        bridge_item = rows['parent']['gates']['owner_original']
        old_bridge = read(ROOT / bridge_item['path'], bridge_item['sha256']); absorb(old_bridge)
        original_contract_path = ROOT / 'reports/m4-lockit-source/owned-contracts-r1/report.json'
        original_contract_sha = rows['original_source']['source_contract_sha256']
        need(old_bridge['passed'] and old_bridge['original_source_contract_sha256'] == original_contract_sha and old_bridge['source_contract_sha256'] == old_interface['contracts_sha256'], 'Accepted physical original-to-native owner interface bridge')
        need(has(rows['original_source'], original_contract_path, original_contract_sha) and has(old_interface, original_contract_path, original_contract_sha) and has(old_bridge, old_interface['contracts'], old_interface['contracts_sha256']), 'Fresh actual source and unchanged native interface share exact bridged physical original contract')
        need(rows['original_source']['source_owned_contracts'] == old_bridge['source_owned_contracts'] == old_interface['owned_accesses'] == 32 and rows['original_source']['source_publication_contracts'] == old_bridge['source_publication_contracts'] == old_interface['publications'] == 8, 'Complete fresh original owner/publication corroborations to accepted interface')"""
assert source.count(old) == 1
source = source.replace(old,new)
out = path.with_name('accept_v2.py'); assert not out.exists(); out.write_text(source)
