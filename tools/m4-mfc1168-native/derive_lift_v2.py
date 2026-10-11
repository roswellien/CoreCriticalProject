"""Retain a denied async-hypercall bridge for padded, unentered branch bytes."""
from pathlib import Path
import hashlib
R=Path(__file__).resolve().parents[2];p=R/'tools/m4-mfc1168-native/lift.py';s=p.read_text();assert hashlib.sha256(p.read_bytes()).hexdigest()=='b65cda1158a777bed0c3d3d6215768c7ead3c287b6b1e04fe7343cea195d26da'
a="'function_call','function_return','jump','missing_block','fpu_exception_clear','fpu_exception_test'";assert s.count(a)==1;s=s.replace(a,"'function_call','function_return','jump','missing_block','async_hyper_call','fpu_exception_clear','fpu_exception_test'")
a="ROOT/'tools/m4-mfc1168-native/derive_lift.py',";assert s.count(a)==1;s=s.replace(a,"ROOT/'tools/m4-mfc1168-native/derive_lift.py',ROOT/'tools/m4-mfc1168-native/derive_lift_v2.py',ROOT/'tools/m4-mfc1168-native/lift.py',")
out=R/'tools/m4-mfc1168-native/lift_v2.py';assert not out.exists();out.write_text(s);print(hashlib.sha256(out.read_bytes()).hexdigest())
