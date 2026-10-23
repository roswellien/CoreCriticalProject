import struct

with open('MW3/zbd/t1/reader.zbd', 'rb') as f:
    f.seek(106303 - 32)
    chunk = f.read(64)

for i in range(0, len(chunk)-4, 4):
    fval = struct.unpack_from('<f', chunk, i)[0]
    ival = struct.unpack_from('<i', chunk, i)[0]
    print(f"Offset -32 + {i}: float={fval:.3f}, int={ival}")
