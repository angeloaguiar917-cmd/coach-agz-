# Reel 02: "Test esters: cyp vs enan vs prop" (1080p final)

**Source:** Drive `1WWdxwf7M-pWPfWLjVNBrDSjqyf0XIX_9` ("Ester hook main 1"), 1080×1920 HEVC, 60 fps, 1:36, one take in the car.
**Output:** `coach-agz_test-esters_1080p30.mp4`, 1080×1920, 30 fps, H.264 High + AAC, `+faststart` (plays and saves on iPhone/Android), −14 LUFS, true peak −1.5 dBFS.

## Cut
- Clean single take. No misspeaks found.
- 10 dead-air pauses (0.22–0.36 s) trimmed to about 0.12 s with 8 ms audio fades. Running time went from 1:36.0 to 1:34.3.
- Punch-ins alternate 100% / 108% at each cut on full-frame shots.

## Text hook (see `edit_log.json`)
- Frame 0: **CYP vs ENAN vs PROP** / stop guessing your ester. It holds until 3.4 s.
- After that a "TEST ESTERS how to pick" band runs until the midpoint, as the engine specifies.

## Overlay system: a different layout for each section
| Time | Section | Layout | What it shows |
|---|---|---|---|
| 0:03 | Three esters | **Top chips** over the cap | Three X-ray vial chips (CYP / ENAN / PROP), each drawing its own curve shape. Tag: SAME HORMONE · 3 CURVES |
| 0:09 | Cypionate | **Split screen** (face in a gold-framed window, dossier below) | #1 SCRIPTED · US stamp. **Half-life range bar 5–8 days.** Stacked mg bar: 100 mg cyp ≈ 70 mg testosterone + 30 mg ester (DEAD WEIGHT) |
| 0:21 | Flexibility | **Full takeover chart + circular face-cam** | Serum line chart over 14 days: 2×/week (amber) → 3×/week (gold) → daily (green) inside a STABLE ZONE band. Tag: LONG TAIL = FORGIVES A LATE PIN |
| 0:36 | Enanthate | **Side rail** (footage pushed right, evidence column left) | Vertical half-life ruler: **ENAN 4–5 days** next to a CYP ghost bar. Then a red-header research document with a highlighted line and a SUGGESTS · EARLY DATA tag. Then a weekday pin-dot strip: 2× → 3× → daily |
| 0:52 | Propionate | **Full takeover + square face-cam** | 90% ring counts up (OF CASES / it makes no sense). **Big stat: half-life 20–36 HRS.** Then a **half-life bar chart of all three** (CYP 5–8 days, ENAN 4–5 days, PROP 20–36 hrs) with SHORTEST bracketed |
| 1:01 | Missed day | **Top HUD monitor** over full footage | Cyan oscilloscope of daily prop pins. One pin is crossed out and the line drops into the red TROUGH zone (MISSED 1 DAY) |
| 1:09 | Same molecule | **Glass card, lower** | X-ray steroid skeleton. The ester tail cycles cyp → enan → prop, gets cut and drifts off, and the core turns green (ESTER = CARRIER, SAME MOLECULE). Hands off into a table: pins/week and missed-pin tolerance |
| 1:18 | Pick a schedule | **Selector cards** | A cursor sweeps the CYP / ENAN / PROP cards, then a gold verdict bar lands: THE ONE YOU WILL ACTUALLY KEEP |
| 1:22 | Consistency | **Top HUD streak log** | A 30-day pin log fills green, with a DAY counter and EVERY SINGLE TIME |
| 1:27 | CTA | **End card, lower** | Logo, @coach.agz, CYP / ENAN / PROP poll chips ("comment yours"), then a gold COMMENT "LABS" bar |

- **Face:** it's never covered. Graphics sit on the cap/headliner, the chest, or in their own takeover space. During takeovers the face stays on screen in a gold-framed window, circle or square cam.
- **Footage:** untouched (no grade). Vibrance comes from the overlays only: the test-06 palette with bloom.
- **Captions:** the saved style (Bebas, red lit box on the spoken word). Ester names light up gold, and TROUGH and 90% light up red. Caption position moves with each layout so it never collides with a graphic. Mis-hearings are fixed: "cell" → TEST, "Inante" → ENANTHATE, "Cipionate" → CYPIONATE.
- **SFX:** clinical only (sub hits on layout landings, scan sweeps on chart draws, ticks on rows, impacts on verdicts and stamps). Built by `sfx.py` from the shared library.

## Notes / flags
- **Prop half-life:** the spoken line says "24 to 48 hour". The on-screen value is **20–36 hrs**, as Coach AGZ supplied.
- **Serum curves are illustrative:** first-order kinetics with each ester's half-life, not patient data.
- **Mg split:** the ~70/30 split for cypionate is the standard testosterone fraction of the ester (about 70%).
- **Research document:** generic. No study is named, because the video doesn't cite one.
- **Fonts:** stand-ins (Bebas Neue, DM Sans, Barlow Condensed, JetBrains Mono).

## Files
`render.py` (frames), `sfx.py` (sound), `edit_log.json` (text hook). Source cut and words are in the session scratch (`build/timeline.json`, `build/words.json`).
