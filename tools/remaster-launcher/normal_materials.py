"""Pack explicitly registered linear OpenGL normal maps for native materials.

BWNRM2 uses material names, explicit unperturbed batch bindings and full-pixel
FNV-1a identities. Colour conversion, strength baking and normal-Y inversion
are deliberately absent. Inputs and generated sidecars stay local.
"""
from pathlib import Path
import struct
import io
from functools import lru_cache

NO_NORMAL = 0xffffffff


@lru_cache(maxsize=8)
def pixel_hash(data):
    value = 0xcbf29ce484222325
    for byte in data:
        value = ((value ^ byte) * 0x100000001b3) & 0xffffffffffffffff
    return value


def normal_environment(texture_environment):
    if not texture_environment.startswith('MW34_') or not texture_environment.endswith('_TEXTURES'):
        raise ValueError('Normal maps require a MW34_*_TEXTURES binding')
    return texture_environment[:-9] + '_NORMALS'


def pack_normals(batch_materials, images):
    """images maps material names to (width, height, raw RGBA bytes), or None."""
    if not batch_materials or len(batch_materials) > 256 or len(images) > 256:
        raise ValueError('Invalid normal material/batch count')
    if set(batch_materials) - images.keys():
        raise ValueError('Every batch needs an explicit normal-map or disabled binding')
    used = {name for name in batch_materials if images[name] is not None}
    names = [name for name in images if name in used]
    if len(names)>64:
        raise ValueError('Invalid normal image count')
    indices = {name: i for i, name in enumerate(names)}
    bindings = [indices.get(name, NO_NORMAL) for name in batch_materials]
    out = bytearray(b'BWNRM2\0\0' + struct.pack('<II', len(bindings), len(names)))
    out.extend(struct.pack('<' + 'I' * len(bindings), *bindings))
    total = 0
    for name in names:
        encoded = name.encode('ascii')
        if not encoded or len(encoded) > 31 or b'\0' in encoded:
            raise ValueError('Invalid normal material name')
        width, height, pixels = images[name]
        total += len(pixels)
        if not 0 < width <= 4096 or not 0 < height <= 4096 or len(pixels) != width * height * 4 or total > 256 * 1024 * 1024:
            raise ValueError('Invalid normal image size')
        out.extend(encoded.ljust(32, b'\0'))
        out.extend(struct.pack('<IIQ', width, height, pixel_hash(pixels)))
        out.extend(pixels)
    return bytes(out)


def load_images(root, normal_textures):
    from PIL import Image
    images = {}
    for name, relative in normal_textures.items():
        if relative is None:
            images[name] = None
            continue
        with Image.open(Path(root) / relative) as source:
            # Preserve channel values and resolution; normal maps are linear data.
            image = source.convert('RGBA').transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            images[name] = (*image.size, image.tobytes())
    return images


def pack_surface_normals(entries):
    """entries: (source width, height, 16-bit format, packed colour bytes, normal image).

    Normal images are (width,height,RGBA bytes) or None. No short texture
    signatures, map-specific names, or process addresses enter the contract.
    """
    keys = []
    for width, height, format_, colour, normal in entries:
        if not 0 < width <= 4096 or not 0 < height <= 4096 or format_ not in (1,2,3) or len(colour)!=width*height*2:
            raise ValueError('Invalid source texture identity')
        keys.append(((width, height, format_, pixel_hash(colour)), normal))
    return pack_surface_bindings(keys)


def pack_surface_bindings(entries):
    """Pack validated full-content keys, sharing byte-identical normal images.

    Up to 256 original surfaces can reference up to 64 images. A key supplied
    here must come from hashing every source color byte, or a validated catalog.
    """
    if not 0 < len(entries) <= 256:
        raise ValueError('Invalid surface binding count')
    header=bytearray(b'BWSNR2\0\0'+struct.pack('<I',len(entries)))
    images={};keys=set();names=[];shared={}
    for key,normal in entries:
        width,height,format_,hash_=key
        if not 0 < width <= 4096 or not 0 < height <= 4096 or format_ not in (1,2,3) or not 0<=hash_<1<<64:
            raise ValueError('Invalid source texture identity')
        if key in keys:raise ValueError('Ambiguous duplicate surface identity')
        keys.add(key)
        # The entire immutable image tuple participates in equality; a hash
        # collision alone cannot conflate different normal images.
        if normal not in shared:
            name='surface'+str(len(images));shared[normal]=name;images[name]=normal
        name=shared[normal];names.append(name)
        header.extend(struct.pack('<IIIQ',*key));header.extend(name.encode().ljust(32,b'\0'))
    return bytes(header)+pack_normals(names,images)


def read_surface_bindings(data):
    """Read an existing BWSNR2 catalog for a validated, lossless extension."""
    stream = io.BytesIO(data)
    def read(size):
        value = stream.read(size)
        if len(value) != size:
            raise ValueError('Truncated surface catalog')
        return value
    def u32():
        return struct.unpack('<I', read(4))[0]
    def name():
        raw = read(32)
        if not raw[0] or raw[-1]:
            raise ValueError('Invalid surface material name')
        return raw.split(b'\0')[0].decode('ascii')
    if read(8) != b'BWSNR2\0\0':
        raise ValueError('Unsupported surface catalog')
    count = u32()
    if not 0 < count <= 256:
        raise ValueError('Invalid surface binding count')
    bindings=[];keys=set()
    for _ in range(count):
        key=struct.unpack('<IIIQ',read(20));material=name()
        w,h,format_,_=key
        if not 0<w<=4096 or not 0<h<=4096 or format_ not in (1,2,3) or key in keys:
            raise ValueError('Invalid or duplicate surface key')
        keys.add(key);bindings.append((key,material))
    if read(8) != b'BWNRM2\0\0' or u32()!=count:
        raise ValueError('Invalid surface normal payload')
    image_count=u32()
    if image_count>64:
        raise ValueError('Invalid normal image count')
    indices=[u32() for _ in range(count)];images=[];names=set();total=0
    for _ in range(image_count):
        material=name();w,h,hash_=struct.unpack('<IIQ',read(16))
        total+=w*h*4
        if material in names or not 0<w<=4096 or not 0<h<=4096 or total>256*1024*1024:
            raise ValueError('Invalid normal image')
        names.add(material);pixels=read(w*h*4)
        if pixel_hash(pixels)!=hash_:
            raise ValueError('Normal image hash mismatch')
        images.append((material,(w,h,pixels)))
    if stream.read(1):
        raise ValueError('Trailing surface catalog data')
    result=[]
    for (key,material),index in zip(bindings,indices):
        if index==NO_NORMAL:normal=None
        elif index>=len(images) or images[index][0]!=material:
            raise ValueError('Normal material binding mismatch')
        else:normal=images[index][1]
        result.append((key,normal))
    return result
