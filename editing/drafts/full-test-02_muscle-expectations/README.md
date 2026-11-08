# Full test 02: "Realistic muscle gain · 3 months to 5 years" (1080p30)

**Source:** Drive `1aUEDUCnRBLFlIhipbCnbzG5clP9-KxHx` ("Muscle expect test 2"), 1080×1920 HEVC, 60 fps, 1:56.9, one clean selfie take.
**Output:** `coach-agz_muscle-expectations_full-test-02_1080p30.mp4`. It's 1080×1920 at 30 fps, H.264 High@4.2 with AAC 192k and faststart, so it plays and saves on a phone. Length 1:54.7, 80 MB, −14.3 LUFS, true peak −1.5 dBFS.
**Style:** the test-06 overlay palette. Footage isn't graded, captions show every word, the text hook comes from `TEXT_HOOK_ENGINE.md` (see `edit_log.json`), and the topic band runs until the midpoint.

## Cut
- The take had no fillers, stumbles or retakes. A filler-preserving transcription pass found none.
- 11 dead-air runs (silences of 0.25 s or more, below −40 dB) were trimmed to about 0.14 s. That's 2.2 s removed, with frame-aligned cuts and 8 ms audio fades.
- Punch-in alternates (100% / 108%) at every jump cut. Two extra punch-ins land on "suboptimal" and "die in 10 years".

## Overlay variety (the brief: graphs, more graphics, no repeated overlay type)
Six layout types rotate, so the frame keeps changing shape: side rail, full panel, split screen, top shelf, scope grid and picture-in-picture, plus the end card.

| Time | Layout | Graphic type |
|---|---|---|
| 0:00 | hook | Frame-0 text hook "Realistic **MUSCLE** gain / 3 months to 5 years" |
| 0:02 | side rail | Rolling digital readout (LEAN MASS Δ +?? LB). It expands into an **assumptions spec sheet**: untrained, average genetics, locked in, each ticked as it's spoken |
| 0:12 | full panel | **Range-bar chart**: 3 MO 3–8, 6 MO 5–12, 1 YR 10–20 lb, with a trend line through the midpoints and an empty 5 YR slot "?" |
| 0:26 | split screen | **Stack build** (training → nutrition → protocols → side-fx mitigation) feeding a **5-year growth curve** with a range band. 20–40 LB slams in on "20 to 40" |
| 0:41 | full panel | **Bell curve** of genetic response. The 240 LB / 1% of 1% / +40 LB cycle-1 tail is lit red, the average male is shaded gold as the benchmark, then an OUTLIER stamp |
| 0:57 | top shelf | **Gantt strip** of 10 years of ON/OFF cycles, plus a **spectrum meter** (physique result) landing on NOT OPTIMAL then SOLID |
| 1:06 | scope grid | **Line chart**: dashed "expected" straight line vs the real curve with plateaus, then a NON-LINEAR flag |
| 1:10 | top shelf | **ECG trace** with BLOODWORK MONITORED ✓, and a **segmented cardiovascular-risk meter** that dips on "magically", then snaps back up: NOT ELIMINATED, LONG-TERM |
| 1:22 | full panel | **Expectation vs reality bars**: client goal 20–30 lb vs the 6-month reality of 5–12 lb, with a GAP bracket |
| 1:27 | picture-in-picture | Footage shrinks into a LIVE window. **Time-on-gear bars** (DAY 90 vs YEAR 5) and a **forensic feed post** ("@someone_else", brackets on 5 YRS IN, LIGHTING, PUMP) |
| 1:31 | picture-in-picture | **Speedometer** (gain rate) redlines on "as fast as possible", then the verdict bar FASTEST ≠ THE GOAL |
| 1:35 | top shelf | **Built vs kept bars** and a **long-term health battery** that drains and cracks on "disposable" |
| 1:41 | full panel | **Lifespan timeline**: YOU cut short at +10 years and hatched out, YOUR KIDS row with NO FATHER, then an RGB glitch hit on "destroy everything" |
| 1:48 | end card | Logo, FREE · MUSCLE GROWTH TRACKING FRAMEWORK, a tracker-sheet preview and a gold COMMENT "GROWTH" pill on "comment" |

## Sound
These are synthesised clinical SFX (`sfx.py`): sub thuds on panel entries, scan sweeps on chart draws, digital ticks on rows, needle risers on the gauges, and impacts on the 5-year slam, OUTLIER, the speed verdict and NON-LINEAR. There's also one glitch burst. Each sound is placed on the frame where its graphic lands. Speech is loudness-normalised to −14 LUFS.

## QC done
- An overview frame every 1.5 s across the whole render.
- Frame strips at 30 fps around the split-screen entry, the expectation panel in/out, the PIP exit and the glitch.
- Fixed during the build:
  - The CTA pill collided with the captions.
  - Bar glow washed out the bars.
  - Split-screen text was too small.
  - The bell-curve tail fill was invisible, and its tags overlapped.
  - Tags overlapped on the physique meter.
  - The expectation panel sat empty for 6 s (it now enters on "new client").
  - The battery card overlapped the PIP exit.
- Captions are built from a transcript of the edited cut.
  - "fucking" is shown as F*CKING.
  - "we're" was corrected.
  - The unclear 0.2 s lead-in before "stop comparing" ("you have to" or "just") is left out of the captions, and the caption starts on STOP.
- **Not done:** listening. I can't play audio here, so check the SFX balance and the trims by ear.

## Caveats
- The ON/OFF pattern on the 10-year strip, the "expected" vs real curve shape, the 12% battery and the tracker-sheet rows are illustrative, not data.
- The chart numbers (3–8, 5–12, 10–20, 20–40, 20–30) are exactly what's spoken.
- The fonts are stand-ins: Bebas Neue, Barlow Condensed, DM Sans and JetBrains Mono.

## Rebuild
1. `cut` from `trim.json`.
2. `python3 render.py <scratch> chunk n0 n1 out.mp4` in 4 to 6 chunks.
3. `python3 sfx.py sfx.wav`, then mix with the loudnorm'd voice and loudnorm the mix to −14 LUFS / −1.5 dBTP.
4. Concat and encode the H.264 High CRF 19 with faststart.
