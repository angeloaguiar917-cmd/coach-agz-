# Reel: "Gram vs 6pack" — 1 gram of test a week vs 6 beers a night (720p30 preview)

**Status:** first full edit, for review. Not a final export; a final would be 1080×1920. Built on the saved setup and `editing/TEXT_HOOK_ENGINE.md`; the engine output is in `edit_log.json`.
**Source:** Drive file `1MlOQQ2YWdHHQvUzdYDHtk8uNWTCMb2ES` ("Gram vs 6pack"), 1080×1920 HEVC 60 fps, 1:52.6, single take in the car.
**Output:** `coach-agz_gram-vs-sixpack_720p30.mp4`, 720×1280, 30 fps, H.264 + AAC, 1:53.2 (111.9 s of speech plus a 1.3 s end-card hold).

## Order of work
1. **Cut.**
   - The long single-pass transcript truncated 27–55 s into fragments. The source was re-transcribed in overlapping 24 s windows (`transcribe_win.py`) and cross-checked with the small and medium models.
   - No stumbles found.
   - 7 dead-air trims (≥0.22 s → about 0.12 s, frame-aligned, 8 ms fades) removed 1.70 s.
   - The cut was re-transcribed in windows: 448 words.
2. **Text hook engine** on the cut's transcript. The JSON is in `edit_log.json`.
   - **Winner (A · pain):** **1 GRAM** vs **6 BEERS** / same red flags
   - **Runners-up:** "1 GRAM vs 6 BEERS / the real winner" and "BLOODWORK just exposed / your nightly 6 PACK"
   - **Flags:**
     - `winners.md` missing.
     - Trust anchor missing in the lock-in zone (nothing invented).
     - The spoken hook runs 6.6 s, so the hold is capped at 6.0 s.
3. Captions, graphics, sound, render.

## Text hook and top-of-frame
- **Text hook:**
  - Visible on frame 0, no entry animation, 0.00–6.00 s, then a 0.15 s fade.
  - Premium mode in Barlow Condensed with boxed lines over the bright car roof.
  - **1 GRAM** and **6 BEERS** in caps and v-gold; the rest sentence case, no punctuation.
  - Top-centre, y ≈ 262–440, above the cap (y ≈ 480–520) and inside the safe zone.
- **Visual hook:** a 108% punch-in snaps in on "a thousand milligrams" at 0.20 s. After that, 108% alternates at every jump cut.
- **Topic band:** **1 GRAM** a week vs **6 BEERS** a night (with @coach.agz and the disclaimer), from 6.0 s to the midpoint.
  - The midpoint is 56.6 s and the nearest jump cut (51.0 s) is 5.5 s away. So the band fades at the midpoint itself; a jump cut is used only when one falls within 1.5 s of the midpoint.
- **Captions:** y ≈ 1450, on the upper chest above the tattoo. The chin sits at about y 1340–1400 in this framing.

