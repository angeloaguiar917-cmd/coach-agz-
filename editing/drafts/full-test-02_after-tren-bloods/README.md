# Full test 02: "After Tren bloods" (1080p30)

**Source:** Drive `1b3iFLzSHLldcCyWdAkGzQavKxkfi90kN` (1080×1920 HEVC, 60 fps, 1:44.6, one continuous take in the kitchen).
**Output:** `coach-agz_after-tren-bloods_1080p30.mp4`, 1080×1920, 30 fps, 1:42.4, H.264 High + AAC, `faststart` (plays and saves on a phone).
**Brief:** saved setup and style; 1080p; downloadable to the phone; **more overlay variety** (graphs, more graphics, vibrant, on brand).

## Cut
- Single take with no retakes or misspeaks, so the cut only tightens pauses: 10 pauses of 0.24 to 0.6 s were cut to about 0.12 s. That removes 2.1 s with frame-aligned cuts and 8 ms audio fades (`trim.json`).
- The cut audio was re-transcribed for captions (`words_cut.json` → `words_cap.json`). Name fixes: TRENBOLONE, TREN, ApoB. Spoken numbers are shown as digits (100, 132, 54, 55, 56) and "f*cking" is starred.
- Transcription used NVIDIA Parakeet TDT 0.6B through sherpa-onnx, because HuggingFace is blocked in this environment.

## Text hook (TEXT_HOOK_ENGINE)
`500+ TREN panels` / `same red flags every time`. Premium mode (Barlow Condensed stand-in, which has lowercase, so it keeps rule 8's sentence case). Fully visible on frame 0 and held to 5.5 s. The first punch-in lands on "Tren" at 0.88 s. Then the topic band "Bloodwork after 12 weeks on TREN" runs until the 51.2 s midpoint. The full block is in `edit_log.json`.

## Overlays: 13 beats in 12 different types, none repeated back to back
| Time | Type | Placement | What it shows |
|---|---|---|---|
| 0:01.8 | **Protocol strip** | lower card | DOSE meter maxes, HIGH tag, then 12 week cells fill and a scan line sweeps on "blood work" |
| 0:05 | **Body-scan HUD** | on the footage (no card) | MIRROR CHECK brackets, cyan scan sweep, DRY / HARD / VASCULAR callouts with leader lines, PHYSIQUE meter at PEAK, then MIRROR = PASS flips to BLOODWORK = ? on "But" |
| 0:12 | **Evidence meter** | lower card | HUMAN RESEARCH meter barely fills: ALMOST NONE. ANECDOTAL chip = real-world bloodwork |
| 0:18 | **Big-stat counter + document stack** | full panel | 500+ counts up while five lab sheets (with H/L flags) fan in. SAME PATTERN EVERY TIME |
| 0:22.6 | **Hormone-axis schematic** | full panel (handoff, same frame) | Brain → LH·FSH → testes. LH and FSH tubes drain to 0, TOTAL ANDROGEN LOAD lights the brain red, OWN PRODUCTION OFF |
| 0:31 | **Bar chart** | lower card | HDL baseline 52 vs on Tren 52→18 (counts down), −65 %. HEPATIC LIPASE ↑ pulls HDL particles off the bar: CLEARS HDL |
| 0:40.5 | **Line graph + artery cross-section** | full panel | ApoB 88 → 100 → 132 with the 100+ zone shaded. Below, particles flow through an artery, plaque builds on the walls: PLAQUE BUILD-UP, LONG-TERM RISK |
| 0:50.7 | **Radial gauge + ECG** | lower card | Hematocrit dial needle settles 54 → 55 → 56 % into the red zone. EPO ↑, RED BLOOD CELLS ↑, THICKER BLOOD, then a scrolling ECG trace with HEART WORKLOAD ↑ |
| 1:02.6 | **Document (lab order)** | full panel, paper slides in | Requisition with LH / FSH / HDL / ApoB / HEMATOCRIT ticked and PROLACTIN empty: MOST GUYS SKIP. Highlighter on "prolactin" |
| 1:07.6 | **Receptor binding diagram** | full panel (handoff) | TREN docks into the progesterone receptor first (PROLACTIN ↑), then the androgen receptor: NOT JUST AR |
| 1:12 | **Curve chart** | lower card | Libido over weeks 1–12: green plateau (EVERY 10 MIN), then a red crash in the shaded LATER WEEKS: FALLS APART |
| 1:22.3 | **Route map** | full panel | A roadmap draws with pins on each word: BIOMARKERS → HOW YOU FEEL → SIDE EFFECTS → DOSAGE. Cyan cross-reference lines link them, then the verdict slam 4 INPUTS = ONE ROADMAP |
| 1:33.9 | **CTA card** | lower card | Logo, FREE · FULL BLOODWORK BIBLE, then a gold COMMENT "PANEL" bar on "comment". Disclaimer in the card |

- Placement alternates between full panels (background blurred and pushed), lower cards (face stays visible), and the on-footage HUD. Talking-head breathers sit between them (for example 0:29–0:31, 0:39.7–0:40.5, 1:01.9–1:02.5 and 1:20.9–1:22.3).
- The palette is the test-06 overlay palette (red `#FF221C`, gold `#FFC21A`, cyan `#00E5FF`, green `#1EFF6E` only for OK/checked) with bloom. The gold left rule and @coach.agz are always on screen.
- **Footage is untouched.** It's only blurred and pushed behind full panels, as in earlier tests.
- Every number on screen is spoken in the video (12 weeks, 500+, LH/FSH 0, HDL 52→18, ApoB 88/100/132, hematocrit 54/55/56, every 10 minutes). −65 % is worked out from 52→18. The libido curve is illustrative and has no y-axis values.
- Captions: every word, Bebas, with the red active-word block at y≈1335 (unchanged from the saved setup). Punch-ins alternate 100/108 % at every jump cut.

## Sound
Generated clinical SFX (`sfx.py`): sub hits on panel landings, scan sweeps, digital ticks on rows and data points, impacts on 500+, PRODUCTION OFF, the hematocrit red zone, MOST GUYS SKIP and the verdict. There's a paper slide for the lab order and a marker for the highlighter. The mix is at −14.0 LUFS integrated, with a −1.5 dBFS peak.

## Files
`render.py` (frames), `sfx.py`, `trim.json`, `words_cut.json`, `words_cap.json`, `edit_log.json`.

## QC done
- **Full decode:** 3073 frames with no errors. The final file is 56 MB, H.264 High@4.1, yuv420p, AAC 192k, `faststart`.
- **Visual review:** an overview every 1.5 s across the whole cut. Frame strips at the hook exit and at every render-chunk seam (frames 769, 1537 and 2305 are continuous). Stills at every overlay build.
- **Fixed during review:**
  - Axis tag collided with the gauges.
  - VASCULAR callout sat on the cheek.
  - Dial readout sat on the tick labels.
  - Highlighter hid PROLACTIN.
  - Roadmap labels were crossed by lines.
  - Plaque shapes were too blobby.
  - The topic band overlapped the fading hook for 5 frames; the band now enters after the hook's 0.15 s fade.
- **Loudness:** −14.0 LUFS integrated, peak −1.1 dBFS.
- **Not done:** listening to the mix (only levels were measured) and checking SFX placement by ear. The fonts are stand-ins.
