# Full 02: "Prolactin / 19-nor lactation + gyno" (v01, 1080×1920, 30 fps)

**Source:** Drive `1AKylfQ6Jecdac6XflOmFoeGN4IT61bt7` (1080×1920 HEVC 60 fps, 1:44, car selfie, one take).
**Output:** `coach-agz_prolactin-19nor_v01_1080p.mp4`, 1:39, H.264 High + AAC, faststart (phone-ready), −14.5 LUFS.

## Instructions for this video
- No text hook at frame 0 and no topic band (Coach AGZ's request). See `edit_log.json`.
- Use a different overlay type for each beat. Keep the face recognizable: graphics sit above the cap, or the face moves into a framed PiP.
- Leave the footage ungraded (QUALITY_STANDARD §1). Only the overlays are vibrant (test-06 palette + bloom).

## Cut
- Stumble "mammary glan—" removed (source 41.80–42.60).
- 17 dead-air trims (≥0.24 s pauses cut to ~0.12 s), 5.0 s removed in total, 8 ms crossfades. Punch-in alternates 100/108% at each cut.

## Overlay types (14, no repeats)
Post mockup + MISLABELED flag · prior-upload tiles + engagement meter · FLEX→WARNING SIGN toggle · 2-step stepper (calls back at "simple version") · bar chart · heavy compound chips · full-screen receptor mechanism + X-ray duct schematic (circle PiP right) · threshold line graph → GALACTORRHEA · gyno domino with dials, balance scale and tissue target (circle PiP left) · paper lab report → scan wipe → two-lane pathways · fork diagram 1 hormone → 2 outcomes · post-card callback + NOT ELITE GAINS slam · protocol checklist (portrait PiP) · CTA cover card + COMMENT "PROLACTIN" pill.

## Notes
- The lab report is generic and shows no invented values ("IN RANGE", "PALPABLE"). Bars and graph are relative, with no numbers.
- Profanity in captions is starred. Fonts are stand-ins.
- QC: caption sync (median 0.00 s, p95 0.06 s against the final-audio transcript), overview sheet, and transition strips. **Not listened to**: please check the SFX levels by ear.
- Rebuild: `plan_cut.py` → `assemble_audio.py` → `build_caps.py` → `facetrack.py` → `render.py chunk a b out` → `sfx.py` → mux. These need `mezz30.mp4`, the audio and fonts in a scratch folder.