## Timeline (trimmed timeline)
| Time | Speech | On screen |
|---|---|---|
| 0.0–6.0 | "a thousand milligrams of testosterone a week versus a six pack of beer every single night…" | **Text hook**, with the punch-in. |
| 6.8–30.0 | gram side | **SIDE A · 1 GRAM TEST / WEEK:**<br>• Marker rows land on each word, each status snapping in on its verb: HEMATOCRIT CLIMBS ▲, BLOOD THICKENS, BLOOD PRESSURE RISES ▲, HDL DROPS ▼, APOB CLIMBS ▲, ESTROGEN UP ▲, NATURAL PRODUCTION SHUT DOWN ▼, HEART WALL THICKENS.<br>• Verdict **NOT SAFE · NO BREAKS · NO MITIGATION** on "nobody should call it safe", with impact and shake. |
| 30.0–32.1 | "You got yourself six beers every single night" | Talking head. |
| 32.1–51.0 | beer side | **SIDE B · 6 BEERS / NIGHT:**<br>• **6** STANDARD DRINKS and **~900** KCAL/DAY.<br>• Rows: LIVER FAT ACCUMULATES ▲, GGT CLIMBS ▲, TRIGLYCERIDES CLIMB ▲, REM SLEEP DESTROYED ▼, RECOVERY UNRECOVERED ▼, TESTOSTERONE LOWER ▼, CORTISOL RAISES ▲.<br>• Verdict **GROUP 1 CARCINOGEN**, with impact and shake. |
| 51.0–55.0 | "here's where it gets uncomfortable…" | Talking head. |
| 55.0–64.3 | both show up on the same bloodwork… felony vs Super Bowl commercial | **SAME BLOODWORK (A vs B):**<br>• Columns **1 GRAM** | **6 BEERS**, with BLOOD PRESSURE / LIPIDS / LIVER MARKERS / HORMONES each flagged red in both columns as spoken.<br>• FELONY under A, SUPER BOWL AD under B.<br>• Verdict **SAME BODY · TWO STANDARDS** (the brand's own voice line). |
| 64.3–66.9 | "we're asking the wrong question" | Talking head. |
| 66.9–86.6 | who's checking | **WHO'S CHECKING (A vs B):**<br>• GUY ON GEAR: a 3-year timeline fills with green bloodwork checks every 8–10 weeks, then ✓ KNOWS ✓ MITIGATES ✓ LONGEVITY and EVEN ON 1 GRAM.<br>• GUY ON 6 BEERS: an empty 3-year timeline, MARKERS CHECKED · 0 IN 3 YEARS, then one red dot at the end: SICK → DOCTOR. |
| 86.6–97.6 | neither is great; bloodwork tells the truth, roadmap | Talking head. |
| 97.6–end | CTA | **End card:** logo, COACH AGZ, @coach.agz. THE FULL **BLOODWORK PANEL** / FRAMEWORK + PROTOCOL, then "see what **1 GRAM** or **6 BEERS** do to you". A gold **COMMENT "BLOODS"** pill, then SENT TO YOU · FREE. Disclaimer. |

## Caption notes
- **GGT** is captioned correctly (one pass heard "GTT").
- Swears are starred.
- 87.3 s: the cut pass hears "those" and the final-audio pass hears "though", so it's captioned **THOUGH** ("Realistically, though, either or…").

## Checks done
- **Captions vs final audio** (windowed medium pass): 444/447 match. The rest are the starred swears and one "then" at 30.0 s heard by that pass only. Drift: median 0.00 s, p95 0.02 s, max 0.18 s.
  - The check also flipped one call: "THOUGH" at 87.3 s was restored, and the tail re-rendered.
- **Frame 0** of the encoded file shows the full hook.
- **Frames:**
  - Strips at the hook exit and band entry, all four panel opens and closes, both shakes, the SAME BODY · TWO STANDARDS verdict, the band exit at the midpoint, the end card and the pill.
  - Full decode, all 3,395 frames.
  - Chunk seams frame-exact.
- **Sound sync:** all heavy hits are within 1 ms of their frames. No music.
- **Audio:** the source has 165 full-scale samples (59 flat-topped runs), so the clipping was baked in before upload.
  - ffmpeg `adeclip` was tried and **didn't reduce** the flat-topped runs (41 → 44 on the near-peak measure), so it wasn't used and the voice is untouched.
  - Voice +0.9 dB, then the limiter: −14.4 LUFS, peaks −2.0 dBFS.
  - **Needs a listen** for crackle.

**Not done:**
- Listening.
- Subject cutout.
- Real fonts (stand-ins).
- `winners.md`.

**Content:** the panels depict Coach AGZ's own claims and numbers (1 gram, 6 drinks, ~900 kcal, 8–10 weeks, 3 years, Group 1 carcinogen). No lab values or studies are shown. The arrows and timelines are illustrative.

## Audio fix (2026-11-03): voice was right channel only
The source recording carries the voice in the **right channel only** (left silent, about −109 dB). The earlier version of this preview carried that through, so the voice played in one ear on headphones. It also skewed the loudness readings.
- **Fix:** the right channel is copied to both channels (dual-mono), then the voice is re-mastered with the SFX bed. Left and right are now identical.
- **Result:** −14.2 to −14.3 LUFS, peaks about −2.0 dBFS. Video, captions and timing are unchanged.
- The pipeline now checks channel balance before mixing.
