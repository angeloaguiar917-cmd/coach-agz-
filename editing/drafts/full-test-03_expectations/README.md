# Full test 03: "Expectations" (genetics, realistic gains). 1080p

**Source:** Drive `15uM-_MdRgpZKZok2WGRU5UMygwoa8f3N` ("Expectations 3"), 1080×1920 HEVC, 60 fps, 2:05, one clean selfie take.
**Output:** `coach-agz_expectations_full-test-03_1080p30.mp4`, 1080×1920, 30 fps, H.264 High + AAC, `+faststart` so it plays and saves straight to a phone. Length 2:01 (2:00 of speech plus a 1 s end-card hold).
**Brief:** use the saved setup (test-06 overlay palette, footage untouched, every-word captions, text hook engine) and give it **more varied overlay types**: graphs, more graphics, vibrant, on brand.

## Cut
- There were no retakes or misspeaks. A filler-preserving medium.en pass found none.
- Dead air: 20 silent runs of 0.22 s or more were trimmed to about 0.12 s, frame-aligned, with 8 ms audio fades. That removed 5.2 s in total (`trim.json` lives in scratch).
- Punch-ins alternate between 100% and 108% at every jump cut.

## Text hook (see `edit_log.json`)
- **Hook:** `Expecting 20 to 30 lbs / in 6 months on STEROIDS`, native mode (DM Sans Bold), with STEROIDS in v-gold.
  - Visible on frame 0 and holds until 6.0 s, with a slow 100→104% scale.
- **Topic band:** "Real expectations on STEROIDS" shows from 6 s until the midpoint (60 s). After that, the top of the frame stays clear.

## Overlays: 12 moments, 11 different types
| Time | Type | What it shows |
|---|---|---|
| 0:06 | **Line chart → timeline zoom** | The client's ask: a red line to 20–30 lb in 6 months. On "stop comparing" the axis zooms out from months to 5 years. The line becomes a near-vertical spike ("TOO STEEP"). Your first 90 days is a cyan sliver; their year 5 is gold. "90 DAYS vs 1,825 DAYS" counts up. |
| 0:15 | **Speed gauge** | A "rate of gain" gauge shakes in the redline under "AS FAST AS POSSIBLE", then gets ✕ "NOT THE GOAL". On "building" the needle drops into the gold zone: "MUSCLE WORTH KEEPING", ✓ SUSTAINABLE. |
| 0:19 | **ECG monitor** (top strip, face stays visible) | Green trace at 72 BPM. On "disposable" it turns red and erratic, then flatlines on "die": "10 YRS", FLATLINE, NO FATHER. |
| 0:32 | **CTA card** (lower) | Logo plus "FREE · MUSCLE GROWTH TRACKING FRAMEWORK", then a gold `COMMENT "GROWTH"` pill on "comment". |
| 0:38 | **Quadrant map** | A GENETIC CEILING line draws on. Then a response × tolerance map: HYPER-RESPONDER, HYPER-TOLERATOR, and BOTH (gold, pulsing). |
| 0:46 | **Bell curve** (handoff) | The gold "BOTH" dot flies into the far tail of a population curve: "1 PHIL HEATH", "1 RONNIE COLEMAN", with MOST LIFTERS in the middle. |
| 0:55 | **Document / evidence** | A client progress file: weekly dose circled LOW in red pen, the lean-mass trend inks upward, HYPER-RESPONDER, and an "OUTLIER" stamp slams on "insane". |
| 1:09 | **Checklist + meter** (top strip) | My inputs tick in as spoken: training, nutrition, recovery, sleep, bloodwork, every day. The effort meter fills to 100%. |
| 1:19 | **Grouped bar chart** | Them vs me at 6 MO, 1 YR, 3 YR and 5 YR. The bars grow on each spoken time point. A big cyan "¼ OF THEIR GAINS" lands. |
| 1:33 | **Amplifier stack** | Elite genetics shoots up ("THAT ONE GUY"). For average genetics ("YOU"), gear adds only up to its ceiling. The ceilings flash red, then a verdict bar slams: "GENETICS = YOUR CEILING". |
| 1:47 | **Waffle chart (100 dots)** | "100 guys on gear": the dots fill red as the count reaches 80, then the label settles to "80–85%". The remaining 15–20 light gold. |
| 1:54 | **Progress line + end card** (top strip + lower card) | "YOU vs YOU": a rising green line to a gold "BEST VERSION", EVERY SINGLE DAY. The end card has the `COMMENT "GROWTH"` pill, the handle and the disclaimer, then holds for 1 s. |

Full panels alternate with top strips and cards, so the face stays on screen regularly. 1:29–1:33 ("set the right expectations") and 1:53–1:54 are plain talking head.

## Sound
- Clinical SFX only: sub thuds on panel landings, scan sweeps on strips and builds, and digital ticks on rows. An ECG beep runs, then a flatline tone. Impacts land on "as fast as possible", "insane" and the verdict.
- Speech is loudness-normalised to about −14 LUFS.

## QC
See the final report in chat. All chart values are **illustrative**, except the figures you say on camera: 20–30 lb, 6 months, 90 days, 5 years (1,825 days), ¼, 80–85%. The fonts are stand-ins (Bebas Neue, DM Sans, JetBrains Mono, Barlow Condensed).

## Rebuild
`render.py <scratch> chunk n0 n1 out.mp4` renders frames from `ex/cut.mov`. `sfx.py <scratch>` writes `ex/sfx.wav`. Both read `ex/trim.json` and `ex/words_final.json` (also copied here).

## QC done
- **Format:** 1080×1920, 30 fps, H.264 High@4.2, yuv420p, AAC 192k, faststart. 62.7 MB, 3,630 frames, 2:01.
- **Audio:** −14.5 LUFS integrated, true peak −1.1 dBFS.
- **Visuals:**
  - Checked stills of every scene, a contact sheet every 2 s, and 10–30 fps frame strips at the hook exit, the gauge→ECG handoff and the verdict slam.
- **Fixed during review:**
  - Tags clipped at the panel edge, and label collisions on the zoomed timeline.
  - "NO FATHER" was white on white.
  - "HYPER-RESPONDER" collided with the panel header, and the OUTLIER stamp covered the dose field.
  - Top strips moved up off the eyes.
  - The gauge panel overlapped the ECG strip entrance.
  - The hook box hard-cut instead of fading and overlapped the topic band for 2 frames.
  - A divide-by-zero on the first frame of the ceiling draw-on.
- **Captions:** built from the medium.en transcript of the cut audio, with fixes for "anabolic", "gonna", "I have a" (from a focused re-check) and "85%".
- **Not done:** listening. Check the SFX balance and the "will only optimize" caption by ear.
