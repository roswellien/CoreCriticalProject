"""Add tree occurrence relations to the accepted finite paired124 policy.

Generate a fresh125 tool before execution. Historical124 source/provider
models remain frozen; actual125 original/natively derived values are supplied
by freshly authenticated source receipts, never borrowed from old processes.
"""
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[2]


def change(text, before, after, count=1):
    assert text.count(before) == count, (before[:160], text.count(before), count)
    return text.replace(before, after)


def main():
    path = ROOT / 'tools/m4-lockit-paired-provider/paired_v3.py'
    text = path.read_text()
    text = change(text, 'original/native124', 'original/native125')
    text = change(text, 'def main(native_report,name,native_source_report,native_source_sha):',
                  'def main(native_report,name,native_source_report,native_source_sha,original_source_report,original_source_sha,original_review_report,original_review_sha):')
    text = change(text, "out=ROOT/'reports/m4-lockit-paired-provider'/name", "out=ROOT/'reports/m4-tree-paired'/name")
    text = change(text, "ROOT/'reports/m4-lockit-original/original-validation-r2/report.json','4a6f998156b13fc24ed6e6cb285ae482ff562c8d267d1a171c35b0bf7a36c6c3'",
                  "ROOT/'reports/m4-tree-original/original125-validation-r1/report.json','5a7911dee3f77d504a5a28cf66de2be7cc0b159a15a4e81282368a24d3a45534'")
    text = change(text, "ROOT/'reports/m4-lockit-paired-provider/original-r2/report.json','48f184d6edbaae5e1ec9d384f743089210e65dea9655822a4f517b41fa3b757b'",
                  'original_source_report,original_source_sha')
    text = change(text, "execution['build_sha256']=='05a198d319f2e3ee2259b998a8989db23df0b20afd40416fb185e7a0b1d17c30'",
                  "execution['build_sha256']=='cdb5b9ca08e4e66dae276fa783bc59b5944e8435113fe9bb65a73cc53f218165'")
    text = change(text, 'Exact finalprep5/build4 actual native124 run', 'Exact finalprep4/build1 actual native125 run')
    text = change(text, "ROOT/'reports/m4-lockit-original/original-preparation-r4/report.json','6a25b9b16ccdbfefe30488ea6b87afd5c266489fd63f2b5710c05c04a14fd68b'",
                  "ROOT/'reports/m4-tree-original/original125-preparation-r1/report.json','6e55c14d0195d099f8a02a51dee250a4b3fb0d92832b7c0a6e08f307cbd9c5a1'")
    text = change(text, "read_bytes())['order'];G.PAGES=PAGES", "read_bytes())['selected_order'];G.PAGES=PAGES")
    text = change(text, "ROOT/'reports/m4-lockit-original/original-build-r3/build.json','3a2214354b280439342e5b128bf48d980d9f3fb8ac9aab88ac8d8e570ed693a6'",
                  "ROOT/'reports/m4-tree-original/original125-build-r1/build.json','e25a97c26e9a23d54f8340c7c0908a891915865b9ccda044ae3793e244d5a585'")
    text = change(text, "ROOT/'reports/m4-lockit-original/original-execution-r2/report.json','2caaa9be2cd24c2862d4f6e98cf92f5418a4492ffda244a8a19527c15e65e5a1'",
                  "ROOT/'reports/m4-tree-original/original125-execution-r1/report.json','1e327ed23d5276964fc67e70308ce80a60a7e34051960b02e9c30da67b9998ae'")
    text = change(text, "original_source_dir=ROOT/'reports/m4-lockit-paired-provider/original-r2'",
                  'original_source_dir=Path(original_source_report).resolve().parent')
    text = change(text, "original_source_dir/'report.json','48f184d6edbaae5e1ec9d384f743089210e65dea9655822a4f517b41fa3b757b'",
                  "original_source_dir/'report.json',original_source_sha")
    text = change(text, "ROOT/'reports/m4-lockit-review/full-original-r1/report.json','570bc3dc54aadcb7b67abccb06182c7177eeb7d059bb31ea5caf40f57625659f'",
                  'original_review_report,original_review_sha')
    text = change(text, "full_original_gate['original_validation_sha256']=='4a6f998156b13fc24ed6e6cb285ae482ff562c8d267d1a171c35b0bf7a36c6c3'",
                  "full_original_gate['original_validation_sha256']=='5a7911dee3f77d504a5a28cf66de2be7cc0b159a15a4e81282368a24d3a45534'")
    text = change(text, "roots={r['entry']:r['registration']['callback']for r in rootrows}",
                  "tree_instructions=json.loads(pin(ROOT/'reports/m4-tree-source/recovery-r1/instruction-contracts.json').read_bytes())['instructions'];need(next(r for r in tree_instructions if r['pc']==0x4b7f70)['bytes_hex']=='68a07f4b00','Physical tree callback PUSH4B7FA0');rootrows.append(dict(entry=0x4b7f70,registration=dict(callback=0x4b7fa0)));roots={r['entry']:r['registration']['callback']for r in rootrows}")
    before = "  for level in ('O0','O2'):\n"
    additions = '''  T=load('current125_tree_pair_relations',ROOT/'tools/m4-tree-paired/tree_relations.py')
  original_tree_gate_path=ROOT/'reports/m4-tree-source/original125-source-r1/report.json'
  original_tree_gate=json.loads(pin(original_tree_gate_path,'884abbe43d69570265b2b8539d04455bdb622664d136b0055b8ab073a8735c5f').read_bytes());need(original_tree_gate['passed'],'All six genuine original tree source cases')
  original_trees={}
  for row in original_tree_gate['cases']:
   receipt=Path(row['receipt']);case=json.loads(pin(receipt,row['sha256']).read_bytes());need(case['passed'],'Passed own original tree case');original_trees[row['sequence']]=source_artifact(receipt.parent,case,'source-derivations.json')
  native_trees=source_artifact(Path(native_source_report).parent,source_gate,'Tree-source-derivations.json');need(len(native_trees)==12 and {(r['level'],r['sequence'])for r in native_trees}=={(level,seq)for level in('O0','O2')for seq in range(6)},'Every current full125 literal tree source case')
  tree_pairs=[]
  for level in ('O0','O2'):
'''
    text = change(text, before, additions)
    text = change(text, "need(len(mfc_records)==58,'58 exact native allocation owners')",
                  "need(len(mfc_records)==65,'65 exact native allocation owners')")
    text = change(text, "['API_relations'];need(len(native_Lockit)==8,'All8 current actual native Lockit source API relations')",
                  "['API_relations'];need(len(native_Lockit)==34,'All34 current actual native Lockit source API relations')")
    text = change(text, "    for phase,item in enumerate(order):",
                  "    tree_source=next(r['source']for r in native_trees if r['level']==level and r['sequence']==seq);tree_fields,tree_counts=T.compare(original_trees[seq],tree_source,native,stem);counts.update(tree_counts);tree_pairs.append(dict(level=level,sequence=seq,static_fields={str(a):list(v)for a,v in tree_fields.items()},counts=tree_counts));old_Lockit_indices={w[10]for w in struct.iter_unpack('<16Q',native.data(stem+'lockit-calls.bin'))if w[2]in lockit_roots};native_Lockit=[r for r in native_Lockit if r['API_index']in old_Lockit_indices];need(len(native_Lockit)==8,'Eight old-root actual API relations after current tree occurrence filtering')\n    for phase,item in enumerate(order):")
    text = change(text, "       need(all(x['offset']in declared for x in differences)",
                  "       T.carry(tree_fields,phase,side,page,original,actual,declared,counts)\n       need(all(x['offset']in declared for x in differences)")
    text = change(text, "struct.pack('<96I',*expected_callbacks)", "struct.pack('<97I',*expected_callbacks)")
    text = text.replace('paired124', 'paired125').replace('selected124', 'selected125').replace('native124', 'native125')
    text = change(text, "counts['paired_phases']==1488", "counts['paired_phases']==1500")
    text = change(text, "counts['whole_nonstack_page_relations']==122016", "counts['whole_nonstack_page_relations']==123000")
    text = change(text, "counts['separate_whole_loader_page_input_relations']==2976", "counts['separate_whole_loader_page_input_relations']==3000")
    text = change(text, "counts['whole42_nonstack_page_endpoint_relations']==124992", "counts['whole42_nonstack_page_endpoint_relations']==126000")
    text = change(text, 'len(provider_page_rows)==8928', 'len(provider_page_rows)==9000')
    text = change(text, "('Lockit-paired-normal-FS.json',new_FS_rows)", "('Tree-paired-source-relations.json',locals().get('tree_pairs',[])),('Lockit-paired-normal-FS.json',new_FS_rows)")
    text = change(text, "new_original_source_report_sha256='48f184d6edbaae5e1ec9d384f743089210e65dea9655822a4f517b41fa3b757b'",
                  'new_original_source_report_sha256=original_source_sha')
    text = change(text, "Lockit_independent_original_compiled_observer_gate_sha256='570bc3dc54aadcb7b67abccb06182c7177eeb7d059bb31ea5caf40f57625659f'",
                  'Lockit_independent_original_compiled_observer_gate_sha256=original_review_sha')
    text = change(text, 'eight new private owners from genuine branch initial backings',
                  'fifteen retained/new dynamic private owners from genuine branch initial backings; exact seven-role tree relations and static carries')
    text = change(text, "if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],Path(sys.argv[3]).resolve(),sys.argv[4])",
                  "if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],Path(sys.argv[3]).resolve(),sys.argv[4],Path(sys.argv[5]).resolve(),sys.argv[6],Path(sys.argv[7]).resolve(),sys.argv[8])")
    target = ROOT / 'tools/m4-tree-paired/paired.py'
    assert not target.exists()
    ast.parse(text)
    target.write_text(text, encoding='utf-8')
    print('Generated fresh full125 paired policy; execution and independent review pending')


if __name__ == '__main__':
    main()
