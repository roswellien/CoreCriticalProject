"""Literal widget/provider journal association in one carried source machine.

The guest machine and memory are never replaced at widget entry, provider
entry, provider return, or widget return. Only source journals have separate
owners. The two literal CALL5AC11E operands are checked in both journals.
"""
from pathlib import Path
import collections, copy, hashlib, json, re, struct

ROOT = Path(__file__).resolve().parents[2]
WIDGETS = (0x40e250, 0x40ef50, 0x40f000, 0x479590, 0x5a3c30, 0x5a3ff0, 0x5a66f0)
CALLBACKS = (0x40e420, 0x40ef90, 0x40f030, 0x4795d0, 0x5a3c60, 0x5a4020, 0x5a6720)
FRAME = 0x20001800

def need(value, message):
    if not value:
        raise ValueError(message)

def equal(left, right, message):
    need(left == right, message)

def whole_checkpoint(machine, archive, prefix):
    """Compare a captured Context boundary to the already computed source.

    Nothing read here enters the source machine. The complete captured Game
    inventory must be the same at every such boundary in this sequence.
    """
    need(prefix.endswith('/'), 'Canonical complete current Context checkpoint prefix')
    equal(archive.data(prefix+'State.bin'), bytes(machine.state), 'Whole carried Context State3504 from source')
    equal(archive.data(prefix+'CPU.bin'), struct.pack('<10I',*machine.projected_cpu()), 'Whole carried Context CPU40 from source')
    equal(archive.data(prefix+'FX.bin'), machine.fx, 'Whole carried Context FX512 from source')
    names = sorted(name for name in archive.entries if name.startswith(prefix+'game-region-'))
    need(names and all(re.fullmatch(re.escape(prefix)+r'game-region-\d+\.bin',name) for name in names),
         'Complete finite actual Game-region byte inventory')
    regions=[]
    for name in names:
        address=int(name[len(prefix+'game-region-'):-4]);raw=archive.data(name)
        need(raw and address % 4096 == 0 and len(raw) % 4096 == 0, 'Whole actual mapped Game-region extent')
        equal(raw, machine.bytes(address,len(raw)), 'Every complete carried Game-region source byte '+hex(address))
        regions.append((address,len(raw),hashlib.sha256(raw).hexdigest()))
    equal(archive.data(prefix+'stack.bin'),machine.bytes(0x20001000,4096),'Whole carried guest stack from source')
    TIB=machine.word(2168)
    equal(archive.data(prefix+'TIB.bin'),struct.pack('<5I',TIB,*[int.from_bytes(machine.bytes(TIB+o,4),'little') for o in (0,4,8,0x18)]),
          'Every complete actual TIB field from carried source')
    pages=[]
    for page in (0x7800f000,0x78010000,0x78023000,0x7802e000,0x78037000):
        raw=archive.data(prefix+'provider-source-page-'+str(page)+'.bin')
        equal(raw,machine.bytes(page,4096),'Whole carried formatter provider page from source '+hex(page))
        pages.append((page,hashlib.sha256(raw).hexdigest()))
    return dict(prefix=prefix,whole_State_bytes=3504,whole_CPU_bytes=40,whole_FX_bytes=512,
                whole_stack_bytes=4096,Game_regions=regions,provider_pages=pages,source_equality_only=True)

def checkpoint_index(archive, stem):
    """Retain every duplicate borrowed checkpoint with its exact source root."""
    rows = []
    for name in archive.entries:
        if name.startswith(stem+'registry-checkpoint-') and name.endswith('-name.bin'):
            number = int(name[len(stem+'registry-checkpoint-'):-len('-name.bin')])
            rows.append((number, archive.data(name).decode(), name[:-9]))
    rows.sort()
    index = {}; before = after = 0
    for number, label, prefix in rows:
        if label == 'widget-onexit-before':
            need(before == after and before < len(WIDGETS), 'Exactly one complete ordered borrowed entry per widget')
            label = f'widget-onexit-{WIDGETS[before]}-before'; before += 1
        elif label == 'widget-onexit-after':
            need(after+1 == before and after < len(WIDGETS), 'Same ordered borrowed entry returns once')
            label = f'widget-onexit-{WIDGETS[after]}-after'; after += 1
        need(label not in index, 'Every actual checkpoint retained exactly once '+label)
        index[label] = prefix
    need(before == after == 7, 'All fourteen actual borrowed checkpoint names retained')
    return index

