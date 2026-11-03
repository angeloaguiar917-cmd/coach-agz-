# Reel: "300MG" — more mg ≠ more growth (720p30 preview)

**Status:** first full edit, for review. Not a final export; a final would be 1080×1920.
**Source:** Drive file `1uJ3wifiSC4hTLqK3gWZWkCrRnoeIcypD` ("300MG"). 1080×1920 HEVC, 60 fps, 2:00. Single indoor take with no retakes.
**Output:** `coach-agz_300mg_720p30.mp4`. 720×1280, 30 fps, H.264 + AAC, 1:59.0 (117.8 s of speech plus a 1.3 s end-card hold). −14.3 LUFS, peaks −1.4 dBFS.

## Saved setup applied
**Look (test 06):**
- Every-word captions with the red active-word block.
- Clinical evidence panels that open out of the gold edge rule.
- High-pop overlay palette and bloom.
- Lit red verdict bars with a 2-frame shake.
- Cyan scan wipes.
- Footage ungraded.

**Workflow (full test 02):**
- **Transcription:** a vocabulary-prompted pass plus a filler-preserving pass, run with both the small and medium models.
- **Paper edit:** misspeaks cut and dead air tightened.
- **Punch-ins:** 108% alternating at every jump cut.
- **Captions:** rebuilt from a transcript of the trimmed audio.

## Paper edit (`trim.py`, `trim.json`)
**One take, so no take selection.**

**Misspeak cut:** "and prepare **for** yourself for those complications" → "and prepare yourself for those complications".
- Source 95.87–96.00 s, cut on frame boundaries at the speech-energy dips.
- The splice was verified by re-transcribing the cut.

**Dead air:**
- Every silent run of 0.22 s or more (−32 dB, which is 10 dB under the speech RMS) is trimmed to about 0.12 s.
- That's 13 trims, frame-aligned, with 8 ms audio fades at each join.
- 2.3 s removed in total.
- The delivery is dense, so most pauses are already under 0.22 s.

**Ending:** the last frame is held 1.3 s so the end card can be read.

**Light stabilisation:** vidstab, smoothing 20.

## Framing change
The face sits lower in this clip: the chin is at about y 1400–1500 (1080 space). The saved caption line (y 1335) would cover the mouth, so captions sit at **y ≈ 1505**, max 116 px. That puts them on the hoodie, clear of the Instagram bottom UI.

