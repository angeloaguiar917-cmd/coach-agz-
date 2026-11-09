# Reel 03: "3 things I'd never do on cycle again" (1080p30)

**Source:** Drive `1wuVOxJrpFsdvpQO_HP8uNlXEyiz4RoUh` ("3 things Iwouldnt do", 1080×1920 HEVC, 60 fps, 1:41.9, one clean take).
**Output:** `coach-agz_3-things-never-on-cycle_1080p30.mp4`, 1080×1920, 30 fps, H.264 High + AAC, `+faststart` (plays and saves on a phone straight from Drive).
**Style:** the saved full-test pipeline (test-06 overlay palette, clinical evidence look, every-word red-block captions, alternating 108% punch-in at each jump cut, gold edge rule). Footage is not graded.

## Cut
- One take, no retakes or misspeaks found. 16 silent gaps of 0.2 s or more were trimmed to about 0.12 s (2.5 s removed, 8 ms audio fades), giving 1:39.4. `trim.json` lists the cuts.

## Text hook (TEXT_HOOK_ENGINE)
- Frame 0 to 6.0 s: **3 CYCLE mistakes / your clinic won't like #3** (premium mode, CYCLE in v-gold). Full block in `edit_log.json`.
- Topic band from 6.0 s to the 48.5 s jump cut, with 01 · 02 · 03 chips that light up per mistake. Chip 03 flashes red with "DOCTORS ✕" on "number three will piss some doctors off".

## Overlays: a different graphic type and layout per beat
| Time | Beat | Graphic type | Layout |
|---|---|---|---|
| 0:04 | 500 mg Tren for a year | **52-week grid** fills, mg counter counts up, "NEVER AGAIN" stamp on "idiot" | lower-third card, face visible |
| 0:12 / 0:25 / 0:57 | Mistake 01 / 02 / 03 | **Giant numeral bumper** slam with a lit label bar | full-frame push |
| 0:15 | No baseline bloodwork | **Grouped bar chart**: week 0 ghost bars "?" vs week 8 bars, "Δ ?" brackets, "0 DATA POINTS" | full evidence panel |
| 0:26 | AI at one high E2 number | **Single data point**, AI pill thrown onto it | inside bumper 02 |
| 0:29 | Joints, libido, mood, IGF-1, growth | **Hub-and-spoke callouts** around the head, E2 hub on the chest | over footage |
| 0:36 | Reference range → red alert → AIs → crash | **Spectrum scale** (brand overlay ref 04): marker drifts high, RED ALERT, AI ×4 stack, marker crashes to TOO LOW, FLAT, LIBIDO ✕ | **split screen**: face window + graph |
| 0:48 | One number vs trend + biomarkers + feel | **Line chart**: one high dot, then a 6-panel trend, biomarker chips, HOW YOU FEEL ✓ | split screen |
| 0:63 | 52% hematocrit, EPO, donate, ferritin | **Gauge** sweeps into the red zone, then an **EPO loop flow** and a draining **ferritin meter** | full evidence panel |
| 1:12 | Hydration, dose, cardio first; donation last | **Ranked ladder** + 12-month strip with every-3-month donations struck out | **push-aside**: footage slides right |
| 1:20 | Read the panel before touching anything | **Roadmap route** with pins, AI · DOSE · DONATE locked until the panel | full evidence panel |
| 1:26 | CTA | End card: logo, COMMENT "ROADMAP" pill, BEFORE · DURING · AFTER checks, disclaimer | lower card |

Graph shapes and bar heights are illustrative; no values are shown other than what's spoken (500 mg, 52%, 52 weeks, 3 months).

## Sound
Same synth palette as the full test (sub hits, scan sweeps, digital ticks, one impact per beat); `sfx.py`. Speech is normalised to about −14 LUFS.

## Files
`reel_render.py` (frames), `sfx.py`, `cut2.py` + `trim.json` (cut), `words.json` (caption timing on the cut), `edit_log.json` (text hook).
