# Reel: "Normal Reference Ranges" — testosterone reference ranges (native 1080p + phone copy)

**Source:** Drive file `1rnuoYO2tZtTiwVnggdxGGT-FVCpZLDKC`, 1080×1920 HEVC 30 fps, 1:47.7, single office take.
**Output:** `coach-agz_reference-ranges_1080p_phone.mp4`, 1080×1920, two-pass ~2.5 Mbps, phone-sized. Master: `coach-agz_reference-ranges_1080p_master.mp4` (CRF 16, 68 MB, under the git limit this time).

## Work
- **Audio:** both channels carry the voice, no clipping. Voice gain and limiter to −14.3 LUFS.
- **Transcription:** gap-guarded windows, no gaps. The key figures were re-checked by two models: 250–900 ng/dL, median 500, the guys at 300 and 880, and "15,000 free testosterone".
- **Captions:**
  - "total T **or** free T" corrected to "your free T" (both focused passes agree).
  - "ng for dl" corrected to NANOGRAMS PER DECILITER.
  - Swears starred.
- **Cut:** 6 dead-air trims (0.67 s). No stumbles.
- **Text hook:** "Normal **TESTOSTERONE** / your doctor's dismissal" (`edit_log.json`).

## Overlays: ten formats, all new
| Time | Format |
|---|---|
| 6.0 s | **Lab-result chip** TOTAL TESTOSTERONE · WITHIN REFERENCE RANGE ✓, struck through, with a red **DISMISSED** verdict bar on "dismissal" |
| 7.7 s | **Full-screen bell curve**: draws on, fills with population dots, shades the **middle 95%** (2.5% tails), "= PERFECTLY NORMAL" |
| 17 s | **Population pictogram**: an 80-person grid where people light up per trait, with OVERWEIGHT / TIRED / DEPRESSED / MEDICATIONS / PRESCRIPTIONS / ANTIDEPRESSANTS chips (floats above the cap) |
| 24.4 s | **Reference-range bar** (ng/dL, 0–1200): "YOUNG · HEALTHY · NOT OBESE", the 250–900 band grows, MEDIAN 500 tick, GUY AT 300 and GUY AT 880 markers, BOTH "NORMAL" |
| 43 s | The markers **morph into two batteries** (300 nearly empty, 880 full): SAME FEEL? / BOTH OPTIMIZED? |
| 48 s | **3-number rule flip tiles**: ONE NUMBER struck out, then 1 TOTAL T, 2 FREE T, 3 SHBG flip over on each word, + HOW YOU ACTUALLY FEEL |
| 60 s | **Warehouse and trucks line schematic**: crates stack in the warehouse (TOTAL T), trucks drive out (FREE T, DELIVERING), then they stop (FULL WAREHOUSE / NOTHING MOVING) and **0% UTILIZED** lands |
| 79 s | **Three-zone meter** (floats above the cap): MEDIOCRE / OPTIMAL / CHASING A NUMBER, with the marker swinging to "chasing" and settling on OPTIMAL. "Not where the lab starts caring" |
| 93.7 s | **Full-screen kinetic slam**: REFERENCE / RANGES, slashed red, **MEAN SH*T** |
| 95.4 s | **"BLOODWORK BIBLE" book-cover end card**, then a **COMMENT "LEVELS"** stamp and SENT TO YOU |

- **Full-screen scenes** (footage pushed back, topic band hidden) alternate with face-on stretches and floating graphics, so the face shows every few beats.
- **Content:** every number is Coach AGZ's own. The study is shown only as he describes it ("young, healthy, not obese"), not named. The bell curve and pictogram are illustrative.

## Checks done
- **Decode:** 3,249 frames at 1080×1920 (master and phone copy). Phone copy 36 MB, −14.4 LUFS, peaks −1.7 dBFS.
- **Frames:** strips at every scene in and out, the dismissal, the pictogram, the battery morph, the zone meter, the slam and the end card.
- **Fixed in review:**
  - The DISMISSED bar hid the chip it dismisses.
  - The zone meter covered the mouth (moved above the cap).
  - The trucks ran off the frame edge.
- **Captions vs final audio:** drift median 0.01 s, p95 0.05 s.
  - That pass dropped 79–87 s, but both source passes heard it, so the captions stand.
  - At 53 s the passes split between "your free T" and "or free T"; the captions keep "your".
- **Sound sync:** all 19 heavy hits within 2 ms of their frames. No music. Not listened to.

**Not done:**
- Listening.
- Subject cutout.
- Real fonts (stand-ins).
- `winners.md`.
