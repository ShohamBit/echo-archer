# UI and Rendering

Rendering lives in `src/loop_archer/main.py`.

## Window Mode

The game starts fullscreen. `F11` toggles fullscreen/windowed. Window resize is
handled only when not fullscreen.

## Arena

The arena is drawn as a large circle centered on screen. Its radius comes from
`arena_radius_for_screen(width, height)`:

- it keeps the original MVP radius at `1280x720`
- it grows on larger displays to use more fullscreen space

The player is still blocked by the circular arena boundary.

## HUD

Top-left metrics:

- loop number
- run shards
- total shards
- damage
- Echo Decay status

Top-center:

- run timer

Top-right:

- best time

Bottom-center:

- wide HP bar spanning the middle half of the screen
- numeric HP is intentionally hidden for now

When settings are added later, numeric HP can become an optional setting.

## Shape Language

Current visual identities:

- player: warm circle
- chaser enemy: larger red triangle body with a darker core and forward mark
- arrows: yellow line strokes
- shards: cyan circles

Future enemy shape ideas:

- fast enemy: sharp diamond
- tank enemy: square/block
- shooter enemy: pentagon or hexagon
- exploder enemy: spiky star

Keep collision circles separate from visual shape. Shape changes should improve
readability without changing physics unless a feature explicitly asks for it.

## Death and Upgrade Screens

The death summary is an overlay panel showing:

- `LOOP FAILED`
- death reason
- time survived
- enemies defeated
- shards gained

The upgrade screen currently shows clickable upgrade cards. Cards display branch,
name, description, and status:

- `Owned`
- `Locked`
- `Buy: <cost>`
- `Need: <cost>`