class JournalAssociation:
    def __init__(self, machine, observer, gdi, archive, sequence, level, pin):
        self.machine = machine; self.observer = observer; self.gdi = gdi
        self.archive = archive; self.seq = sequence; self.level = level; self.pin = pin
        self.mode = 'provider'; self.root = 0; self.shared = []; self.records = []
        self.root_runtime_cpu = None; self.source_rows = []; self.root_result = []
        self.provider_before = None; self.component_accesses = []
        self.projections = []; self.counters = collections.Counter()
        self.Game_inventory = None

    def begin(self, root):
        need(self.mode == 'provider' and not self.root and root in WIDGETS,
             'One exact current widget enters from the carried provider source machine')
        need(len(self.root_result) == WIDGETS.index(root), 'Literal table-sorted seven-root association')
        m = self.machine
        need(m.cursor == root and m.reg('esp') == FRAME and m.call_stack[-1][:3] == (root, FRAME, 0x410a80),
             'Actual committed scheduler source CALL frame before widget')
        self.mode = 'component'; self.root = root; self.shared = []
        self.root_runtime_cpu = struct.pack('<10I', *m.projected_cpu())
        self.provider_before = len(m.accesses); self.component_before = len(self.component_accesses)
        self.PC_before = len(m.PCs); self.source_before = len(self.source_rows)
        self.observer.root = root
        boundary=whole_checkpoint(m,self.archive,f'sequence-{self.seq}/Widget/root-{root}/carried-before/')
        inventory=[r[:2] for r in boundary['Game_regions']]
        if self.Game_inventory is None:self.Game_inventory=inventory
        equal(inventory,self.Game_inventory,'Same whole mapped Game inventory at every actual widget boundary')
        self.current_before_boundary=boundary
        self.gdi.begin_root(m, root, m._source_undefined_flags)
        m.begin_widget(root)

    def committed(self, row):
        """Called after the independent interpreter committed a source operand."""
        if self.mode != 'component':
            return
        m = self.machine
        need(m.accesses and tuple(m.accesses[-1]) == tuple(row), 'One exact committed component source operand')
        m.accesses.pop()
        ordinal = len(self.component_accesses)
        self.component_accesses.append(tuple(row)); self.source_rows.append(tuple(row))
        self.gdi.record_access(m, tuple(row), ordinal)
        if row[0] == 0x5ac11e:
            self.shared.append(tuple(row))

    def before_control(self, event, data):
        if self.mode == 'component':
            self.gdi.control(self.machine, event, data, self.machine._source_undefined_flags)
        if event != 'control' or data.get('op') != 'call' or data.get('target') != 0x78004a36:
            return
        need(self.mode == 'component' and self.root and data['site'] == 0x5ac11e,
             'Only exact literal widget CALL enters the borrowed provider')
        m = self.machine; frame = m.reg('esp'); root = self.root
        callback = CALLBACKS[WIDGETS.index(root)]
        shared = [(0x5ac11e, 0x5bb52c, 0x1decb0, 4, 0),
                  (0x5ac11e, FRAME-24, 0x5ac124, 4, 1)]
        equal(self.shared, shared, 'Exactly two whole shared raw-IAT/CALL-frame operands')
        need(frame == FRAME-24 and m.cursor == 0x78004a36 and
             m.bytes(frame,8) == struct.pack('<2I',0x5ac124,callback),
             'Complete current literal return and callback words at borrowed entry')
        self.mode = 'provider'
        self.observer.runtime_cpu = self.root_runtime_cpu
        self.observer.check(m, f'widget-onexit-{root}-before')
        before = len(m.accesses)
        m.accesses.extend(shared)
        projection = (9, root, 0x5ac11e, 0x5bb52c, 0x1decb0, 0x78004a36, frame, 0x5ac124)
        self.projections.append(projection)
        self.records.append(dict(level=self.level, sequence=self.seq, root=root,
            provider_before_source_index=before, shared_source_rows=[list(r) for r in shared],
            shared_component_source_indices=list(range(len(self.component_accesses)-2,len(self.component_accesses))),
            provider_source_start=before+2, source_CALL_frame=frame, callback=callback,
            borrowed_projection=list(projection), before_State_sha256=__import__('hashlib').sha256(bytes(m.state)).hexdigest(),
            before_CPU_hex=struct.pack('<10I',*m.projected_cpu()).hex(),
            before_FX_hex=m.fx.hex(), returned=False))

    def after_control(self, event, data):
        if event != 'returned' or not data.get('caller') or data['caller'][0] != 0x78004a36:
            return
        need(self.mode == 'provider' and self.root and self.records and not self.records[-1]['returned'],
             'Same borrowed source CALL returns once')
        m = self.machine; root = self.root; row = self.records[-1]
        need(data['frame'] == FRAME-24 and m.reg('esp') == FRAME-20 and m.cursor == 0x5ac124,
             'Genuine source provider RET returns to the committed widget frame')
        need(m.reg('eax') == CALLBACKS[WIDGETS.index(root)], 'Source returned the exact current callback')
        self.observer.check(m, f'widget-onexit-{root}-after')
        row.update(returned=True, provider_source_end=len(m.accesses),
            provider_source_rows=[list(r) for r in m.accesses[row['provider_source_start']:]],
            after_State_sha256=__import__('hashlib').sha256(bytes(m.state)).hexdigest(),
            after_CPU_hex=struct.pack('<10I',*m.projected_cpu()).hex(), after_FX_hex=m.fx.hex())
        self.source_rows.extend(m.accesses[row['provider_source_start']:])
        self.mode = 'component'
        self.gdi.control(m, event, data, m._source_undefined_flags)

    def end(self):
        m = self.machine; root = self.root
        need(self.mode == 'component' and root and len(self.shared) == 2 and self.records[-1]['returned'],
             'One complete prefix/provider/tail source interval')
        need(m.reg('esp') == FRAME+4 and m.cursor == 0x410a80 and not m.call_stack,
             'All four literal source CALL frames return to the real scheduler')
        m.end_widget()
        proof = self.gdi.end_root(m, self.archive.data, f'sequence-{self.seq}/Widget/')
        boundary=whole_checkpoint(m,self.archive,f'sequence-{self.seq}/Widget/root-{root}/carried-after/')
        equal([r[:2] for r in boundary['Game_regions']],self.Game_inventory,
              'Same complete mapped Game inventory at actual widget return')
        row = dict(level=self.level, sequence=self.seq, root=root,
            source_PCs=m.PCs[self.PC_before:],
            source_accesses=[list(r) for r in self.source_rows[self.source_before:]],
            component_source_accesses=[list(r) for r in self.component_accesses[self.component_before:]],
            borrowed_provider=dict(self.records[-1]), GDI_source=proof,
            whole_carried_before=self.current_before_boundary,whole_carried_after=boundary,
            whole_State_source_derived=True, AFTER_machine_or_page_seed=False,
            source_journal_domains='Exact component prefix/tail and actual provider, with only two literal shared CALL operands')
        self.root_result.append(row)
        self.root = 0; self.mode = 'provider'; self.shared = []
        return row

    def cleanup(self, physical_identity):
        """Prove actual manual owned-font cleanup before Session teardown.

        This uses native DeleteObject observations and typed source ownership.
        Guest source callbacks remain unexecuted; no teardown is fabricated.
        """
        m=self.machine;gdi=self.gdi
        need(self.mode=='provider' and not self.root and len(self.root_result)==7,
             'All seven carried source roots precede actual manual font cleanup')
        gdi.finish();owned=[copy.deepcopy(f) for f in reversed(gdi.fonts) if f['owned'] and f['live']]
        need(len(owned)==15,'Exactly fifteen genuinely source-acquired live owned font generations')
        prefix=f'sequence-{self.seq}/Widget/';manual=[];expected=set()
        for font in owned:
            stem=prefix+'manual-font-cleanup/'+str(font['generation'])
            raw=self.archive.data(stem+'-row.bin');hardware=self.archive.data(stem+'-hardware.bin')
            need(len(raw)==64 and len(hardware)==1152,'Complete actual manual font identity and native hardware sides')
            row=struct.unpack('<8Q',raw)
            equal(row[:6],(font['guest'],font['generation'],font['instance'],font['root'],font['native'],gdi.thread),
                  'Current live typed source/native font generation identifies actual reverse DeleteObject')
            need(row[6] and row[7]==1,'Actual successful same-owner manual DeleteObject observation')
            equal(struct.unpack_from('<Q',hardware,8)[0],font['native'],'Real full native DeleteObject RCX owns current font')
            equal(struct.unpack_from('<Q',hardware,576)[0],row[6],'Real full native DeleteObject RAX joins success observation')
            manual.append((raw,hardware));expected.update((stem+'-row.bin',stem+'-hardware.bin'))
        actual={name for name in self.archive.entries if name.startswith(prefix+'manual-font-cleanup/')}
        equal(actual,expected,'All and only fifteen complete source-owned manual cleanup observations')
        physical=physical_identity.verify(self.archive.data,self.pin,prefix=prefix,source_records=gdi.api_bytes,
            manual_records=manual,logical_names=self.archive.entries,expected_thread=gdi.thread)
        stem=prefix+'root-'+str(WIDGETS[-1])+'/cleaned/'
        fonts=list(struct.iter_unpack('<IIIIQBB6x',self.archive.data(stem+'fonts.bin')))
        expected_fonts=[(f['guest'],f['generation'],f['instance'],f['root'],f['native'],int(f['owned']),int(f['live'] and not f['owned'])) for f in gdi.fonts]
        equal(fonts,expected_fonts,'Every current private font field reflects actual successful owned-font release')
        status=list(struct.unpack('<12Q',self.archive.data(stem+'status.bin')))
        expected_status=[gdi.thread,7,WIDGETS[-1],FRAME,0,0,1,gdi.local_api,gdi.local_virtual,gdi.local_FS,gdi.generation,gdi.FS_invocation]
        equal(status,expected_status,'Whole actual post-cleanup current source context status')
        for field in ('accesses.bin','frames.bin','FS-frames.bin','FS-events.bin','virtuals.bin','arrays.bin','imports.bin','APIs.bin','formats.bin','format-dispatches.bin'):
            equal(self.archive.data(stem+field),self.archive.data(prefix+'root-'+str(WIDGETS[-1])+'/after/'+field),
                  'Manual native cleanup invents no source operations or machine context '+field)
        boundary=whole_checkpoint(m,self.archive,prefix+'font-cleaned-current/')
        equal([r[:2]for r in boundary['Game_regions']],self.Game_inventory,'Every whole mapped Game extent retained through manual cleanup')
        hardware=self.archive.data(prefix+'font-cleanup-caller-hardware.bin')
        need(len(hardware)==1632,'Whole current native ASM manual-cleanup caller boundary1632')
        equal(hardware[:512],hardware[1088:1600],'Complete outside-cleanup raw caller FX512 restoration')
        equal(hardware[512:540],hardware[1600:1628],'Complete outside-cleanup caller ENV28 restoration')
        return dict(level=self.level,sequence=self.seq,actual_owned_font_frees=len(owned),font_generations=[f['generation']for f in owned],
            physical_GDI=physical,whole_carried_cleanup=boundary,whole_caller_FX512_ENV28_restore=True,
            source_callbacks_executed=False,manual_cleanup_source_body_modeled=False,
            manual_native_ownership_and_scalar_observations=True,AFTER_State_or_memory_seed=False)

    def prove_projection_rows(self, raw):
        actual = [tuple(r) for r in struct.iter_unpack('<8I', raw) if r[0] == 9]
        equal(actual, self.projections, 'Entire actual borrowed source projection list from literal CALLs')
        self.counters['whole_borrowed_source_projection_rows'] += len(actual)
        self.counters['shared_raw_IAT_and_CALL_operand_pairs'] += len(actual)

