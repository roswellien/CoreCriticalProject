"""Unchanged accepted131 CPU/FX/ENV rules at physical current138 chronology.

No widget exclusion is added. SPI own metadata is carried only until the first
physical literal FP root exactly as in the accepted parent policy.
"""
def need(v,m):
 if not v:raise ValueError(m)
def compare(cells,order,graphs):
 spi=next(i for i,r in enumerate(order)if r['entry']==0x482cf0);nextfp=next(i for i,r in enumerate(order)if i>spi and graphs[str(r['entry'])]['FP_sites'])
 by={(r['sequence'],r['phase'],r['side']):r for r in cells};need(len(by)==len(cells)==6*138*2,'Complete six actual root endpoint sets')
 counts=dict(whole_CPU10_records_retained=0,exact_EAX_nonvolatile_ESP_PC_relations=0,exact_ECX_EFLAGS_relations=0,whole_FX512_parent_projection_relations=0,exact_ENV12_head_relations=0,whole_ENV28_relations=0,own_SPI_metadata_carry_relations=0)
 for seq in range(6):
  spi_seed=by[(seq,spi,'after')];seed=(bytes.fromhex(spi_seed['original_ENV_hex'])[12:],bytes.fromhex(spi_seed['native_ENV_hex'])[12:])
  for phase,root in enumerate(order):
   for side in('before','after'):
    r=by[(seq,phase,side)];need(r['root']==root['entry'],'Exact physical source schedule')
    a=r['original_CPU'];b=r['native_CPU'];need(len(a)==len(b)==10,'Whole measured CPU10 records')
    for i in(0,3,4,5,6,7,9):need(a[i]==b[i],'Exact accepted parent EAX/nonvolatile/ESP/measuredPC field');counts['exact_EAX_nonvolatile_ESP_PC_relations']+=1
    boundary=phase==(spi if side=='after'else spi+1)
    if not boundary:
     need(a[1]==b[1]and a[8]==b[8],'Exact accepted parent ECX/EFLAGS outside literal SPI return/input seam');counts['exact_ECX_EFLAGS_relations']+=2
    af=bytes.fromhex(r['original_FX_hex']);bf=bytes.fromhex(r['native_FX_hex']);need(len(af)==len(bf)==512,'Whole FX512')
    # Exactly the retained parent hardwarefx function: reserved metadata is zero;
    # the only physical hardware capability descriptor is the exact0x2FFFF mask.
    need(af[6:24]==bf[6:24]==bytes(18),'No new actual source FP metadata exclusions')
    projected=bytearray(bf);projected[6:24]=bytes(18);projected[28:32]=(0x2ffff).to_bytes(4,'little');need(bytes(projected)==af,'Complete unchanged parent hardwarefx projection, all FP/SIMD values')
    ae=bytes.fromhex(r['original_ENV_hex']);be=bytes.fromhex(r['native_ENV_hex']);need(len(ae)==len(be)==28 and ae[:12]==be[:12],'Exact own ENV28 extents and accepted head12')
    interval=spi<=phase<nextfp if side=='after'else spi<phase<=nextfp
    if interval:need(ae[12:]==seed[0]and be[12:]==seed[1],'Each own complete SPI FIP/FOP/FDP/reserved metadata carries until literal FP overwrite');counts['own_SPI_metadata_carry_relations']+=2
    else:need(ae==be,'Every complete ENV28 byte equal outside unchanged finite SPI interval');counts['whole_ENV28_relations']+=1
    counts['whole_CPU10_records_retained']+=1;counts['whole_FX512_parent_projection_relations']+=1;counts['exact_ENV12_head_relations']+=1
 return dict(counts=counts,SPI_phase=spi,next_FP_phase=nextfp,next_FP_root=order[nextfp]['entry'],new_widget_CPU_exclusions=0,new_widget_FX_exclusions=0,new_widget_ENV_exclusions=0,measured_PC_field_equal=True,complete_all138_chronology=True)
