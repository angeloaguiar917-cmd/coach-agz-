# GH2: "Your GH results aren't on the scale" (1080p final)

**Source:** Drive `1EmdecevkcPlbECVQX3jHrENQ11d5Zhsx` ("GH2", 1080×1920 HEVC, 60 fps, 1:50; single take with a few in-camera jump cuts).
**Output:** `coach-agz_gh-results-scale_1080p.mp4`: 1080×1920, 30 fps, H.264 High 4.2 + AAC 192k, faststart (plays and saves on iPhone/Android), 1:46.5, −14.3 LUFS, true peak −1.4 dBTP.

## Cut
- Removed: "So I think" (open), "I mean, realistically," (0:10), "Well, I guess" (1:18).
- Silent runs ≥ 0.26 s trimmed to ~0.14 s (energy-based, threshold 51 dB on the 16 kHz track). That's 11 segments with 8 ms audio fades; `segments.json` holds the source in/out points.
- Every segment's audio was checked against the source: level within 0.3 dB, sync offset 0.0 ms.
- The cut was re-transcribed for captions (391 words). Fixes: "antibiotics" → **anabolics** (confirmed on a medium-model re-check), "IGF one" → IGF-1, "college and" → collagen.

## Text hook (see `edit_log.json`)
Your **GH** results / aren't on the scale. Frame 0 → 4.9 s, then a topic band "GH results · track the right thing" runs to the midpoint (53.3 s).

## Overlays: a different type per beat
| Time | Type | What it shows |
|---|---|---|
| 0:06 | Side card, LCD | Bathroom-scale readout flickers, settles on 214.6; "MUSCLE: LOADING" bar stuck |
| 0:09 | Line graph | Fat-oxidation curve over weeks 0–4; WK 2–3 band, rising fat droplets, "HIGHER RATE" |
| 0:16 | Gantt strip | FAT LOSS bar fills now; MUSCLE "NOT YET", hatched block at MO 6+; playhead |
| 0:22 | Twin cards | Scale returns (handoff) with a flat 14-day trend and "NO CHANGE"; muscle cross-section fills with intramuscular water |
| 0:30 | Stacked bars + big stat | START vs NOW body comp (fat ↓, lean ↑, water); scale net change **0.0 LB**; mirror ✓ |
| 0:45 | Pathway schematic | Testosterone/anabolics → muscle DIRECT; GH → muscle NOT DIRECT; GH → liver → IGF-1 → muscle; gates "IGF-1 LOW" and "TRAINING OFF" → verdict bar NO IGF-1 SIGNAL = NO GROWTH |
| 0:56 | Expectation vs reality graph | Slow-burn gold curve to "6 MO: NOTICEABLE"; red dashed "+10 LB / 1 MO" expectation; THE GAP; **WRONG TIMING** stamp |
| 1:06 | Progress-ring tile grid | Collagen, tendon, connective tissue, skin, hair, nails, sleep light up on the word; rings fill slowly; MONTHS ✓ / WEEKS ✕ |
| 1:16 | Full-screen carousel + picture-in-picture | Navy/gold "Audit" page wipes in behind the gold rule; live PiP of Coach; TRACK vs IGNORE columns tick in on each spoken item |
| 1:29 | Calendar strip + big stat | 24 week-dots fill, "6 MONTHS" lands, "THEN JUDGE IT" |
| 1:35 | Route stepper | Bloodwork → Analyze → Pivot → Optimize along a gold path |
| 1:40 | CTA | Logo, FREE · FULL HGH FRAMEWORK, gold COMMENT "GH" bar |

Also: every-word captions (red active-word block; GH/IGF-1/six months recolour gold on the spoken word, scale/wrong red), alternating 108% punch-ins on jump cuts, a 112% punch on "where most guys get it wrong", and clinical SFX (sub hits, ticks, scan sweeps, two impacts). Footage is not graded.

## QC done
- Overview every 1.5 s; full-size stills of every scene; frame strips through the hook exit, panel 01 entry, verdict, stamp, carousel wipe in/out.
- Fixed during review: pathway overflow (verdict covered LIVER), cards/strips moved lower and shorter to clear the mouth, band overlapping the fading hook, scale card fading through panel 01 (now a hard exit on the jump cut), carousel exit colliding with the calendar strip, a render crash on a zero-length dashed line.
- Final file: 3196 frames, splice at frames 270–300 re-checked; loudness −14.3 LUFS, true peak −1.3 dBTP after AAC (limiter run oversampled).
- **Not done:** listening. SFX placement was checked against timings, not by ear.
- **Illustrative, not data:** the 214.6 lb reading, body-comp percentages and all graph curves. Fonts are stand-ins (Bebas Neue, DM Sans, JetBrains Mono, Barlow Condensed).
