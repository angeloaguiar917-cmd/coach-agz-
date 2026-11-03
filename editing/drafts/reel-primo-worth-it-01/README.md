# Reel: "Primo Ai edit" — Primo: holy grail or placebo (720p30 preview)

**Status:** first full edit, for review. Not a final export; a final would be 1080×1920. This is the first edit run under `editing/TEXT_HOOK_ENGINE.md`; the engine output is in `edit_log.json`.
**Source:** Drive file `1cXPmoIQfuKga_uvYr8oEMxOVNeGv242E` ("Primo Ai edit"), 1080×1920 HEVC 60 fps, 1:34.4, single indoor take with no scene cuts.
**Output:** `coach-agz_primo-worth-it_720p30.mp4`, 720×1280, 30 fps, H.264 + AAC, 1:33.6 (92.3 s of speech plus a 1.3 s end-card hold).

## Order of work (per CLAUDE.md and the engine)
1. **Cut:** filler-preserving and clean transcription found no stumbles. 11 dead-air trims (≥0.22 s → about 0.12 s, frame-aligned, 8 ms fades) removed 2.03 s. The cut was re-transcribed: 358/358 words, nothing clipped.
2. **Text hook engine** on the edited cut's transcript. The JSON is in `edit_log.json`.
   - **On screen now (Coach AGZ's wording, 2026-11-03):** **Primobolan** Only Works / For One Type Of Person?
     - This overrides the engine. It breaks rule 3 ("?") and rule 8 (Title Case; subject emphasised by colour only, not caps). Its promise is paid off at the verdict (1:03–1:18), not in the lock-in zone. All of this is flagged in `edit_log.json`.
   - **Engine winner (C · state change):** **PRIMO** holy grail / both camps got it wrong
   - **Runners-up:** "PRIMO worth the price / the real verdict" and "PRIMO crashing / your estrogen too low"
   - **Flags:** `winners.md` missing (used the starter bank). Trust anchor missing in the lock-in zone: no lab, study or result between 0:04 and 0:12, and nothing invented.
3. Captions, graphics, sound, render.

## Text hook and top-of-frame (engine rules)
- **Text hook:**
  - **Visible on frame 0** with no entry animation, so it's also the cover frame.
  - Premium mode in Barlow Condensed (brand condensed, with sentence case), two equal lines.
  - **PRIMO** in caps and v-gold `#FFC21A`; the rest white, sentence case, no punctuation.
  - Each line has a dark rounded box, because the wall behind is bright (rule 7).
  - Top-centre, y ≈ 262–440, above the eyes (y ≈ 710) and inside the safe zone.
- **Hold:** 0.00–5.12 s (spoken hook ends 4.62 s, + 0.5 s), then a 0.15 s fade.
- **Visual hook:** a 108% punch-in snaps in on the spoken subject word "Primobolan" at 0.40 s. After that, 108% alternates at every jump cut (saved setup).
- **Topic band:** **PRIMO** holy grail or placebo (with @coach.agz and the disclaimer). It enters as the hook fades and exits on the jump cut nearest the midpoint (45.63 s; the midpoint is 46.8 s). After that the top of the frame stays clear.
  - This replaces the old all-caps title pinned for the whole video, as the engine's implementation notes require.
- **Captions:** back to the saved y ≈ 1335, which sits under the chin in this framing. They never overlap the hook.

## Timeline (trimmed timeline)
| Time | Speech | On screen |
|---|---|---|
| 0.0–5.1 | "Primobolan is the holy grail, or the most expensive placebo…" | **Text hook**, with the punch-in on "Primobolan". |
| 5.1 | "both sides are wrong… break it down" | Talking head with the topic band. |
| 11.5 | methenolone, DHT derivative, no aromatization (no water), no liver hit like an oral, binds SHBG → frees testosterone | **EVIDENCE 01 · COMPOUND PROFILE:**<br>• PRIMOBOLAN with METHENOLONE and DHT-DERIVED.<br>• Rows tick in as spoken: AROMATIZATION ✓ NONE (NO WATER), LIVER STRAIN ✓ NONE (NOT AN ORAL), SHBG BOUND HARD.<br>• FREE TESTOSTERONE meter ▲ (ALREADY IN YOUR SYSTEM). |
| 24.1 | the catch: weak per mg vs stronger compounds, premium price | **Scan wipe to EVIDENCE 02 · THE CATCH:**<br>• SIGNAL bars: a short PRIMO bar (WEAK PER MG) against STRONGER COMPOUNDS.<br>• MG NEEDED ▲ and COST ▲.<br>• Verdict **PREMIUM PRICE · MILD SIGNAL**, with impact and shake. |
| 34.6–37.0 | guys get burned two ways | Talking head. |
| 37.0 | way one: no aromatization → E2 too low → joints, libido, mood → blame the wrong compound | **WAY 01 / 02 · ESTROGEN CRASH:**<br>• An estradiol marker slides below a green target range (TOO LOW).<br>• JOINTS / LIBIDO / MOOD chips.<br>• BLAMED ON ~~ANOTHER COMPOUND~~, ACTUAL CAUSE **LOW E2**. |
| 47.2–51.0 | "I know you trust your source…" | Talking head (top clear after the midpoint). |
| 51.0 | most faked compound… a mystery… test vial with an AI sold as Primo | **WAY 02 / 02 · COUNTERFEIT RISK:**<br>• A cyan X-ray vial labelled PRIMOBOLAN, tagged ONE OF THE MOST FAKED.<br>• SOURCE TRUST · 10 YRS, a "?" in the vial, CONTENTS UNVERIFIED.<br>• ASSAY rows: TESTOSTERONE DETECTED, AROMATASE INHIBITOR DETECTED, METHENOLONE NOT FOUND.<br>• Verdict **LABEL ≠ CONTENTS**, with impact and shake. |
| 63.5 | final verdict: worth it if… | **VERDICT · IS PRIMO WORTH IT:**<br>• YES · IF, then a checklist ticking green as spoken: TRAINING HARD, EATING CORRECTLY, STRONG FOUNDATION, WANT THE CLEAN DRY LOOK, OK WITH THE COST, PATIENT · NOT A FAST TRANSFORMATION.<br>• Gold verdict **WORTH IT · IF EVERY BOX IS CHECKED** on "Primo is for you". This pays off the hook. |
| 78.7–end | CTA, then "Primo versus Mast?" | **End card:** logo, COACH AGZ, @coach.agz. THE FULL **PRIMO** FRAMEWORK, with "what to look for in your bloods · how to optimize". A gold **COMMENT "PRIMO"** pill, then SENT TO YOU · FREE. **PRIMO VS MAST** and TELL ME IN THE COMMENTS on the closing question. Disclaimer. |

## Caption notes
- **Corrected:** PRIMOBOLAN (heard as "primo bowling"), VIAL (heard as "bile"), starred swear.
- **15.98 s:** one pass hears "until", the other "so". Captioned as **SO** ("so there's no water"), which matches the sense.
- "Guys get burned within two ways" is captioned as said.

## Checks done
- **Paper edit:** the cut was re-transcribed: 358/358 words.
- **Captions vs final audio:** 353/357 match; the rest is transcriber variance ("vial"/"bile", "primobolan"/"primo bowling", "a"/"any", the starred swear). Drift: median 0.00 s, p95 0.04 s, max 0.28 s.
  - That check caught one real miss: "I'll send **it** out" (86.6 s) had been dropped by the cut's transcript. It was restored and the tail re-rendered.
- **Frame 0** of the encoded file shows the full hook (cover-frame rule).
- **Frames:**
  - Strips at the hook exit and band entry, every panel open and close, the stage wipe, both shakes, the band exit at 45.63 s, the gold verdict, the end card, the pill and PRIMO VS MAST.
  - Full decode, all 2,808 frames.
  - Chunk seams frame-exact.
- **Defects fixed:**
  - The TOO LOW tag sat on the ESTRADIOL label.
  - The end-card disclaimer crowded the captions (card moved up 60 px).
  - A 3-frame face flash between the verdict panel and the end card (the panel now closes under it).
- **Audio:** the source is clean, with no clipping. Voice +5.0 dB, then the limiter: −14.1 LUFS, peaks −1.9 dBFS. All heavy hits are within 1 ms of their frames. No music.

**Not done:**
- Listening.
- Subject cutout.
- Real fonts (stand-ins).
- `winners.md`.

**Content:** the panels depict Coach AGZ's own claims. The assay rows show his described case (a test vial with an AI sold as Primo); no lab, values or brands are named. Bars and meters are illustrative.
