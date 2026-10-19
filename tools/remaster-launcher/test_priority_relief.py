"""Synthetic checks for the priority scan and broad-feature relief regression."""
import math
import unittest
import numpy as np
from PIL import Image, ImageFilter
from prepare_priority_relief import relief, profile
from rank_normal_priorities import polygon_area
from prepare_authored_relief import normals_from_height, periodic_height, alignment


class PriorityReliefTests(unittest.TestCase):
    def test_broad_rock_ridge_survives(self):
        x = np.arange(512, dtype=np.float32)
        h = np.tile(.5+.25*np.sin(x*2*math.pi/256), (256, 1))
        image = Image.fromarray(np.rint(h*255).astype('uint8')).convert('RGB')
        normal, height = relief(image, profile('txwall01', []))
        self.assertEqual(normal[:2], (512, 256))
        channels = np.frombuffer(normal[2],dtype='uint8').reshape(256,512,4)
        # The previous tiny/high-pass first pass discarded these broad ridges.
        self.assertGreater(int(channels[:,:,0].max())-int(channels[:,:,0].min()), 40)
        self.assertGreater(int(height.max())-int(height.min()), 1000)

    def test_flat_atlas_and_border(self):
        normal, _ = relief(Image.new('RGB',(128,128),(100,100,100)), profile('truck1',['vehicle_all_materials']))
        n = np.frombuffer(normal[2],dtype='uint8').reshape(128,128,4)
        self.assertTrue(np.all(n[:,:,:3]==[128,128,255]))
        self.assertTrue(np.all(n[:,:,3]==255))

    def test_polygon_area_uses_geometry_not_texture_size(self):
        vertices = [dict(x=0,y=0,z=0),dict(x=4,y=0,z=0),dict(x=4,y=0,z=3),dict(x=0,y=0,z=3)]
        self.assertAlmostEqual(polygon_area(vertices,dict(vertex_indices=[0,1,2,3])),12.)
        self.assertAlmostEqual(polygon_area(vertices,dict(vertex_indices=[0,1,3,2],flags=dict(tri_strip=True))),12.)

    def test_authored_flat_height_remains_flat(self):
        normal, stats = normals_from_height(Image.new('L',(64,32),128),(64,32),.05,.7)
        values=np.frombuffer(normal[2],dtype='uint8').reshape(32,64,4)
        self.assertTrue(np.all(values[:,:,:3]==[128,128,255]))
        self.assertAlmostEqual(stats['max_slope'],0.)

    def test_seam_decomposition_does_not_invent_wrap_ridge(self):
        ramp=np.tile(np.linspace(0,1,128),(64,1))
        corrected=periodic_height(ramp)
        self.assertLess(float(np.abs(corrected[:,-1]-corrected[:,0]).mean()),.02)

    def test_alignment_detects_moved_features(self):
        rng=np.random.default_rng(42)
        raw=rng.integers(0,256,(256,256),dtype='uint8')
        image=Image.fromarray(raw).filter(ImageFilter.GaussianBlur(4))
        same=alignment(image,image)
        self.assertEqual(same['best'][1:],(0,0))
        shifted=Image.fromarray(np.roll(np.array(image),8,axis=1))
        self.assertNotEqual(alignment(image,shifted)['best'][1:],(0,0))


if __name__=='__main__':
    unittest.main()
