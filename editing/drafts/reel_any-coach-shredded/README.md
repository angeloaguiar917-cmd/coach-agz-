# Reel: "Any coach can get you shredded" (1080p final candidate)

**Source:** Drive `1qVTGq3vbVPceTNdSvcew8DZl4zGR9E1p` ("Coach anyone can get it done"), 1080×1920 HEVC, 30 fps, 2:00.7. A single car take.
**Output:** `coach-agz_any-coach-shredded_1080p.mp4`: 1080×1920, 30 fps, H.264 High with faststart (plays and saves on a phone), AAC 48 kHz, 1:58.0, −14.3 LUFS, −1.5 dBTP.

## Direction for this edit (Coach AGZ, 2026-11-17)
- No text hook at the start. No frame-0 hook and no topic band, so the engine was skipped (see `edit_log.json`).
- Overlays vary in type. No layout repeats back to back.
- The face stays recognisable: no full-frame blur or push behind any graphic. Graphics sit in the dark headliner band, on a side rail over the seat, in split-screen with the full face kept on top, or in a picture-in-picture window.
- Graphs, more graphics, and vibrant colour from the test-06 overlay palette. The footage itself is ungraded.

## Cut
- Eight dead-air trims, 2.7 s in total, each with an 8 ms crossfade.
- A deliberate 0.27 s beat is kept before "Shredded isn't the goal."
- There were no stumbles. The medium model heard a repeated "insane" at 1:21, but a focused re-transcription showed it was a model artifact.
- The punch-in alternates 100% / 108% at every jump cut.

## Graphics (raw source time → layout → type)
| Time | Layout | Overlay type |
|---|---|---|
| 0:02–0:16 | Top band | **The stack.** Line-art vials and pens drop in on each word: Tren 300 mg, Test 500 mg, Masteron, Reta, GLP-1, peptides. Then LOOKS: INCREDIBLE and a SHORT-TERM tag. Research disclaimer. |
| 0:16–0:22 | Left side rail | **Line graph.** Body fat drops steeply over weeks, then SHREDDED, then THE GOAL? |
| 0:22–0:31 | Split screen | **Two-line timeline chart.** PHYSIQUE holds, then falls off a cliff at OFF. The HEALTH line is dashed, with a "?" landing at 1 YR, 2 YRS and "health phase". OFF RETA / OFF COMPOUNDS tags. |
| 0:31–0:37 | Top band (cyan) | **DM inbox.** Message requests slide in and the unread badge counts to 99+. Brackets land on "dose" and "protocol". |
| 0:37–1:00 | Picture-in-picture | **Client file and lab report.** Footage shrinks into a live window. YOUR BLOODWORK: NOT ON FILE. Each marker he names (estradiol, prolactin, eGFR, ALT/AST, HDL, side-effect, compound and positive response) gets ?? NO DATA. Verdict bar: NO BLOODWORK = NO PROTOCOL. |
| 1:00–1:09 | Top band (green) | **Bar chart.** Weekly panels W1–W8 converge into the target range, which turns green on "optimization": OPTIMIZED FIRST. |
| 1:09–1:18 | Left side rail | **Pillar blocks.** 01 Sustainability, 02 Consistency, 03 Education slide in heavy. Then a YOU UNDERSTAND IT check and a "decades" ruler. |
| 1:19–1:32 | Top band (red) | **Meters.** LOOKS fills to 100%, a 5:00 PM clock appears, and the ENERGY battery drains to 7% FRIED. ✕ KIDS / ✕ WIFE. |
| 1:32–1:34 | Top band | **Stamp.** SHREDDED is struck through: ≠ THE GOAL (impact). |
| 1:34–1:40 | Top band (green) | **Radial gauge.** Sweeps to 100%: HORMONALLY OPTIMIZED, THE GOAL. |
| 1:40–1:55 | Split screen | **Staircase roadmap.** 01 Bloodwork → 05 Frameworks, with a stepped "low + slow" titration line drawn in step 03. FOR LIFE. |
| 1:55–end | Top band | **CTA card.** Logo, FREE · FULL PROTOCOL BREAKDOWN, and a gold COMMENT "LABS" landing on "comment". |

Captions are every-word Bebas with a red lit-block highlight. They sit below the chin (y ≈ 1528) and move into the split panel during split-screen. Brand words recolour gold, green or red. The gold left rule and a vertical @coach.agz handle stay throughout.

## QC
- Stills reviewed at 35 timestamps across every scene in and out, at both punch-in levels.
- The full render was checked frame by frame (see below).
- Audio is speech plus synthesized clinical SFX (thuds, ticks, scan sweeps and two impacts), placed on the landing times. Loudness was measured; I didn't listen to it.
- The chart shapes are illustrative depictions; no values are claimed. The fonts are stand-ins (Bebas Neue, JetBrains Mono, DM Sans, Barlow Condensed).

## Rebuild
Fonts go in `../fonts/`, and `raw.mov` in `../src/` relative to the work folder.
1. Run `python3 render.py <n0> <n1> chunk.mp4` in 4 chunks over 3540 frames.
2. Run `python3 audio.py`, then loudnorm to −14 LUFS.
3. Concat the chunks and mux, with final encode `-crf 20 -maxrate 6M -preset slow -profile:v high -movflags +faststart`.
