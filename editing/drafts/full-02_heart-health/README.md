# Full 02: "2 compounds every STEROID cycle needs" (Ezetimibe + Telmisartan), 1080p

**Source:** Drive `1ByY1VxgIV3k-2U3hO93SRD5RZoaCk9DR` ("2 heart health"), 1080×1920 HEVC, 60 fps, 2:26.7, one car selfie take with three in-camera cuts.
**Output:** `coach-agz_heart-health_full-02_1080p30.mp4`, 1080×1920, 30 fps, H.264 High + AAC, `+faststart` (plays and saves on a phone). The video lives on the session branch and was sent in chat; it isn't committed here because of its size.

## What changed from the earlier tests (per feedback)
- **Face stays recognisable.** The footage is never blurred or darkened behind a graphic any more. Graphics sit in the roof and side zones, or the footage shrinks into a sharp framed window that tracks the face (Haar face tracking, smoothed).
- **No repeated overlay type back to back.** There are 14 beats and 11 different overlay types:

| Time | Beat | Overlay type | Graphic |
|---|---|---|---|
| 0:00 | Text hook | Frame-0 title box (premium) | "2 compounds / every STEROID cycle needs" |
| 0:04 | "unprotected" | **Side card** (it picks the side away from the face) | Cyan heart scan, ECG trace turns red, gold shield cracks, UNPROTECTED tag |
| 0:10 | Two mechanisms | **Top HUD lanes** | 01 LIPIDS / 02 PRESSURE, both stamped UNMANAGED on "neither" |
| 0:15 | Lipid mechanism | **Split: face window top, panel below** | Liver LDL receptors dim (↓ DOWN), HDL ↓, artery cross-section with plaque growing as ApoB climbs |
| 0:25 | "lipid panel" | Same window, panel swaps | **Horizontal bar graph** against a reference band, H/L flags, then a FLAGGED ON ARRIVAL verdict bar |
| 0:32 | Fix 01 | **Top comparison table** + heavy pill slide | STATIN vs EZETIMIBE: works at liver vs gut, side-effect load |
| 0:38 | How it works | **PiP circle** (face top right, full graphic) | Gut → NPC1L1 transporter → Ezetimibe gate drops → less absorbed → liver → LDL pulled out of the blood |
| 0:49 | Bloodwork | **Side-by-side** (face left, graph right) | **Paired bar chart**, before vs on (LDL ↓, ApoB ↓, HDL ratio ↑), then the zeros: 0 hormonal interference, 0 performance impact |
| 1:00 | Problem 02 | **Chapter wipe** | Gold-edged navy wipe, giant red "02", then it hands off into a PROBLEM 02 tag that stays on screen |
| 1:06 | Resistance / BP | **Top HUD gauge** | Vessel narrows, flow speeds up, BP gauge needle climbs into red |
| 1:09 | LVH | **Split window** | LV short-axis ring wall thickens, ejection-fraction meter declines, **line chart** of LV mass rising silently over years |
| 1:21 | Fix 02 | **Title slam** | FIX 02 pill, TELMISARTAN lands in gold, ARB sub-line |
| 1:26 | Mechanism | **Drawer** (footage slides up, panel underneath) | Ang II hits the AT1 receptor, a Telmisartan block drops in, the vessel relaxes, the pressure gauge drops, wall stress ↓ |
| 1:39 | "gold standard" | **Stamp** | Rotated gold seal slams in beside the head |
| 1:44 | vs diuretics / beta blockers | **PiP rectangle + full table** | ✓/✕ grid: arterial resistance, heart rate, electrolytes, cardiac output |
| 1:52 | Clinical data | **Top line chart** | LV-mass regression curve, PREVENTION struck through, REVERSAL lands |
| 2:03 | Two problems / two solutions | **Flanking cards** (either side of the face) | Problem → solution cards merge into the "CV PROTECTION STACK" bar: EVERY CYCLE · EVERY COMPOUND |
| 2:14 | CTA | **End card** | Logo, "FREE CV PROTECTION STACK + DOSING FRAMEWORK", gold COMMENT "HEALTH" pill on "comment" |

- **Throughout:**
  - Saved caption style: Bebas, 3-word groups, a lit red box tracks the active word. Captions sit at y≈1395 to clear the chin.
  - Gold left rule.
  - Static disclaimer.
  - Punch-ins alternate at every jump cut, plus punches on "steroids", "gold standard" and "reversal".

## Cut
- 15 pauses tightened, each to about 0.12 s; 2.97 s removed in total (`trim.json`), with 8 ms audio fades.
- There were no misspeaks or retakes to remove.
- The cut was re-transcribed (Whisper medium.en) for the captions.

## Caption corrections (heard → shown)
- "a xenomide" / "Azetimibe" → EZETIMIBE
- "Telmasartan" → TELMISARTAN
- "super physiological" → SUPRAPHYSIOLOGICAL
- "injection fraction" → EJECTION
- "atrophy" → HYPERTROPHY
- "clives" → CLIMBS
- "three receptors" → AT1 RECEPTORS
- "coach Aks" → COACH AGZ
- "stacked in" → STACK AND
- One misheard echo, "vascular", was dropped.

**Please check by ear:**
- **0:19–0:22.** It transcribes as "…your liver HDL. HDL breaks down, your ApoB climbs". It may be "hepatic lipase / HL".
- **1:31.** "AT1" (heard as "three").

## Audio
- Speech is normalised, then the clinical SFX bed is added (`sfx.py`): scan sweeps, ticks, sub thuds and one impact per beat. Whooshes land on each layout change.
- Mastered to about −14 LUFS with a peak limiter. **Not listened to.**

## Not done / caveats
- The bar-graph and line-chart shapes are illustrative trends, with no lab values or study numbers on screen. The lab panel is labelled ILLUSTRATIVE.
- The fonts are Google stand-ins (Bebas Neue, Barlow Condensed, DM Sans, JetBrains Mono).
- **Topic band suppressed:** the engine's post-hook topic band was turned off because the top zone carries graphics through the whole first half.

## Rebuild
1. `cut.py` steps: make `assembled.mov` from the source.
2. Transcribe the cut to `words.json`.
3. Run `face.py` to make `face.json`.
4. Render the video: `python3 render.py <workdir> <n0> <n1> <out>`, in 4 chunks.
5. Render the sound: `python3 sfx.py <workdir>`.
6. Mux the chunks with the mix.
