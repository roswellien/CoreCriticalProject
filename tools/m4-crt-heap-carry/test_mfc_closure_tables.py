"""Asset-free checks for bounded indexed continuation recovery."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('closure',Path(__file__).with_name('mfc_closure.py'))
closure=importlib.util.module_from_spec(spec);spec.loader.exec_module(closure)

class LiteralTable:
    def __init__(self,words):self.words=words
    def word(self,address):return self.words[address]

class JumpTableChecks(unittest.TestCase):
    def recover(self,words):
        closure.PES.clear()
        with patch.object(closure,'IMAGES',{'fixture':(None,None,0x1000,0x1010,0x2000)}),patch.object(closure,'PE',return_value=LiteralTable(words)):
            return closure.jump_table('fixture',0x1800,0x1100)
    def test_backward_seven_dwords(self):
        words={0x1800:0x1100,0x1804:0}
        words.update({0x1800-4*i:0x1100+8*i for i in range(1,9)})
        recovered=self.recover(words)
        self.assertEqual(recovered,[0x1100]+[0x1100+8*i for i in range(1,8)])
        self.assertNotIn(words[0x17e0],recovered)
    def test_unreachable_zero_slot_and_forward_cases(self):
        self.assertEqual(self.recover({0x1800:0,0x1804:0x1120,0x1808:0x1130,0x180c:0x1140,0x1810:0}),[0x1120,0x1130,0x1140])
    def test_negative_scan_stops_at_first_noncode_word(self):
        self.assertEqual(self.recover({0x1800:0x1100,0x1804:0,0x17fc:0x1120,0x17f8:0x3000,0x17f4:0x1130}),[0x1100,0x1120])
    def test_negative_scan_stops_at_unreadable_slot(self):
        self.assertEqual(self.recover({0x1800:0x1100,0x17fc:0x1120,0x17f4:0x1130}),[0x1100,0x1120])

if __name__=='__main__':unittest.main()
