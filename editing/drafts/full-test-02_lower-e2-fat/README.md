# Full test 02: "Two things to lower E2 (fat)": 1080p30 final

**Source:** Drive `18ikiGLLdKcgUpHlMFxvWy6a0pWSBAKrn`. 1080×1920 HEVC, 60 fps, SDR, 1:22. Pre-assembled from 8 takes: 5 outdoor, then the car from 0:31.
**Output:** `coach-agz_lower-e2-fat_1080p30.mp4`.
- 1080×1920, 30 fps, 1:20.4.
- H.264 High 4.2, yuv420p, AAC 192k, faststart (plays and saves on a phone).
- 50 MB, −14.0 LUFS, true peak −3.3 dBTP.

## Cut
`trim.json` (source timeline).
- Removed the stumble "And it's very quite simple" (44.70→45.87, lands on the existing take change).
- Tightened three pauses (35.63, 53.43, 69.63) to about 0.1 s, with 8 ms audio crossfades.
- The cut was re-transcribed (`words_cut.json`, medium.en) and captions were built from it.

## Text hook (`edit_log.json`)
- **Hook:** "High **ESTROGEN** / fix this before an AI" (native mode, frame 0 to 3.6 s). It exits on the jump cut, and the text scales 100→104% over the hold.
- **Topic band:** "High ESTROGEN the real fix", from 3.6 s to the jump cut at 38.42 s (nearest to the midpoint).

## Captions
- **Position:** they sit low (y≈1398) on the outdoor shots. From 31.45 s they sit at the top (y≈392), over the dark car roof, because his mouth sits at y≈1400 in the car framing.
- **Censoring:** F*CKING, SH*T. Nolvodex is spelled NOLVADEX.

## Overlays: a different type per beat (the brief asked for variety)
| Time | Type | Depicts |
|---|---|---|
| 0:04 | Live line graph | E2 climbs from the reference range after "cycle start", then breaks out of the chart frame (OUT OF RANGE) |
| 0:08 | Scan inset + live detection brackets | Cyan chest X-ray with tender/swollen markers, then red brackets and a scan line over the face (bloat) |
| 0:12 | Prescription labels + stamp | Tamoxifen (SERM) and anastrozole (AI) Rx labels, then a "TREATS THE SYMPTOM" stamp on "wrong" |
| 0:16 | Document: receipt | A drive-thru receipt prints item by item, then a SURPLUS stamp and BODY FAT ↑ |
| 0:21 | Picture-in-picture + mechanism | The speaker shrinks into a gold-ringed circle; fat cells are relabelled from STORAGE to ENDOCRINE ORGAN, aromatase multiplies, T flows in and E2 flows out |
| 0:31 | Kinetic stat + meter | 400 counts up, then a body silhouette fills with fat and a HIGH meter appears |
| 0:35 | Gauge | The aromatase output needle sweeps to MAX, and a factory icon vents E2 |
| 0:38 | Dual-curve graph | The gains curve plateaus while the estrogen curve keeps climbing; the wasted-dose area is hatched |
| 0:43 | Full-screen title wipe | A gold rule wipes in "FIX THE SOURCE / Not the symptom" (callback to the stamp) |
| 0:44 | Numbered step cards | 01 cut body fat (bar drops), 02 lean first (lock opens), 03 lower the dose (bar drops) |
| 0:54 | Range slider + chips | The dose marker slides from 400 into the green 100–150 mg window; then nutrition, steps, cardio and eat-right chips tick |
| 1:00 | Grouped bar chart | High body fat vs lean on the SAME DOSE: aromatase drops and E2 spikes vs stays in range |
| 1:08 | Route map + foundation slab | A bloodwork route draws with lab pins, then the BODY COMPOSITION slab drops and lands heavy |
| 1:13 | Comment-box CTA | Logo, a free framework + protocol offer, ESTROGEN typed into a comment field, a gold COMMENT "ESTROGEN" pill, and the disclaimer |

The overlays use the test-06 palette. The footage is ungraded. Bloom applies only to lines and edges.

## Sound (`sfx.py`)
- Clinical palette: sub hits on panel entries, scan sweeps, quiet ticks, a needle riser, and impacts.
- Impacts land on the breach (0:07.5), the stamp (0:15.6), the gauge (0:37.8) and the slab (1:10.5).
- Every sound is placed on its visual landing frame.

## QC done
- Stills of every scene, frame strips at every transition, and an overview every 2.5 s.
- **Fixed during review:**
  - The stamp collided with the Rx label, and its bloom washed out the lettering.
  - Two labels collided: GAINS with ESTROGEN, and SPIKE with the column header.
  - Raw footage flashed before the title wipe.
  - An empty panel frame appeared on the gauge swap.
- **Captions:** the final audio was re-transcribed. All 287 words match, apart from spelling variants. Drift median 0.04 s, p95 0.14 s.
- **Not done:** listening (levels only).

## Illustrative values
- The receipt kcal figures, the curve shapes and the bar heights are illustrative, not data.
- 400 mg and 100–150 mg are from the transcript. The fonts are stand-ins.
