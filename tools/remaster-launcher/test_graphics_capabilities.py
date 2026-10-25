"""Detected display sizes must agree with the declared native output contract."""
import contextlib
import io
import unittest
from unittest.mock import patch
import play_remaster


class GraphicsCapabilitiesTests(unittest.TestCase):
    def host(self):
        return dict(graphics_capabilities=dict(width=3440,height=1440,aa="fxaa",af=16),
                    supported_graphics_values=dict(width=[1920,2560,3440],height=[1080,1440],aa=[1,"fxaa",2,4],af=[1,2,4,8,16]),
                    supported_graphics_ranges=dict(width=[640,7680],height=[480,4320]))

    def test_detected_and_scaled_display_sizes(self):
        for width,height in [(1536,864),(1366,768),(1920,1200),(1280,1024),(2256,1504),(640,480),(7680,4320)]:
            with self.subTest(width=width,height=height):
                self.assertEqual(play_remaster.graphics_limitations(dict(width=width,height=height,aa="fxaa",af=16),self.host()),[])

    def test_invalid_dimensions_and_other_settings_still_rejected(self):
        for key,value in [('width',639),('width',7681),('height',479),('height',4321),('width','1366'),('width',True),('aa',8),('af',3),('unknown',1)]:
            with self.subTest(key=key,value=value):
                self.assertIn(f'{key}={value}',play_remaster.graphics_limitations({key:value},self.host())[0])

    def test_legacy_profile_is_not_silently_extended(self):
        host=self.host();del host['supported_graphics_ranges']
        self.assertTrue(play_remaster.graphics_limitations(dict(width=1536,height=864),host))
        self.assertEqual(play_remaster.graphics_limitations(dict(width=1920,height=1080),host),[])

    def test_malformed_or_excessive_advertised_ranges_fail(self):
        for ranges in [dict(aa=[1,4]),dict(width=[1,10000]),dict(height=[480,4321]),dict(width=[7680,640]),dict(width=[640]),dict(width=[640,True])]:
            host=self.host();host['supported_graphics_ranges']=ranges
            with self.subTest(ranges=ranges),self.assertRaisesRegex(RuntimeError,'Invalid native graphics range'):
                play_remaster.graphics_limitations({},host)

    def test_check_mode_must_fail_for_unsupported_profile(self):
        planned=dict(backend='native',graphics=dict(width=1366,height=768,aa='fxaa',af=16),texture_banks=0,
                     models=[],offline_models=[],music=None,supported=False,
                     limitations=['Unsupported native graphics setting width=1366; supported: 1920.'])
        output=io.StringIO()
        with patch('sys.argv',['play_remaster','--check']),patch.object(play_remaster,'plan',return_value=planned), \
                patch.object(play_remaster,'read_json',return_value={'native':{'executable':'fixture.exe'}}), \
                contextlib.redirect_stdout(output),contextlib.redirect_stderr(output):
            self.assertEqual(play_remaster.main(),2)
        self.assertIn('width=1366',output.getvalue())


if __name__=='__main__':unittest.main()
