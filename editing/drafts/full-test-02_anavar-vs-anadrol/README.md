# Full test 02: Anavar vs Anadrol (1080p30, phone-ready)

**Source:** Drive `1Ar0JpA2sVbQ6W4qmstbIaWE7Q19W4V6m` (1080×1920 HEVC, 30 fps, 80.7 s, single take in the car).
**Output:** `coach-agz_anavar-vs-anadrol_1080p30.mp4`. 1080×1920, 30 fps, H.264 High 4.2, yuv420p, AAC 192k, faststart. 80.0 s, 89 MB, −14.2 LUFS, true peak −1.3 dBFS.

## Cut
Two pauses tightened (0.20 s after "defined" and 0.40 s after "sodium") plus the tail. Those are the only jump cuts. `edit_log.json` has the frame ranges.

## Overlay plan (toned down, varied: no type repeats)
| Time (src) | Type | Layout |
|---|---|---|
| 0:00–0:06 | Frame-0 text hook "ANAVAR vs ANADROL / What most guys get wrong" (native mode) | Full |
| 0:06–0:40 | Topic band (engine rule: after the hook, until the midpoint) | Full, top strip |
| 0:13, 0:24, 0:35, 0:45 | Chapter blocks 01–04 (gold block slides from the left edge) | Full |
| 0:52–0:56 | Kinetic VS slam → red strike + WRONG QUESTION | Full, punch-in 113% |
| 0:56–1:04 | Diet switchboard: calorie toggles OFF → result meters empty; compound chip plugs in, nothing moves; toggles ON on "food decides" → bars fill | **Split screen**: graphic on top, footage pushed down at 1:1 |
| 1:04–1:12 | Bloat dashboard: estrogen / water / sodium dials swing into the red on each spoken word | **Inverse split**: footage pushed up, dashboard below |
| 1:13–1:20 | CTA card (logo, FREE list, COMMENT "ORALS" pill) + a "sent you" notification on "I'll send it" | Full |

- **Face:** never blurred, darkened or scaled. Graphics sit in the dark roof area above the cap, or the footage slides as a whole at 1:1.
- **Captions:** in the full layout they sit at the chin line. In split layouts they move to the seam, and they hide for the 0.36 s while the layout moves.
- **Footage:** no grade.

## Review done
- Contact sheet every 2 s. Frame strips around the hook exit, both jump cuts, and every layout transition (entering split, split → inverse, inverse → full).
- **Fixed during review:**
  - Hook width.
  - Captions over the switchboard.
  - Notification colliding with captions.
  - Disclaimer showing over the face in split.
  - Band/hook overlap.
  - Captions crossing the face during transitions.
- **Loudness:** measured with ebur128.
- **Sound effects:** synthesized (sub hits, ticks, sweeps, switches) and placed by code on the landing frames. One lead-in sweep fell inside the first trim and was dropped; its hit still lands.

## Not done
- Not listened to. Check the sound effects mix by ear.
- Caption words come from a Whisper medium.en transcript of the source. I spot-checked them visually but didn't do a second transcription pass on the cut.
- Fonts are stand-ins (Bebas Neue, DM Sans, JetBrains Mono).
- First half (0:07–0:50) has chapter blocks only, no mechanism graphics. That was the toned-down plan.
