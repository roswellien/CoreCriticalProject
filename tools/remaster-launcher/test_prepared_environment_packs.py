"""Asset-free checks of operation selection, relocation and disabled bindings."""
import hashlib,json,struct,tempfile,unittest
from pathlib import Path
from normal_materials import pack_surface_bindings,read_surface_bindings
from prepared_environment_packs import select,prepare,detail_metadata,PROFILE,REGISTRY,REGIONS,sha

class EnvironmentPackTests(unittest.TestCase):
    def test_detail_pins_follow_selected_pack_revision(self):
        with tempfile.TemporaryDirectory() as t:
            root=self.fixture(Path(t)/'current')
            chosen=select([str(root)],self.host())
            pins=detail_metadata(chosen)
            self.assertEqual(set(pins),{'water','surf','cloud'})
            for role,pin in pins.items():
                self.assertEqual(pin['sha256'],sha(Path(pin['path'])))
                self.assertEqual(pin['bytes'],Path(pin['path']).stat().st_size)
            self.assertEqual(detail_metadata({}),{})
    def fixture(self,root,operation='training',normal=b'\x80\x80\xff\xff'):
        root.mkdir(); files={}
        def put(name,data,fmt=None):
            p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
            files[name]=dict(bytes=len(data),sha256=sha(p))
            if fmt:files[name]['format']=fmt
            return name
        bank=put('environment/bank.bin',struct.pack('<6I',0,1,0,1,0,0),'ZBD-texture-v1')
        reg=dict(schema_version=2,payload_profile=PROFILE,operation=operation,banks={f'zbd/{r}/{n}.zbd':bank for r in REGIONS[operation] for n in ['rtexture','rtexture2','rtexture3','texture','texture1','texture2']},detail={})
        data=pack_surface_bindings([((1,1,1,123),(1,1,normal))])
        for role,magic in [('authored','MW34SNA1'),('world','MW34SNP1')]:
            reg[role]=[put('environment/'+role+'.bin',data,'BWSNR2')]
            reg[role+'_manifest']=put('environment/'+role+'.txt',(magic+'\n'+role+'.bin\n').encode(),magic)
        for role in ['water','surf','cloud']:reg['detail'][role]=put('environment/'+role+'-detail.bin',data,'BWSNR2')
        reg['effects']=put('environment/effects.bin',b'MWFX1\0\0\0'+struct.pack('<I',0),'MWFX1')
        if operation=='shared-mechs':
            reg['banks']={f'zbd/{n}.zbd':bank for n in ['rmechtex','rmechtex16']}
            reg={k:v for k,v in reg.items() if k in {'schema_version','payload_profile','operation','banks','authored','authored_manifest'}}
            used={bank,*reg['authored'],reg['authored_manifest']}
            files={k:v for k,v in files.items() if k in used}
        put(REGISTRY,json.dumps(reg).encode())
        manifest=dict(schema_version=2,id='test.'+root.name.replace(' ','-').lower(),native_payload=dict(profile=PROFILE,registry=REGISTRY,path_base='pack-root',reference_host_sha256='a'*64,required_formats=['BWSNR2']),files=files)
        (root/'pack.json').write_text(json.dumps(manifest))
        return root
    def host(self):
        return dict(executable_sha256='a'*64,runtime_environment={'MW34_WORLD_NORMALS':'stale','MW34_REMASTER_BANKS':'stale','MW34_BUSHWACKER_TEST':'selected-mech','MW34_FIXTURE_LIGHT_RETAIN_DISTANCE':'160'})
    def test_relocation_selection_and_disable(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);one=self.fixture(root/'one');two=self.fixture(root/'two','operation4');moved=root/'relocated with spaces';one.rename(moved)
            chosen=select([str(moved),str(two)],self.host());self.assertEqual(set(chosen),{'training','operation4'})
            bindings=prepare(chosen,self.host(),root/'launch');self.assertEqual(bindings['MW34_BUSHWACKER_TEST'],'selected-mech')
            self.assertEqual(bindings['MW34_FIXTURE_LIGHT_RETAIN_DISTANCE'],'160')
            raw=Path(bindings['MW34_REMASTER_BANKS']).read_bytes();self.assertEqual(struct.unpack('<I',raw[8:12])[0],18)
            pages=Path(bindings['MW34_SURFACE_NORMALS']);page=pages.parent/pages.read_text().splitlines()[1]
            self.assertEqual(len(read_surface_bindings(page.read_bytes())),1)
            empty=prepare({},self.host(),root/'disabled');self.assertNotIn('MW34_WORLD_NORMALS',empty);self.assertNotIn('MW34_REMASTER_BANKS',empty)
    def test_reject_bad_host_corruption_and_conflicts(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);one=self.fixture(root/'one');two=self.fixture(root/'two','operation1',b'\x90\x80\xff\xff')
            with self.assertRaises(ValueError):select([str(one)],dict(executable_sha256='b'*64))
            with self.assertRaises(ValueError):prepare(select([str(one),str(two)],self.host()),self.host(),root/'conflict')
            (one/'environment/bank.bin').write_bytes(b'bad')
            with self.assertRaises(ValueError):select([str(one)],self.host())
    def test_lighting_pack_admission_on_reviewed_cinematic_host(self):
        with tempfile.TemporaryDirectory() as t:
            pack=self.fixture(Path(t)/'lighting-base')
            manifest=json.loads((pack/'pack.json').read_text())
            manifest['native_payload']['reference_host_sha256']='0d3d920f6b560ddcd92fbeeb4034d59430ddd46a19b75269255fc8ec83fe12ef'
            (pack/'pack.json').write_text(json.dumps(manifest))
            host=self.host()
            for digest in ['9fd17ba2459ac2d349adda33c0c84d41772bbd2ec7c0e2a620242c696526bb83',
                           'c1afedadd8ed9e13a956db917a1a5335a6581fac01374b367969d4e985852115']:
                host['executable_sha256']=digest
                self.assertIn('training',select([str(pack)],host))
            host['executable_sha256']='b'*64
            with self.assertRaises(ValueError):select([str(pack)],host)

    def test_shared_mechs_own_only_global_banks_and_compose_with_operations(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);shared=self.fixture(root/'shared','shared-mechs');world=self.fixture(root/'world','operation2')
            moved=root/'moved shared pack';shared.rename(moved)
            chosen=select([str(moved)],self.host());env=prepare(chosen,self.host(),root/'alone')
            self.assertEqual(env['MW34_EFFECT_LIGHTS'],'0')
            self.assertNotIn('MW34_WORLD_NORMALS',env)
            self.assertIn('MW34_SURFACE_NORMALS',env)
            raw=Path(env['MW34_REMASTER_BANKS']).read_bytes();self.assertEqual(struct.unpack('<I',raw[8:12])[0],2)
            chosen=select([str(moved),str(world)],self.host());env=prepare(chosen,self.host(),root/'combined')
            raw=Path(env['MW34_REMASTER_BANKS']).read_bytes();self.assertEqual(struct.unpack('<I',raw[8:12])[0],8)
            self.assertIn('MW34_WORLD_NORMALS',env)
            disabled=prepare({},self.host(),root/'disabled-shared');self.assertNotIn('MW34_REMASTER_BANKS',disabled)

if __name__=='__main__':unittest.main()