## Timeline (trimmed timeline)
| Time | Speech | On screen |
|---|---|---|
| 0.0–5.9 | "If you aren't growing on 300mg… rushing to 500 and 600mg a week?" | **Hook title card.** A gold kicker types "TESTOSTERONE · WEEKLY DOSE". A big gold **300** MG / WEEK lands on "300", then snaps to red **500** and **600** as each is spoken. **MORE MG ≠ MORE GROWTH** lands, with ≠ in red. |
| 5.9 | | **Handoff:** the headline travels into the **pinned title** bar, on the first jump cut. |
| 6.2–12.9 | plateau → increase the dose → impatience | **CASE 01 · PLATEAU RESPONSE.** A lean-mass curve draws and flattens, flagged PLATEAU. A dose lane holds 300, then steps to 500/600 in red on "increase the dose". The curve continues dashed and flat, labelled "CAUSE NOT ADDRESSED". Red verdict **IMPATIENCE · NOT OPTIMIZATION**, with impact and shake. |
| 16.9 | step one: training, nutrition, overload, calories, protein, recovery; gear amplifies, doesn't replace | **STEP 01 · FOUNDATION:**<br>• TRAINING / NUTRITION chips, then four base tiles land on each word.<br>• An OUTPUT bar grows with the base, and **× GEAR** extends it in gold on "amplifies".<br>• On "doesn't replace" the tiles are struck out one by one and output collapses: **NO BASE · NOTHING TO AMPLIFY → 0**. |
| 27.8 | step two: bloodwork | **Scan wipe in the same frame to STEP 02 · BLOODWORK** (header ticks 01 → 02). A lab requisition form: estradiol (sensitive), hematocrit, ApoB, liver, kidney tick in ink as named, then a 7-day blood-pressure log fills. On "before you start changing anything" the dose-adjustment field is flagged **HOLD · REVIEW FIRST**. |
| 38.3–45.0 | step three, synergy and mechanisms | Talking head. |
| 45.0 | adding another anabolic… cardiovascular, endocrine, side effects… no reason | **STEP 03 · STACK AUDIT.** TESTOSTERONE plus a "+ COMPOUND 2" chip. GROWTH barely moves (NOT AUTOMATIC). The CARDIOVASCULAR / ENDOCRINE / SIDE EFFECTS risk bars fill as each is named. Red verdict **RISK ADDED · NO GROWTH RETURN**, with impact and shake. |
| 55.4 | step four: complication plan, AI, caber, a compound you may never open | **STEP 04 · CONTINGENCY DRAWER.** WARNING SIGNS ✓ KNOWN, then AROMATASE INHIBITOR / CABERGOLINE / SUPPORT COMPOUND as vial rows, each ✓ ON HAND as spoken. The last row is tagged SEALED on "crack open". |
| 70.2–80.3 | track side effects, water, how you feel… weekly check-ins, daily communication | Quiet chip lists over the wall, keeping the face clear: TRACK · DAILY, then COACHING. |
| 80.9 | keep that cabinet full… pops up… next two to three weeks… catch it way before | **Callback:** the drawer panel returns, then scan-wipes to **EARLY CATCH**. A red dot appears ("SIDE EFFECT APPEARS"), a dashed IF MISSED curve projects out to week 3, and a gold bracket marks **CAUGHT EARLY**. |
| 89.1–98.9 | "in basic terms…" four steps | **Full-screen recap** (carousel look). "THE 4 STEPS." with four heavy blocks landing on each step: OPTIMIZE THE STIMULUS / UNDERSTAND YOUR BIOMARKERS / EVALUATE THE EVIDENCE / PREPARE FOR COMPLICATIONS, each with a one-line sub. Step 04 pulses gold on "prepare yourself for the worst". |
| 99.0–108.3 | running anabolics isn't just stacking… | Talking head, and the pinned title returns. |
| 108.4 | CTA | **End card:** logo, COACH AGZ, @coach.agz. ENHANCED ATHLETE / BLOODWORK + / RISK MANAGEMENT / CHECKLIST build as spoken, then + OPTIMIZATION LIST. A gold **COMMENT "OPTIMIZE"** pill lands on "comment", and **SENT TO YOU · FREE** follows on "free". Disclaimer below. |

**Sound** (synthesised, `sfx.py`, 73 cues):
- Whoosh and sub thud on each panel landing.
- Scan sweeps on the wipes.
- Ticks on key rows only.
- Two heavy impacts, on the verdicts.
- Thuds on the recap blocks and the CTA pill.
- No music.

## Checks done
- **Paper edit:** the assembled cut was re-transcribed. All 407 words are present apart from the deliberately cut "for".
  - "two **to** three" was dropped by the transcriber. The nearest trim sits in silence below −45 dB, 0.7 s away.
  - No stumbles found by the filler-preserving pass.
- **Captions:** built from the medium.en transcript of the trimmed audio.
  - Corrections: RUNNING ANABOLICS (heard as "Running in a box" / "Funding anabolic"), CHECK-INS, APOB, CABER, "TO" restored in "two to three".
  - Swears are starred.
  - "Science mechanics" is captioned as heard.
- **Frames:**
  - QC stills of every beat.
  - Frame strips at the hook handoff, every panel in/out, both verdicts, the scan wipes, recap in/out with the pinned-title return, the end-card build and the pill.
  - Full decode with no errors.
  - Chunk seams were verified frame-exact against fresh renders of the seam frames.
- **Defects fixed during build:**
  - The hook headline sat on the cap.
  - BP day boxes overlapped their label, and the HOLD tag covered the BP row.
  - The chip header was invisible on the light wall.
  - The early-catch labels collided.
  - A 0.25 s face flash between STEP 01 and STEP 02. They're now one panel with a scan wipe.
- **Audio:**
  - The source has 124 samples at full scale across 26 brief moments: phone-mic clipping on hard consonants, baked into the recording. It was left as recorded and **needs a listen**.
  - Voice +3.6 dB, then the limiter.
- **Not done:**
  - Listening.
  - Subject cutout.
  - Real fonts (Bebas Neue, Barlow Condensed, DM Sans and JetBrains Mono are stand-ins).
- **Content:**
  - The panels depict what's said. No lab values, studies or product names are invented.
  - The requisition lists tests to order, not results.
  - Compound names (aromatase inhibitor, cabergoline) are the ones Coach AGZ names.
  - The curves are illustrative shapes, with no data points.
