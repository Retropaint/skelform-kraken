import zipfile
import json
import pykraken as kn
import dacite
from dataclasses import dataclass
from copy import copy
import tempfile
import shutil
import math

import sys

# sys.path.append("../../skelform_python")
import skelform_python as skfpy


@dataclass
class ConstructOptions:
    position: kn.Vec2
    scale: kn.Vec2
    velocity: kn.Vec2

    def __init__(
        self,
        position=kn.Vec2(0, 0),
        scale=kn.Vec2(0.25, 0.25),
        velocity=kn.Vec2(0, 0),
    ):
        self.position = position
        self.scale = scale
        self.velocity = velocity


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
    armature.cached_bones = skfpy.construct(armature)

    for bone in armature.cached_bones:
        bone.pos.y = -bone.pos.y

        bone.pos *= options.scale
        bone.scale *= options.scale
        bone.pos += options.position

        if skfpy.is_facing_left(options.scale):
            bone.rot = -bone.rot

        if bone.physics_id != -1:
            phys = armature.physics[bone.visuals_id]
            if phys:
                phys.global_pos -= options.velocity

        if bone.visuals_id != -1:
            visual = armature.visuals[bone.visuals_id]
            if visual and visual.vertices:
                for vert in visual.vertices:
                    vert.pos.y = -vert.pos.y
                    vert.pos *= skfpy.Vec2(options.scale.x, options.scale.y)
                    vert.pos += skfpy.Vec2(options.position.x, options.position.y)

    return armature.cached_bones


# Draws the bones to the provided screen, using the provided styles and textures.
#
# Recommended: include the whole texture array from the file even if not all will be used,
# as the provided styles will determine the final appearance.
def draw(
    armature: skfpy.Armature,
    styles: list[skfpy.Style],
    tex_imgs: list[kn.Texture],
):
    # bones.sort(key=lambda bone: bone.zindex)

    for bone in armature.constructed_bones:
        if bone.visuals_id == -1:
            continue
        visual = armature.visuals[bone.visuals_id]
        if not visual:
            continue

        tex = skfpy.get_bone_texture(visual.tex, styles)
        if not tex:
            continue

        # clip atlas to texture
        tex_imgs[tex.atlas_idx].clip_area = kn.Rect(
            pos=kn.Vec2(tex.offset.x, tex.offset.y),
            size=kn.Vec2(tex.size.x, tex.size.y),
        )

        # will be used to flip pivot rotations if necessary
        dir = -1 if skfpy.is_facing_left(bone.scale) else 1

        # setup pivot
        pivot_pos = (
            skfpy.rotate_vec2(visual.pivot_pos * tex.size, bone.rot * dir)
            * bone.scale
            * visual.pivot_scale
        )
        pivot_pos.y = -pivot_pos.y

        # render mesh
        if visual.vertices:
            # boundaries of the texture within the atlas (in 0-1 coordinates)
            lt_tex_x = tex.offset.x / tex_imgs[tex.atlas_idx].size.x
            lt_tex_y = tex.offset.y / tex_imgs[tex.atlas_idx].size.y
            rb_tex_x = (tex.offset.x + tex.size.x) / tex_imgs[
                tex.atlas_idx
            ].size.x - lt_tex_x
            rb_tex_y = (tex.offset.y + tex.size.y) / tex_imgs[
                tex.atlas_idx
            ].size.y - lt_tex_y

            # batch all triangles
            triangles = []
            for idx in visual.indices:
                vert = visual.vertices[idx]
                uv = kn.Vec2(
                    lt_tex_x + rb_tex_x * vert.uv.x, lt_tex_y + rb_tex_y * vert.uv.y
                )
                vert_pos = vert.pos
                vert_pos += pivot_pos
                triangles.append(
                    kn.Vertex(kn.Vec2(vert_pos.x, vert_pos.y), tex_coord=uv)
                )

            # draw all triangles at once
            kn.draw.geometry(
                tex_imgs[tex.atlas_idx],
                triangles,
            )
            continue

        # flip textures if scales are negative
        tex_imgs[tex.atlas_idx].flip.h = bone.scale.x < 0
        tex_imgs[tex.atlas_idx].flip.v = bone.scale.y < 0

        # render texture
        # scale must be kept positive as flipping is done with kn.texture.flip (above)
        kn.renderer.draw(
            tex_imgs[tex.atlas_idx],
            kn.Transform(
                pos=kn.Vec2(
                    bone.pos.x + pivot_pos.x - tex.size.x * abs(bone.scale.x) / 2,
                    bone.pos.y + pivot_pos.y - tex.size.y * abs(bone.scale.y) / 2,
                ),
                scale=kn.Vec2(abs(bone.scale.x), abs(bone.scale.y)),
                angle=-bone.rot,
            ),
        )

        rect = kn.Rect(bone.pos.x - 5, bone.pos.y - 5, 10, 10)
        kn.draw.rect(rect, color=kn.Color.RED)


# Returns the animation frame based on the provided time.
def time_frame(time: int, animation: skfpy.Animation, reverse: bool, loop: bool):
    return skfpy.time_frame(time, animation, reverse, loop)


# Returns the properly bound animation frame based on the provided animation.
def format_frame(frame: int, animation: skfpy.Animation, reverse: bool, loop: bool):
    return skfpy.format_frame(frame, animation, reverse, loop)
