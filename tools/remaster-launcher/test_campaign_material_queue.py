"""Synthetic ordering checks: no game files, scene assets or native execution."""
import csv
import json
from pathlib import Path
import tempfile
import unittest
from campaign_material_queue import build


class CampaignQueueTests(unittest.TestCase):
    def fixture(self, root):
        def write(name, value):
            path=root/name;path.write_text(json.dumps(value));return str(path)
        inventory=write('inventory.json',dict(textures=[dict(name=n,category='terrain_marked_world_geometry') for n in ('shore','wall','ground')]))
        water=write('water.json',dict(groups=dict(water_surfaces=['shore'],surf_animation=[],foam_and_splash=[])))
        index=write('index.json',dict(bindings=[dict(key=[64,64,1,i],names=[name],source='world_catalog') for i,name in enumerate(('shore','wall','ground'),1)]))
        previous=root/'previous.csv';previous.write_text('texture,authoring_state\nwall,existing candidate\n')
        route=root/'route.txt';route.write_text('Synthetic route fixture')
        events=[]
        for seq,hash_ in enumerate((1,2,3),1):
            events.append(dict(event='first_world_texture_submission',sequence=seq,frame=20,width=64,height=64,format=1,hash=hash_,alpha_blend=0,alpha_test=False,terrain_gpu=True))
        trace=root/'trace.jsonl';trace.write_text('\n'.join(json.dumps(e) for e in events)+'\n')
        config=dict(inventory=inventory,water_inventory=water,key_index=index,previous_queue=str(previous),mission_order=['c1m1','c1m2'],runs=[dict(mission='c1m1',encounters=str(trace),route=str(route),scope='synthetic')])
        path=root/'config.json';path.write_text(json.dumps(config));return path,config,events

    def test_draw_order_and_excluded_water(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);path,_,_=self.fixture(root);r=build(path,root/'out',2)
            self.assertEqual([e['texture'] for e in r['selected']],['wall','ground'])
            self.assertEqual(r['selected'][0]['submission_sequence'],2)
            self.assertEqual(r['selected'][0]['authoring_state'],'existing candidate')

    def test_no_padding_when_route_is_short(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);path,_,_=self.fixture(root)
            with self.assertRaisesRegex(ValueError,'Only 2'):build(path,root/'out',100)

    def test_unknown_key_blocks_exact_order(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);path,_,events=self.fixture(root);events[1]['hash']=99
            (root/'trace.jsonl').write_text('\n'.join(json.dumps(e) for e in events))
            with self.assertRaisesRegex(ValueError,'Unresolved texture'):build(path,root/'out',2)

    def test_campaign_order_cannot_run_backwards(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);path,config,_=self.fixture(root);first=config['runs'][0].copy();first['mission']='c1m2';config['runs'].insert(0,first);path.write_text(json.dumps(config))
            with self.assertRaisesRegex(ValueError,'progression order'):build(path,root/'out',2)


if __name__=='__main__':unittest.main()
