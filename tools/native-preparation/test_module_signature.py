"""Authored PE/certificate framing fixtures; these are not trusted signatures."""
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
from module_signature import export_signature, apply_signature, recover_unsigned


class ModuleSignatureTests(unittest.TestCase):
    def fixture(self, root):
        data=bytearray(1025); data[:2]=b'MZ'; struct.pack_into('<I',data,0x3c,128)
        data[128:132]=b'PE\0\0'; struct.pack_into('<H',data,132,0x8664)
        struct.pack_into('<H',data,152,0x20b); struct.pack_into('<I',data,260,16)
        unsigned=root/'unsigned.dll'; unsigned.write_bytes(data)
        offset=(len(data)+7)&~7
        blob=struct.pack('<IHH',16,0x200,2)+b'FIXTURE!'
        signed=bytearray(data); signed[216:220]=b'abcd'
        struct.pack_into('<II',signed,296,offset,len(blob))
        signed.extend(b'\0'*(offset-len(signed))); signed.extend(blob)
        target=root/'signed.dll'; target.write_bytes(signed)
        return unsigned,target

    def test_exact_reconstruction_and_changed_input_rejection(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t); unsigned,signed=self.fixture(root)
            metadata=export_signature(unsigned,signed,root/'signature')
            original=unsigned.read_bytes()
            unsigned.write_bytes(original[:-1]+b'X')
            with self.assertRaises(ValueError): apply_signature(unsigned,metadata,root/'signature/module-certificates.bin')
            unsigned.write_bytes(original)
            apply_signature(unsigned,metadata,root/'signature/module-certificates.bin')
            self.assertEqual(unsigned.read_bytes(),signed.read_bytes())
            self.assertEqual((root/'signature/module-certificates.bin').stat().st_size,16)

    def test_executable_changes_and_certificate_corruption_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t); unsigned,signed=self.fixture(root)
            raw=signed.read_bytes(); changed=bytearray(raw); changed[700]=1; signed.write_bytes(changed)
            with self.assertRaises(ValueError): export_signature(unsigned,signed,root/'bad')
            signed.write_bytes(raw); metadata=export_signature(unsigned,signed,root/'signature')
            certificate=root/'signature/module-certificates.bin';certificate.write_bytes(b'bad')
            before=unsigned.read_bytes()
            with self.assertRaises(ValueError): apply_signature(unsigned,metadata,certificate)
            self.assertEqual(unsigned.read_bytes(),before)

    def test_interrupted_attachment_can_retry_in_owned_scratch(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t); unsigned,signed=self.fixture(root)
            metadata=export_signature(unsigned,signed,root/'signature')
            work=root/'work';work.mkdir()
            with patch('module_signature.os.replace',side_effect=OSError('interrupted')):
                with self.assertRaises(OSError):
                    apply_signature(unsigned,metadata,root/'signature/module-certificates.bin',work)
            self.assertEqual(len(list(work.glob('*.tmp'))),1)
            apply_signature(unsigned,metadata,root/'signature/module-certificates.bin',work)
            self.assertEqual(unsigned.read_bytes(),signed.read_bytes())

    def test_changed_signature_reuses_code_but_changed_code_does_not(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);unsigned,signed=self.fixture(root)
            metadata=export_signature(unsigned,signed,root/'signature')
            original=unsigned.read_bytes()
            other=bytearray(signed.read_bytes());other[-1]^=1
            signed.write_bytes(other)
            self.assertEqual(recover_unsigned(signed,metadata),original)
            self.assertEqual(signed.read_bytes(),other)
            other[700]^=1;signed.write_bytes(other)
            self.assertIsNone(recover_unsigned(signed,metadata))


if __name__=='__main__': unittest.main()
