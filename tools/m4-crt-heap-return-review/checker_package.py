"""Explicit additive generator edits for same-stage disjoint archive adoption."""
def adapt(header,main,change):
    header=change(header,'from paths import publish_bytes','from paths import publish_bytes\nfrom bundle_union import BundleUnion')
    main=change(main,'(path,Path(__file__),frozen_path,Path(sys.executable))',"(path,Path(__file__),Path(__file__).parent/'bundle_union.py',frozen_path,Path(sys.executable))")
    main=change(main,'    validator, association = T.load_validator()',"""    pin(native['packaging_path'],native['packaging_sha256'])
    packaging=read(native['packaging_path'])
    need(packaging['passed'] is True and packaging['native_rerun'] is False and packaging['transport_limits_changed'] is False and packaging['byte_identical_private_copies'] is True and packaging['copy_verified'] is True and native['native_rerun'] is False and native['adopts_actual_native_execution'] is True,'Explicit same-stage bounded packaging adoption')
    pin(packaging['partition_tool_path'],packaging['partition_tool_sha256'])
    pin(packaging['packager_tool_path'],packaging['packager_tool_sha256'])
    validator, association = T.load_validator()""")
    main=change(main,"        verify_stage(info['pack_stage'], info['pack_stage_sha256'])","""        original_stage=read(Path(info['native_stage'])/'stage.json')
        need(original_stage['passed'] is True and original_stage['argv']==info['argv'] and original_stage['argv'][-1]==info['source_tree'] and packaging['levels'][level]['native_stage_sha256']==info['native_stage_sha256'] and packaging['levels'][level]['inventory_sha256']==info['inventory_sha256'] and packaging['levels'][level]['bundles']==info['bundles'],'Original native stage and packaging level association')
        for key in ('source_controls','source_complete'):
            pin(info[key],info[key+'_sha256'])
            need(original_stage['artifact_sha256'][info[key]]==info[key+'_sha256'],'Original closed native output digest')
        verify_stage(info['partition_stage'],info['partition_stage_sha256'])
        pin(info['partition_map'],info['partition_map_sha256'])
        mapping=read(info['partition_map'])
        need(mapping['passed'] is True and mapping['source_files_modified'] is False and mapping['transport_limit_unchanged']==200000 and mapping['original_relative_paths_preserved'] is True,'Source-preserving partitioning with unchanged transport limits')
        for part in info['bundles']:
            verify_stage(part['pack_stage'],part['pack_stage_sha256'])
            pin(part['inventory_path'],part['inventory_sha256'])""")
    main=change(main,"        published_records = read(info['inventory_path'])['files']","""        published_records = read(info['inventory_path'])['files']
        need(published_records==mapping['files'] and info['logical_files']==mapping['logical_files'],'Whole original native inventory equals partition map')
        for mapped,part in zip(mapping['parts'],info['bundles']):
            need(mapped['part']==part['part'] and mapped['pack_source']==part['pack_source'] and mapped['logical_files']==part['logical_files'] and mapped['files']==read(part['inventory_path'])['files'],'Exact original-to-part association')""")
    main=change(main,"with CaptureBundle(info['bundle'], info['bundle_sha256']) as bundle:",'with BundleUnion(info,published_records) as bundle:')
    return header,main
