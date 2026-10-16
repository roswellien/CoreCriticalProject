"""Adverse cases that must not be reported as successful geometry benchmarks."""
import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('geometry_compare',Path(__file__).with_name('analyze_geometry_comparison.py'))
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RejectedBenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)
        record={'exit_code':1,'executable_sha256':'fixture','protected_originals':[],
                'environment':{'MW34_FRAME_BUDGET':'3','MW34_GPU_MODELS':'1'}}
        (self.path/'run.json').write_text(json.dumps(record))
        (self.path/'stderr.txt').write_text('Presentation frame budget reached: 3 frames presented')
        (self.path/'draw-log.txt').write_text(''.join(f'{n} 2 abc model_up 1 model_bytes 96 model_draw {n}\n' for n in range(1,4)))
        (self.path/'frame-times.txt').write_text('1 0.0 1 50\n2 10.0 2 100\n3 20.0 3 150\n')
        for name in ('input-script.txt','registry.txt'):(self.path/name).write_text('fixture')
        self.rows=[dict(frame=n,qpc_hz=1000,source_calls=1,source_ticks=2,
                       emit_calls=1,emit_ticks=1,cpu_vertices=0,gpu_vertices=3,
                       tl_bytes=0,gpu_batches=1,near_batches=0) for n in range(1,4)]
        self.write_geometry()

    def write_geometry(self):
        with (self.path/'geometry.csv').open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=self.rows[0].keys())
            writer.writeheader();writer.writerows(self.rows)

    def test_valid_live_scope(self):
        _,_,metrics,_=module.load_case(self.path,True,2,3)
        self.assertEqual(metrics['presentation_mean_ms'],10)

    def test_menu_only_is_rejected(self):
        for row in self.rows:row['gpu_vertices']=0
        self.write_geometry()
        with self.assertRaisesRegex(ValueError,'no measured model activity'):
            module.load_case(self.path,True,2,3)

    def test_frame_gap_is_rejected(self):
        self.rows.pop(1);self.write_geometry()
        with self.assertRaisesRegex(ValueError,'profile gaps'):
            module.load_case(self.path,True,2,3)

    def test_no_gpu_execution_is_rejected(self):
        (self.path/'draw-log.txt').write_text(''.join(f'{n} 2 abc model_up 0 model_draw 0\n' for n in range(1,4)))
        with self.assertRaisesRegex(ValueError,'no actual GPU model execution'):
            module.load_case(self.path,True,2,3)

    def test_early_fault_is_rejected(self):
        (self.path/'stderr.txt').write_text('unresolved required service')
        with self.assertRaisesRegex(ValueError,'incomplete budget'):
            module.load_case(self.path,True,2,3)

    def test_wrong_path_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'wrong path'):
            module.load_case(self.path,False,2,3)


if __name__=='__main__':unittest.main()
