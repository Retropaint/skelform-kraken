import zipfile
import json
import pykraken as kn
import dacite
from PIL import Image
from dataclasses import dataclass
from copy import copy
import tempfile
import shutil

import sys

# sys.path.append("../../skelform_python")
import skelform_python as skfpy


@dataclass
class ConstructOptions:
    position: kn.Vec2
    scale: kn.Vec2

    def __init__(
        self,
        position=kn.Vec2(0, 0),
        scale=kn.Vec2(0.25, 0.25),
    ):
        self.position = position
        self.scale = scale


# Loads an `.skfe` file.
def load(path: str):
    with zipfile.ZipFile(path, "r") as zip_file:
        armature_json = json.load(zip_file.open("armature.json"))

    armature = dacite.from_dict(data_class=skfpy.Armature, data=armature_json)
    textures = []

    with zipfile.ZipFile(path, "r") as zip_file:
        for atlas in armature.atlases:
            with zip_file.open(atlas.filename) as src:
                with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
                    shutil.copyfileobj(src, tmp)
                    tmp.flush()
                    textures.append(kn.Texture(tmp.name))

    return (armature, textures)


def animate(
    armature: skfpy.Armature,
    animations: list[skfpy.Animation],
    frames: list[int],
    smooth_frames: list[int],
):
    return skfpy.animate(armature, animations, frames, smooth_frames)


# Returns the constructed array of bones from this armature.
#
# While constructing, several options (positional offset, scale) may be set.
def construct(armature: skfpy.Armature, options: ConstructOptions):
    final_bones = skfpy.construct(armature)

    for bone in final_bones:
        bone.pos.y = -bone.pos.y

        bone.pos *= options.scale
        bone.scale *= options.scale
        bone.pos += options.position

        bone.rot = skfpy.check_bone_flip(bone.rot, options.scale)

        if not bone.vertices:
            continue

        for vert in bone.vertices:
            vert.pos.y = -vert.pos.y
            vert.pos *= skfpy.Vec2(options.scale.x, options.scale.y)
            vert.pos += skfpy.Vec2(options.position.x, options.position.y)

    return final_bones


# Draws the bones to the provided screen, using the provided styles and textures.
#
# Recommended: include the whole texture array from the file even if not all will be used,
# as the provided styles will determine the final appearance.
def draw(
    bones: list[skfpy.Bone],
    styles: list[skfpy.Style],
    tex_imgs: list[kn.Texture],
):
    bones.sort(key=lambda bone: bone.zindex)

    for bone in bones:
        tex = skfpy.get_bone_texture(bone.tex, styles)
        if not tex:
            continue

        tex_imgs[tex.atlas_idx].clip_area = kn.Rect(
            pos=kn.Vec2(tex.offset.x, tex.offset.y),
            size=kn.Vec2(tex.size.x, tex.size.y),
        )

        if bone.vertices:
            lt_tex_x = tex.offset.x / tex_imgs[tex.atlas_idx].size.x
            lt_tex_y = tex.offset.y / tex_imgs[tex.atlas_idx].size.y
            rb_tex_x = (tex.offset.x + tex.size.x) / tex_imgs[
                tex.atlas_idx
            ].size.x - lt_tex_x
            rb_tex_y = (tex.offset.y + tex.size.y) / tex_imgs[
                tex.atlas_idx
            ].size.y - lt_tex_y
            for idx in range(-1, len(bone.indices), 3):
                v0 = bone.vertices[bone.indices[idx - 0]]
                v1 = bone.vertices[bone.indices[idx - 1]]
                v2 = bone.vertices[bone.indices[idx - 2]]
                tri = (
                    kn.Vertex(
                        kn.Vec2(v0.pos.x, v0.pos.y),
                        tex_coord=kn.Vec2(
                            lt_tex_x + rb_tex_x * v0.uv.x, lt_tex_y + rb_tex_y * v0.uv.y
                        ),
                    ),
                    kn.Vertex(
                        kn.Vec2(v1.pos.x, v1.pos.y),
                        tex_coord=kn.Vec2(
                            lt_tex_x + rb_tex_x * v1.uv.x, lt_tex_y + rb_tex_y * v1.uv.y
                        ),
                    ),
                    kn.Vertex(
                        kn.Vec2(v2.pos.x, v2.pos.y),
                        tex_coord=kn.Vec2(
                            lt_tex_x + rb_tex_x * v2.uv.x, lt_tex_y + rb_tex_y * v2.uv.y
                        ),
                    ),
                )
                kn.draw.geometry(tex_imgs[tex.atlas_idx], tri)
            continue

        kn.renderer.draw(
            tex_imgs[tex.atlas_idx],
            kn.Transform(
                pos=kn.Vec2(
                    bone.pos.x - tex.size.x * bone.scale.x / 2,
                    bone.pos.y - tex.size.y * bone.scale.y / 2,
                ),
                scale=kn.Vec2(bone.scale.x, bone.scale.y),
                angle=-bone.rot,
            ),
        )


# Returns the animation frame based on the provided time.
def time_frame(time: int, animation: skfpy.Animation, reverse: bool, loop: bool):
    return skfpy.time_frame(time, animation, reverse, loop)


# Returns the properly bound animation frame based on the provided animation.
def format_frame(frame: int, animation: skfpy.Animation, reverse: bool, loop: bool):
    return skfpy.format_frame(frame, animation, reverse, loop)
