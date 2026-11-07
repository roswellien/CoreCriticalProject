"""Author existing BWMESH4 rigid batches and BWTEX1 constant review materials.

This module creates no geometry or animation. Callers supply donor-local triangle
corners, ordered rest frames and references recovered from their own controller.
"""

import hashlib
import math
import struct
from dataclasses import dataclass

REQUIRED_BONES = {
    "Pelvis",
    "Torso_Twist",
    "Upperarm_Left",
    "Upperarm_Right",
    "Forearm_Left",
    "Forearm_Right",
    "Thigh_Left",
    "Thigh_Right",
    "Calf_Left",
    "Calf_Right",
    "Foot0_Left",
    "Foot0_Right",
}
REQUIRED_REFERENCES = {
    "hip",
    "torso",
    "larm",
    "rarm",
    "lthigh",
    "rthigh",
    "lcalf",
    "rcalf",
    "lfoot",
    "rfoot",
}


@dataclass(frozen=True)
class Bone:
    name: str
    control: str
    parent: int
    rest: tuple[float, ...]


@dataclass(frozen=True)
class Batch:
    owner: str
    visibility: str
    bone: int
    vertices: bytes
    color: int = 0xFFFFFFFF


def _name(value, *, empty=False):
    if not isinstance(value, str) or (not value and not empty):
        raise ValueError("A nonempty ASCII name is required")
    try:
        encoded = value.encode("ascii")
    except UnicodeEncodeError as error:
        raise ValueError("Names must be ASCII") from error
    if len(encoded) > 31 or any(byte < 32 or byte > 126 for byte in encoded):
        raise ValueError("Names must contain at most 31 printable ASCII characters")
    return encoded.ljust(32, b"\0")


def _matrix(values):
    values = tuple(values)
    if len(values) != 16 or not all(math.isfinite(value) for value in values):
        raise ValueError("Rest frames must contain 16 finite values")
    if values[12:] != (0, 0, 0, 1):
        raise ValueError("Rest frames must be affine row-major matrices")
    determinant = (
        values[0] * (values[5] * values[10] - values[6] * values[9])
        - values[1] * (values[4] * values[10] - values[6] * values[8])
        + values[2] * (values[4] * values[9] - values[5] * values[8])
    )
    if not math.isfinite(determinant) or abs(determinant) < 1e-12:
        raise ValueError("Rest frames must be invertible")
    return struct.pack("<16d", *values)


