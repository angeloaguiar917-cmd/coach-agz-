# Editor test 06: vibrant overlays, original footage (test only)

Feedback on test 05: the footage itself had been made more vibrant, which degraded it. Only the overlays should change.
Same structure, timing and audio as test 03–05. 720×1280, 30 fps, 9.4 s. It doesn't approve the style or change final-video settings.

## What changed
- **Footage reverted** to test 04: no colour grade, and the background push back to `#050810` at 68% during the graphic.
  - Verified against test 04 by mean absolute pixel difference in footage-only regions: 1.67 on the face (vs 14.43 for test 05) and 0.53 behind the panel (vs 23.73). The remaining difference is compression noise.
- **Overlays:**
  - Kept test 05's high-pop overlay palette (`#FF221C` red, `#FFC21A` gold, `#00E5FF` cyan, `#1EFF6E` green, near-black panels).
  - Added a lit gradient on the red tags and verdict bar (a hot top edge, saturated body and dark base).
  - Bloom raised further (×2.3 / ×1.8).

## Checks
Frame strips around every transition, a full decode, and the footage-difference measurement above. Audio is unchanged from test 03 (verified there). Not listened to. The fonts are stand-ins.
