"""Authored material fixtures; no original artwork is needed."""
import unittest
import numpy as np
from prepare_surface_detail import normal_for

class SurfaceDetail(unittest.TestCase):
    def test_shared_water_and_protected_surf(self):
        # RGB565 sand, neutral foam and green water, left-to-right.
        words=np.empty((128,128),dtype='<u2')
        words[:,:64]=0xa304;words[:,64:96]=0xffff;words[:,96:]=0x2425
        data=words.tobytes();saved=bytes(data)
        water=np.frombuffer(normal_for('water',data,128,128)[2],dtype='uint8').reshape(128,128,4)
        surf=np.frombuffer(normal_for('surf',data,128,128)[2],dtype='uint8').reshape(128,128,4)
        np.testing.assert_array_equal(water[...,:3],surf[...,:3])
        self.assertTrue(np.all(surf[:,:96,3]==0),'Sand and foam must remain unperturbed')
        self.assertTrue(np.all(surf[:,96:,3]==255),'Water edge must join the shared wave field')
        self.assertEqual(data,saved,'Normal preparation must not modify albedo')

    def test_flat_cloud_is_exactly_neutral(self):
        data=np.full((64,128),0x7bef,dtype='<u2').tobytes()
        w,h,pixels=normal_for('cloud',data,128,64)
        result=np.frombuffer(pixels,dtype='uint8').reshape(h,w,4)
        self.assertTrue(np.all(result[...,:2]==128))

    def test_cloud_relief_is_bounded_and_flat_at_atlas_edges(self):
        rng=np.random.default_rng(0);data=rng.integers(0,65536,(64,128),dtype='uint16').astype('<u2').tobytes()
        w,h,pixels=normal_for('cloud',data,128,64)
        slopes=np.frombuffer(pixels,dtype='uint8').reshape(h,w,4)[...,:2].astype(float)-128
        self.assertLessEqual(np.linalg.norm(slopes,axis=-1).max()/127,.306)
        self.assertTrue(np.all(slopes[:3]==0) and np.all(slopes[:,:3]==0))

if __name__=='__main__':unittest.main()
