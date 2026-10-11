"""Bind reviewed paired v3, all nine branch byteflows and distinct page scopes."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;p=HERE/'paired_review_v2.py';s=p.read_text(encoding='utf-8')
needle="exec(compile(source,str(p),'exec'),globals())"
assert s.count(needle)==1;s=s.replace(needle,'compiled_source=source')
context={'__file__':__file__,'__name__':'paired_review_deriver'};exec(compile(s,str(p),'exec'),context);source=context['compiled_source']
source=source.replace('paired_v2.py','paired_v3.py')
needle="        report=read(paired_report);source=read(source_report)"
extra="""
        pin(ROOT/'tools/m4-lockit-review/paired_review_v2.py')
        need(paired_report.resolve()==(ROOT/'reports/m4-lockit-paired-provider/paired-r2/report.json').resolve(),
             'Exact fresh paired-r2 report required; prior failed final counter receipt excluded')
        preparation_review=read(ROOT/'reports/m4-lockit-review/paired-v3-preparation-r1/report.json',
                                '24360f3cd14a60c47998e983b047fa0b3f6762e636c0ec7191dffd047abbeda3')
        actual_comparer=(ROOT/'tools/m4-lockit-paired-provider/paired_v3.py').resolve()
        need(preparation_review['passed']and preparation_review['files'][str(actual_comparer)]==report['files'][str(actual_comparer)],
             'Actual paired observer is exact independently reviewed two-change v3 preparation')
"""
assert source.count(needle)==1;source=source.replace(needle,needle+extra)
needle="        APIs=output('Lockit-paired-API-observations.json');need(len(APIs)==96,'All96 bounded original/native API pairs')"
extra="""
        branches=output('Lockit-branch-byte-relations.json');need(len(branches)==108,'All nine branch byteflows in twelve actual cases')
        original_path=(ROOT/'reports/m4-lockit-paired-provider/original-r2/original-source-access-ledgers.json').resolve()
        source_ledgers=read(original_path,original['files'][str(original_path)])
        native_path=(source_report.parent/'Lockit-header-derivations.json').resolve()
        native_fields=read(native_path,source['files'][str(native_path)])
        expected_fields={0x411010:{0x6040b8,0x6040b9},0x4dc140:{0x60b5a8,0x60b5a9},
                         0x500660:{0x60bf90,0x60bfa0,0x60bfa1},0x5968f0:{0x731868,0x731869}}
        seen_fields=set()
        for row in branches:
            case=(row['level'],row['sequence']);key=case+(row['root'],row['field'])
            need(case in cases and row['field']in expected_fields[row['root']]and key not in seen_fields,
                 'Exact complete nine-field paired inventory without omissions or duplicate facts');seen_fields.add(key)
            native=row['native_source_derivation'];need(native in native_fields and
                 (native['level'],native['sequence'],native['root'],native['field'])==key,
                 'Whole native branch provenance joins exact independently reviewed persistent source derivation')
            ledger=next(r for r in source_ledgers if r['sequence']==row['sequence']and r['root']==row['root'])['rows']
            writes=[(i,r)for i,r in enumerate(ledger)if r[0]==native['write_pc']and r[1]==row['field']and r[3:]==[1,1]]
            need(len(writes)==1 and writes[0][1]==row['original_source_write'],
                 'Original branch byte is exact independently source-corroborated literal ledger write')
            wi,write=writes[0];reads=[r for r in ledger[:wi]if r[0]==native['read_pc']and r[3:]==[1,0]]
            need(len(reads)==1 and reads[0][2]==write[2],
                 'Original branch publication retains unchanged byte from its prior literal source stack read')
            counts['independent_paired_branch_byteflows']+=1
            counts['independent_paired_branch_source_derivations']+=2
            if row['field']==0x60bf90:counts['independent_paired_auxiliary_byteflows']+=1
        need(len(seen_fields)==108,'All actual branch fields independently checked')
"""
assert source.count(needle)==1;source=source.replace(needle,extra+needle)
needle="        for key,value in expected_counts.items():need(report['counts'][key]==value,'All sealed paired reader observations '+key)"
extra="""
        need(report['counts']['whole_nonstack_page_relations']==122016 and
             report['counts']['separate_whole_loader_page_input_relations']==2976 and
             report['counts']['whole42_nonstack_page_endpoint_relations']==124992,
             'Exact ordinary41 plus separately related entire loader-page endpoint coverage')
        counts['ordinary_whole_page_endpoints']=122016;counts['separate_whole_loader_page_endpoints']=2976
        counts['combined42_nonstack_page_endpoints']=124992
"""
assert source.count(needle)==1;source=source.replace(needle,needle+extra)
exec(compile(source,str(HERE/'paired_review.py'),'exec'),globals())
