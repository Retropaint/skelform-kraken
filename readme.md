SkelForm runtime for [Kraken Engine](https://krakenengine.org).

```
pip install skelform_kraken
```

## Demo

After installing the library:

```
skelform-demo
```

## Usage

```python
import skelform_kraken as skf
```

## Basic Setup

- `skf.load()` - loads `.skf`/`.skfe` file and returns armature & textures, to be
  used later
- `skf.animate()` - transforms the armature's bones based on the animation(s)
- `skf.construct()` - provides the bones from this armature that are ready
  for use
- `skf.draw()` - draws the bones on-screen, with the provided style(s)

### 1. Load:

```python
(armature, textures) = skf.load("skellington.skfe")
```

This should only be called once (eg; before main game loop), and `armature` and
`textures` should be kept for later use.

### 2\. Animate:

```python
# use `skf_pg.time_frame()` to get the animation frame based on time (1000 = 1 second)
time = 2000
frame = skf.time_frame(time, armature.animations[0], False, True)

print(frame) # will be at the 2 second mark of the animation

armature.bones = skf.animate(armature, [armature.animations[0]], [0], [0])
```

_Note: not needed if armature is static_

### 3\. Construct:

```python
center = kn.Vec2(screen.get_width()/2, screen.get_height()/2)

final_bones = skf.construct(
    armature,
    screen,
    skf_pg.AnimOptions(
      pos=center
    )
)
```

Modifications to the armature (eg; aiming at cursor) may be done before or after
construction.

### 4\. Draw:

```python
skf.draw(final_bones, armature.styles, textures, screen)
```
