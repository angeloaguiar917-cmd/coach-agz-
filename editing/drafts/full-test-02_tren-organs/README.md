# Full test 02: "Tren without shitting out your organs" (1080p)

**Source:** Drive `1UJUl_XO_OzRxbm2n9F2-EpZUIcHlY2jt` (1080×1920 HEVC SDR bt709, 60 fps, 1:48, seated selfie, one clean take).
**Outputs:**
- `coach-agz_tren-organs_1080p.mp4`: 1080×1920, 30 fps, H.264 High, yuv420p, AAC 48 kHz, faststart. This is the phone and Instagram upload file.
- The master (CRF 12, about 250 MB) was rendered in the session scratchpad and isn't committed.

**Status:** full-length test of a new layout ("face-first"). It isn't an approved Signature Style.

## Brief (Coach AGZ, 2026-11-11)
- Use the saved setup and style, export 1080p, and make it downloadable to a phone.
- Use different overlay types; don't repeat one type over and over like the earlier tests.
- Give the speaker enough face time to be recognised.
- Use graphs and more graphics: vibrant, on brand, eye-catching.

## How the brief was met
- **Face time.** The face sits at roughly y 440–1020 in this footage, measured with a face tracker every 0.25 s. All graphics live in the lower band (y ≈ 1130–1580), along the left edge (the 01/02/03 rail) or above the cap (hook and topic band).
  - The face is never covered and never blurred. Unlike full test 01, there is no full-frame blur or push.
  - Captions lift from y 1335 to y ≈ 1042 while a lower graphic is up, then glide back.
- **Variety.** 17 overlay moments, and each one is a different type. No type repeats back to back.
- **Graphs.** Diminishing-returns line chart, live BP chart, ECG trace, bell curve, draining vitals meters, tolerance bars and the equation counter. Every curve without real data is labelled ILLUSTRATIVE, and no lab values are invented.
- **Brand.** Uses the test-06 overlay palette (v-gold, v-red, cyan, green on near-black frosted panels) with bloom. The carousel navy and gold look appears on the bell curve and the protocol doc. The gold edge rule, the @coach.agz handle and the disclaimer are on screen. The footage is not graded.

## Cut
`cut.json` holds the 13 keep ranges in source seconds; the cut runs 104.77 s, plus a 0.5 s end-card hold, for 1:45.3 in total.
- The head trim removes "Alright fellas, well…", so the video opens on "If you want extraordinary results with trenbolone…".
- The tail trim removes "Appreciate you guys" and ends on "…send it out to you guys."
- Every silence of 0.22 s or more is trimmed to 0.12 s: 12 frame-aligned joins with 8 ms audio crossfades, removing 3.65 s in total.
- No stumbles. A filler-preserving medium.en pass and a focused re-check of 0:30–0:35 found none.

## Overlay map (output time)
| Time | Type | What it shows |
|---|---|---|
| 0:00 | Frame-0 text hook | "3 TREN rules / before your organs pay" (see `edit_log.json`) |
| 0:05 | Progress rail grown from the gold edge rule | 01 DOSE · 02 CARDIO · 03 SIDES. 03 pulses red with MISTAKE on "massive mistake", and each point lights up when he says its number |
| 0:05–0:52 | Topic band | "TREN without the organ damage"; exits on the jump cut nearest the midpoint |
| 0:13 | Receptor scan → line graph (HUD panel) | The TREN steroid skeleton docks into the androgen receptor (binding strength HIGH). More molecules arrive and bounce off (SATURATED). The panel then turns into an expected-vs-actual dose/muscle graph tagged DIMINISHING RETURNS |
| 0:20 | Free-floating vitals meters | Recovery, appetite, sleep and mood drain to red on each word, then SYSTEM CRASHING |
| 0:28 | Brand tag pill slam | NON-NEGOTIABLE 02 · cardiovascular |
| 0:29 | Paper lab requisition | Blood pressure, ApoB, lipids, hematocrit and cardiac function are ticked on each word; a REQUIRED stamp lands on "overall" |
| 0:36 | Face-only beat | Punch-in on "Greek fucking god" |
| 0:37 | Artery scope + ECG monitor | Plaque narrows the vessel (NOT GUARANTEED). The ECG goes erratic on "explode", with a red edge flash and CARDIAC EVENT RISK |
| 0:42 | Object stack | Five support bottles drop in, a scan sweeps them, MASKS SYMPTOMS appears, and a strike lands on "Bro" |
| 0:44 | Symptom monitor (cyan HUD) | Sleep ring counts 8 → 2 HRS, a NIGHT SWEATS chip appears, and a live BP chart rises into the red zone |
| 0:49 | Dose fader | The knob slides HIGH → MODERATE on "dropping", then MICRO on "microdosing" (MICRODOSE · RECOMMENDED) |
| 0:55 | Alert toasts | "From your body" notifications stack up, then ACTION REQUIRED |
| 1:01 | Decision fork | Smartest move: DROP THE DOSE or DROP THE COMPOUND; each card is selected on its word |
| 1:06 | Case files A vs B | Tolerance 90% (green chips) vs 8% (PSYCHOSIS SX, PARANOIA) |
| 1:16 | Signal amplifier | Input "you" → TREN amp → output grows, then clips red on "massive extent" |
| 1:21 | Bell curve (carousel navy look) | Can't / most guys (MICRODOSE → OK) / handle it |
| 1:26 | Equation | RESULTS MAX × HEALTH 100% → 0% = OUTCOME 0 |
| 1:33 | Protocol doc (carousel look) | TREN FRAMEWORK · MICRODOSE PROTOCOL, USED WITH CLIENTS stamp, rows on the spoken words. It collapses into the CTA (handoff) |
| 1:42 | CTA end card | Gold COMMENT "TREN" pill, a comment field that types TREN and sends on "below", the handle and the disclaimer |

