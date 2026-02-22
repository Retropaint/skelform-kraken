import pykraken as kn
import os
import sys

sys.path.append("../../skelform_kraken")
import skelform_kraken as skf

kn.init()

kn.window.create("anim test", 800, 600)

(skellington, ske_atlases) = skf.load("skellington.skf")
(skellina, ska_atlases) = skf.load("skellina.skf")
anim_time = 0

while kn.window.is_open():
    for event in kn.event.poll():
        if event.type == kn.QUIT:
            kn.window.close()

    kn.renderer.clear(kn.Color.WHITE)

    anim_frame = skf.time_frame(anim_time, skellington.animations[1], False, True)
    skellington.bones = skf.animate(
        skellington, [skellington.animations[1]], [anim_frame], [0]
    )
    bones = skf.construct(
        skellington,
        skf.ConstructOptions(position=kn.Vec2(200, 300), scale=kn.Vec2(0.1, 0.1)),
    )
    skf.draw(bones, skellington.styles, ske_atlases)

    anim_frame = skf.time_frame(anim_time, skellina.animations[1], False, True)
    skellina.bones = skf.animate(skellina, [skellina.animations[1]], [anim_frame], [0])
    bones = skf.construct(
        skellina,
        skf.ConstructOptions(position=kn.Vec2(500, 300), scale=kn.Vec2(0.1, 0.1)),
    )
    skf.draw(bones, skellina.styles, ska_atlases)

    kn.renderer.present()
    anim_time += kn.time.get_delta()