def machine_class(parent):
    class AssociatedMachine(parent):
        def __init__(self,*args,**kwargs):
            self.widget_association = None
            super().__init__(*args,**kwargs)
        def read(self,address,size=4,domain='source',pc=None):
            value = super().read(address,size,domain,pc)
            association = self.widget_association
            if domain == 'source' and association and association.mode == 'component':
                association.committed(self.accesses[-1])
            return value
        def write(self,address,value,size=4,domain='source',pc=None):
            result = super().write(address,value,size,domain,pc)
            association = self.widget_association
            if domain == 'source' and association and association.mode == 'component':
                association.committed(self.accesses[-1])
            return result
        def emit(self,event,**data):
            association = self.widget_association
            if association:
                association.before_control(event,data)
            result = super().emit(event,**data)
            if association:
                association.after_control(event,data)
            return result
    return AssociatedMachine

def observer_class(parent):
    class WidgetObserver(parent):
        def check(self,m,name):
            association = getattr(m,'widget_association',None)
            if association and association.mode == 'component':
                # Native Session owns no checkpoints for component FS writes.
                # Their complete source witnesses are checked in the component.
                return
            return super().check(m,name)
        def string_event(self,m,event,data):
            association = getattr(m,'widget_association',None)
            if association and association.mode == 'component':
                return
            return super().string_event(m,event,data)
    return WidgetObserver