**Camera:** punch-ins alternate at every jump cut, plus emphasis punches on "trenbolone" (hook), "Number two", "Greek", "Why", "But at the end of the day" and "regardless". All are anchored on the face. Nothing moves while a graphic builds.

**Sound:** clinical SFX from `sfx.py` (sub hits, scan sweeps, ticks, monitor beeps, one impact per beat: non-negotiable, explode, action required, outcome 0, comment). Two-frame shake on those five landings. Mix: −14.2 LUFS, peak −1.7 dBFS.

## Files
- `render.py`: frame renderer (`stills` mode for QC, `chunk` mode for the encode).
- `sfx.py`: SFX bed.
- `cut.json`: keep ranges.
- `words_final.json`: caption words, from a chunked medium.en transcript of the cut audio. Fixes: "angioreceptor" → androgen receptor, "tremble own" → trenbolone, the dropped "entirely", and a hallucinated "thanks for watching" removed.
- `edit_log.json`: text hook engine output.

## QC (done on the rendered 1080p file)
- **Cut:** the final audio was re-transcribed. All 360 caption words are present. The rest of the diff is spelling variants only (Tren/"trend", ApoB/"apo b").
  - One real error was caught and fixed. The first cut treated source 67.30–68.55 as a breath, but it held the word "entirely" (confirmed with medium.en on that window). It's now restored, with normal 0.12 s pause trims.
- **Caption sync:** median drift 0.03 s, p95 0.11 s.
  - Every word over 0.2 s off was checked against speech energy.
  - "And" at 1:10 was moved 0.24 s earlier.
  - The others ("feel", "paranoia", "But", "extraordinary") were ASR timing errors; the captions match the energy onsets and a medium.en re-check.
- **Visuals:**
  - Overview every 2 s; stills at every scene; frame-by-frame strips at the hook exit, explode, ACTION REQUIRED, outcome 0 and doc→CTA.
  - Fixed during build:
    - Graph label collisions.
    - Paper moiré.
    - The split "-NEGOTIABLE" caption.
    - Alert header colliding with the captions.
    - The fork's "OR" sitting on a card edge.
    - The topic band overlapping the fading hook (it now enters 0.12 s after the hook starts to fade).
    - The CTA pill landing on the full-size doc (the doc now collapses first, and the pill, its impact and its shake land 0.14 s later).
- **Sound sync:** the five impacts (non-negotiable, explode, action required, outcome 0, comment) start within 0 ms of their target frames. The mix measures −14.2 LUFS with a −1.7 dBFS peak.
- **Not done:** listening. The SFX balance, the 8 ms crossfades and the restored "entirely" join have to be checked by ear. Fonts are stand-ins (Bebas Neue, DM Sans, Barlow Condensed, JetBrains Mono). Graph shapes are illustrative, and no lab values are shown.
