import pykraken as kn
import os
import sys
import copy

sys.path.append("../../skelform_kraken")
import skelform_kraken as skf

kn.init()

kn.window.create("anim test", 800, 600)

(skellington, ske_atlases) = skf.load("skellington.skf")
# (skellina, ska_atlases) = skf.load("skellina.skf")
anim_time = 0
dir = 1
speed = 5
last_anim_idx = -1
anim_idx = 0
yvel = 0
ground = kn.window.get_size().y / 2 + 50
player_pos = kn.Vec2(400, ground)

font = kn.Font("kraken-clean", 24)


# helper for finding bone by name
def bone(name, bones):
    for bone in bones:
        if bone.name == name:
            return bone


while kn.window.is_open():
    for event in kn.event.poll():
        if event.type == kn.QUIT:
            kn.window.close()

    anim_idx = 0

    # gravity
    yvel += 0.1
    if player_pos.y > ground:
        yvel = 0
    player_pos.y += yvel

    # left & right movement
    if kn.key.is_pressed(kn.S_a):
        dir = -1
        player_pos.x -= speed
        anim_idx = 1
    if kn.key.is_pressed(kn.S_d):
        dir = 1
        player_pos.x += speed
        anim_idx = 1

    # jumping
    if kn.key.is_just_pressed(kn.S_SPACE) and player_pos.y >= ground:
        player_pos.y = ground - 1
        yvel = -5

    # jumping/falling animations
    if yvel > 0:
        anim_idx = 3
    elif yvel < 0:
        anim_idx = 2

    kn.renderer.clear(kn.Color.GREY)

    # reset animation timer whenever animation changes, so it plays from start
    if last_anim_idx != anim_idx:
        anim_time = 0
        last_anim_idx = anim_idx

    # Animate Skellington
    anim_frame = skf.time_frame(
        anim_time, skellington.animations[anim_idx], False, True
    )
    skellington.bones = skf.animate(
        skellington, [skellington.animations[anim_idx]], [anim_frame], [20]
    )

    # make immutable edits to armature for construction
    skellington_c = copy.deepcopy(skellington)

    # point shoulder and head to mouse
    skel_scale = 0.15
    shoulder_target = bone("Left Shoulder Target", skellington_c.bones)
    looker = bone("Looker", skellington_c.bones)
    raw_mouse = kn.mouse.get_pos()
    mouse = skf.skfpy.Vec2(
        -player_pos.x / skel_scale * dir + raw_mouse[0] / skel_scale * dir,
        player_pos.y / skel_scale - raw_mouse[1] / skel_scale,
    )
    shoulder_target.pos = mouse
    looker.pos = mouse

    # flip shoulder IK constraint if looking the other way
    looking_back_left = dir == -1 and raw_mouse[0] > player_pos.x
    looking_back_right = dir != -1 and raw_mouse[0] < player_pos.x
    if looking_back_left or looking_back_right:
        bone("Skull", skellington_c.bones).scale.y = -1
        bone("Hat", skellington_c.bones).rot = -bone("Hat", skellington_c.bones).rot
        bone("LSIK", skellington_c.bones).ik_constraint = "Clockwise"
    else:
        bone("LSIK", skellington_c.bones).ik_constraint = "CounterClockwise"

    # Construct Skellington
    bones = skf.construct(
        skellington_c,
        skf.ConstructOptions(position=player_pos, scale=kn.Vec2(0.1 * dir, 0.1)),
    )

    # Draw Skellington!
    skf.draw(bones, skellington.styles, ske_atlases)

    instructions = kn.Text(font)
    instructions.text = "A - Move Left\nD - Move Right\nSpace - Jump\nSkellington will look at and reach for cursor"
    instructions.draw(kn.Vec2(10, 10))

    kn.renderer.present()
    anim_time += kn.time.get_delta()