def encode_mesh(
    bones,
    references,
    batches,
    *,
    walk_x,
    walk_z,
    hip_drop=0.0,
    ground_reference=True,
    hinge_axes=False,
):
    """Encode rigid batches without altering their supplied corner bytes."""
    bones, batches = list(bones), list(batches)
    if not 1 <= len(bones) <= 256 or not 1 <= len(references) <= 128:
        raise ValueError("Donor rig counts exceed the native bounds")
    if not 1 <= len(batches) <= 256:
        raise ValueError("Batch count exceeds the native bound")
    names = [bone.name for bone in bones]
    if len(set(names)) != len(names) or not REQUIRED_BONES <= set(names):
        raise ValueError("Donor bones must be unique and include the canonical joints")
    if not REQUIRED_REFERENCES <= set(references):
        raise ValueError("Required original controller references are missing")
    if type(ground_reference) is not bool or type(hinge_axes) is not bool:
        raise ValueError("Rig flags must be booleans")
    if hinge_axes:
        required_axes = {
            "HingeAxis_" + joint
            for joint in ["Calf_Left", "Calf_Right", "Forearm_Left", "Forearm_Right", "Foot0_Left", "Foot0_Right"]
        }
        if not required_axes <= set(names):
            raise ValueError("Measured hinge frames are missing")
        lookup = {bone.name: bone for bone in bones}
        for side, prefix in [("Left", "l"), ("Right", "r")]:
            for joint, upper in [("Calf_", "Thigh_"), ("Forearm_", "Upperarm_"), ("Foot0_", "Calf_")]:
                axis = lookup["HingeAxis_" + joint + side]
                if (
                    axis.control
                    or type(axis.parent) is not int
                    or not 0 <= axis.parent < len(bones)
                    or bones[axis.parent].name != upper + side
                ):
                    raise ValueError("Measured hinge frame has an invalid parent")
            points = [bone for bone in bones if bone.name.startswith("Sole_" + side + "_")]
            if not 3 <= len(points) <= 64:
                raise ValueError("Measured sole points are missing or excessive")
            for point in points:
                if (
                    point.control
                    or type(point.parent) is not int
                    or not 0 <= point.parent < len(bones)
                    or bones[point.parent].control
                    not in {prefix + "foot", prefix + "toe01", prefix + "toe02"}
                ):
                    raise ValueError("Measured sole point has an invalid parent")
    walk_x, walk_z = tuple(walk_x), tuple(walk_z)
    if len(walk_x) != 2 or len(walk_z) != 2:
        raise ValueError("Gait metadata needs left and right values")
    gait = (hip_drop, *walk_x, *walk_z)
    if not all(math.isfinite(value) for value in gait) or not 0 <= hip_drop <= 10:
        raise ValueError("Invalid native gait metadata")
    output = bytearray(b"BWMESH4\0")
    output += struct.pack(
        "<4I5d",
        len(batches),
        len(bones),
        len(references),
        int(ground_reference) | (2 if hinge_axes else 0),
        *gait,
    )
    ancestors = []
    for index, bone in enumerate(bones):
        if type(bone.parent) is not int or not -1 <= bone.parent < index:
            raise ValueError("Donor parents must precede their children")
        if bone.control and bone.control not in references:
            raise ValueError("Unknown original controller binding")
        output += _name(bone.name) + _name(bone.control, empty=True)
        output += struct.pack("<i", bone.parent) + _matrix(bone.rest)
        inherited = ancestors[bone.parent] if bone.parent >= 0 else set()
        ancestors.append(inherited | ({bone.control} if bone.control else set()))
    for name, matrix in references.items():
        output += _name(name) + _matrix(matrix)
    for batch in batches:
        if type(batch.bone) is not int or not 0 <= batch.bone < len(bones):
            raise ValueError("Batch has an invalid rigid bone")
        # Distance dispatch may fold a toe batch into its foot while preserving
        # the actual toe bone and the same rig in both LOD payloads.
        if batch.owner not in references or batch.owner not in ancestors[batch.bone]:
            raise ValueError("Batch owner disagrees with its donor binding")
        if not isinstance(batch.vertices, bytes) or len(batch.vertices) % 96:
            raise ValueError("Batches require complete triangles of eight float32 corner values")
        count = len(batch.vertices) // 32
        if not 3 <= count <= 65535:
            raise ValueError("Native batch vertex count is out of bounds")
        if type(batch.color) is not int or not 0 <= batch.color <= 0xFFFFFFFF:
            raise ValueError("Invalid packed batch color")
        for corner in struct.iter_unpack("<8f", batch.vertices):
            if not all(math.isfinite(value) for value in corner):
                raise ValueError("Nonfinite corner data")
            normal_length = math.sqrt(sum(value * value for value in corner[3:6]))
            if abs(normal_length - 1.0) > 0.0001:
                raise ValueError("Corner normals must be unit length")
        output += _name(batch.owner) + _name(batch.visibility)
        output += struct.pack("<III", batch.bone, count, batch.color)
        output += batch.vertices
    return bytes(output)


def encode_constant_textures(materials, batch_materials):
    """Encode opaque 1x1 RGB565 source-part colors, with exact batch indices."""
    materials, indices = list(materials), list(batch_materials)
    if not 1 <= len(materials) <= 64 or not 1 <= len(indices) <= 256:
        raise ValueError("Texture/material counts exceed the native bounds")
    if len({name for name, _ in materials}) != len(materials):
        raise ValueError("Material names must be unique")
    if any(type(index) is not int or not 0 <= index < len(materials) for index in indices):
        raise ValueError("Batch material index is out of bounds")
    output = bytearray(b"BWTEX1\0\0" + struct.pack("<II", len(indices), len(materials)))
    output += struct.pack("<" + "I" * len(indices), *indices)
    for name, rgb in materials:
        if len(rgb) != 3 or any(type(value) is not int or not 0 <= value <= 255 for value in rgb):
            raise ValueError("Review materials need three RGB8 components")
        red, green, blue = rgb
        pixels = struct.pack("<H", ((red >> 3) << 11) | ((green >> 2) << 5) | (blue >> 3))
        identity = int.from_bytes(hashlib.sha256(pixels).digest()[:8], "little")
        output += _name(name) + struct.pack("<IIQ", 1, 1, identity) + pixels
    return bytes(output)
