# Full test 02: "Winstrol destroys biomarkers" (1080p30)

**Source:** Drive `1jPhbNzfBY9LM6Uhxq8kUzgVAgcAEMltE` ("Winstrol destroys biomarkers", 1080×1920 HEVC, 60 fps, 1:46, car selfie).
**Output:** `coach-agz_winstrol-biomarkers_1080p30.mp4` — 1080×1920, 30 fps, **1:43.3**, −14.7 LUFS, true peak −1.5 dBFS, H.264 high@4.0 + faststart (phone-downloadable). ~93 MB, delivered to Coach AGZ directly; not committed (binary, see examples/README convention).

This is a **final-spec** edit (1080p, test-06 vibrant-overlay style) and the first in this niche. Footage left as shot; all vibrance is in the overlays.

## What Coach AGZ asked for (this edit)
- Use saved setup + style, **keep 1080p**, make it **downloadable to phone** → done (faststart, 93 MB H.264).
- **Different overlay types, with variety — don't repeat one overlay type** → 7 distinct graphic archetypes (below).
- More graphics, vibrant, on-brand, eye-catching → test-06 accent palette (`#FF221C`/`#FFC21A`/`#00E5FF`/`#1EFF6E`), bloom on edges/bars.
- **Keep the face recognizable** → every graphic lives in a stage **below y≈1050** (the face band is 430–1050); the face is never covered. Captions sit on the upper chest, clear of the face.
- **No frame-0 text hook**, but a **visual hook is allowed** → the opening uses a diagnostic HUD (HDL/LIVER/LIPIDS chips) + a cyan scan-reticle sweep instead of a title card.

## Graphics (one type per beat, for variety)
| Beat | Overlay type |
|---|---|
| 0:00–0:05 | HUD diagnostic chips + scan reticle (**visual hook**, no text headline) |
| 0:21 HDL | **Line-crash chart** — HDL plummets 58 → 21 mg/dL into a red zone |
| 0:32 mechanism | **Molecule schematic** — steroid rings with the C-17 methyl highlighted, "17AA ORAL" |
| 0:40 liver | **Organ load polygon** (fills red) + **ALT/AST vertical bars** rising into HIGH flags |
| 0:54 panel | **Lab-report table** — HDL/ALT/AST/TG flagged, "NOT ORDERED" |
| 1:06 damage | **Radial ring gauge** — organ-damage %, "MEASURABLE & SILENT" |
| 1:26 roadmap | **Chevron flow** — ANALYZE → PIVOT → OPTIMIZE |
| 1:39 CTA | Branded **end card** — logo + `COMMENT "WIN"` gold pill |

Persistent `WINSTROL · BIOMARKERS` topic band top-left (brand anchor), gold edge rule, `@coach.agz` watermark + research/education disclaimer throughout.

## Pipeline (rebuild)
1. `cut.py` / `cut2.py` — silence detection → `trim.json`, assemble tightened cut (`assembled_v.mp4` + `cut_a.wav`). 19 dead-air trims removed (~3.3 s); no misspeaks of substance. `srcmap.json` maps each output frame → source 30fps frame.
2. Face track (MediaPipe selfie-segmenter + BlazeFace) → `faceband.json` (per-frame face box; used to place graphics clear of the face). Raw masks (414 MB) not committed.
3. `words_cut.json` — Whisper medium.en word timings of the tightened cut (362 words). Corrections: alkalated→alkylated, antibiotics→anabolics, bloodworks→bloodwork, Ag's→AGZ.
4. `render_win.py` — all graphics/captions/HUD/CTA + bloom. `python3 render_win.py render <n0> <n1> out.mp4` (chunked), or `... stills <t> <t> ...` for QC.
5. `audio.py` — restrained clinical SFX bed (sub-hits on scene entries, ticks on data rows, one CTA impact, hook sweep) → 2-pass `loudnorm` to −14 LUFS.

## QC done
- Face-track confirmed graphics never cross the face band; stills checked at every scene entry + transitions.
- Captions rebuilt from the tightened-cut transcript; accent words recolour on the spoken word.
- Rendered-file frames inspected across all scenes.

## Not done / flags
- **Not listened to.** SFX were placed blind — please check the mix by ear.
- All lab/graph numbers are **illustrative placeholders**, not a real panel.
- Fonts are free stand-ins (Bebas Neue, DM Sans, Barlow Condensed, JetBrains Mono).
- Per request, no frame-0 text hook; `editing/TEXT_HOOK_ENGINE.md` candidates were computed and logged in `edit_log.json` but not rendered.
