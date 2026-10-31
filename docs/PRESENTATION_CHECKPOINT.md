# Presentation acceptance checkpoint

**Updated direction:** the player rejected the pixel treatment and requested an
independent game. The current build uses smooth typography, vector shapes and a
teal/slate arena. The original-match checklist below is historical reference;
current acceptance is responsive play, legible visuals, preserved progression,
and no victory before defeating the final campaign encounter.

Run `Compare Presentation.cmd`. It uses temporary progress and never writes to
the normal save. Use the supplied Unreal game separately as the reference.
This checkpoint asks whether the presentation feels recognizably like the original,
not whether the new version has more content.

## Short comparison sequence

1. In the tree, hover Damage. Compare icon size, floating rank/description/price,
   font, dark board, glow and cables with the original.
2. Hold left mouse over a node to buy one rank. Compare the press/release feedback
   and newly appearing branches. A short click or moving off the node cancels.
3. Move around with WASD. Mouse wheel zooms, middle/right drag pans and Home returns
   to the starting node. The original map positions and directions are retained.
4. Press Space to enter combat. Compare archer/bow scale, charging deformation,
   release recoil, arrow silhouette and hit feedback.
5. Shoot toward a side portal, then a top/bottom wall. Compare visual transitions
   and the stopped arrow's dim appearance.
6. Hold recall. Compare the return animation and pickup feedback. Existing combat
   rules, upgrade prices and rank caps have not been changed in this pass.

Use F5 to toggle shake, F6 to toggle hit/player flashes, and F7 to toggle local
arrow trails. F11 toggles fullscreen. Pixel/glow/color-splitting passes are removed.

The temporary profile starts with a few purchased roots and 100 points so the tree
can be explored immediately. Closing/restarting comparison restores that same
temporary starting state. For the real profile, use `Play Loop Archer.cmd`.

## Known differences to judge

- The icons are new pixel silhouettes, not the original sprite images.
- CPU glow/color separation and low-resolution scaling approximate the Unreal
  postprocess; fisheye distortion and exact shader behavior remain unreproduced.
- The tree is a flat projection of the original placement. Its exact camera tilt,
  motion curves and connector rendering are approximated.
- Audio is still synthesized. The original music and sound effects are not yet
  reproduced, which may remain a material part of the perceived difference.
- Purchase timing is a half-second hold approximation; the decoded graph establishes
  hold animation but this pass has not established identical curve timing.

Review frames: `artifacts/shop-comparison.png` and `artifacts/combat-comparison.png`.
Reproduce safely with `.venv\Scripts\python.exe analysis/shop/capture_checkpoint.py`.
