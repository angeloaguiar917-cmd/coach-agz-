# Reel: "Tren builds the best illusion" (720p30 preview)

**Status:** first full edit, for review. It is built on the editor-test-06 setup and doesn't change the approved settings.
**Source:** Drive file `1PZrmLLbNzwc4Eda52N-98N-phbkGXJtc` ("TREN Claude test edit"), 1080×1920 HEVC, 60 fps, 102.3 s, single take in the car. The full length is used.
**Output:** `coach-agz_tren-illusion_720p30.mp4`, 720×1280, 30 fps, H.264 + AAC, 102.27 s. Loudness is −14.0 LUFS integrated, with peaks at −1.8 dBFS.

## Carried over from the saved setup (test 06)
- **Captions:** every word, with a red block on the active word, in Bebas caps and groups of 2–3 words.
- **Overlays:** clinical evidence panels (frosted near-black, gold frame and brackets, red rec dot, `EVIDENCE 0X` counter) and red flag brackets with lit tags.
- **Effects:** red verdict bars with a 2-frame shake, cyan scan wipes between stages, the high-pop overlay palette and bloom, and the gold left edge rule.
- **Footage:** no grade, saturation or contrast change. The only changes are light stabilisation, the punch-ins and the dark push behind panels.

## Changes needed for this footage
- **Caption line moved from y≈1335 to y≈1450 (1080 space).** In this framing the chin sits at about y 1340, so the saved position landed on the beard. The new line sits on the dark hoodie, above the Instagram bottom UI.
- **Light stabilisation:** vidstab, smoothing 20, with a small auto-zoom.
- **Grouping:** caption groups avoid ending on weak words (THE / AT / IN…). For example, "ACTUALLY BUILD / THE MOST MUSCLE".
- **Transcript fixes:**
  - Trenbolone, enanthate and androgen were misheard and are corrected.
  - "trend" is corrected to TREN.
  - "re-composition" is merged into one word.
  - "until you get dry…" becomes "SO you get dry…", confirmed with a second, larger model.
  - Swears are starred: F*CKING, SH*T.

## Timeline
| Time | Speech | On screen |
|---|---|---|
| 0.0–4.1 | "Tren doesn't build the most muscle… best illusion" | **Hook title card:** a gold kicker draws on and "TRENBOLONE" types in. "NOT THE MOST MUSCLE." lands, then "THE BEST ILLUSION." ILLUSION turns red when it's spoken. |
| 4.1–4.45 | | **Handoff:** the headline shrinks into the **pinned title** bar ("THE BEST ILLUSION", @coach.agz, disclaimer), which stays until 87 s. |
| 7.9 / 24.3 / 32.7 / 53.9 / 74.5 / 85.6 | new points | **Punch-ins** (110–118%), each a 4-frame snap with a soft sub hit. The viewer-voice line ("Yeah coach, but I took tren…") gets its own punch-in. |
| 11.4 | "binds to androgen receptors 3–6× stronger" | **EVIDENCE 01 · RECEPTOR BINDING:** the testosterone bar lands at 1×. The tren bar grows to 3× on "three", then a hatched band extends to 6× on "six". |
| 16.56 | "protein synthesis up, breakdown down…" | **Scan wipe to EVIDENCE 02 · ANABOLIC PROFILE:** meters move with each word. TREN → E2 is crossed out and flagged NONE. The DRY / HARD / GRAINY chips tick in, then the water-retention meter drops. |
| 25.3 | "no real clinical studies on humans…" | **EVIDENCE 03 · LITERATURE SEARCH:** the query types in and filter chips light as they're spoken. A big red "0" lands on "studies". The existing evidence appears as LIVESTOCK / RODENT / IN-VITRO rows tagged NOT HUMAN. The verdict bar **UNPROVEN · IN HUMANS** slams in on "testosterone", with an impact and shake. |
| 36.7 | "why does it look the way it does?" | **EVIDENCE 04 · WHY IT LOOKS LIKE GROWTH** contrasts what you see with what causes it:<br>• 01 LOOKS LEANER + HARDER: FAT ▼ WATER ▼<br>• 02 BIGGER + FULLER: GLYCOGEN ▲ FULLNESS ▲<br>• 03 FEELS LIKE GROWING: STRENGTH ▲, SOURCE: NERVOUS SYSTEM<br>Then a RECOMPOSITION pill lands and "+10 LB NEW MUSCLE" is struck out on "muscle". |
| 56.5 | "the three things that build muscle" | **EVIDENCE 05 · MUSCLE BUILDERS · ON CYCLE:** SLEEP / TRAINING / NUTRITION start at green BASELINE and flip to red (DISRUPTED, CARDIO LIMITED, OFF TRACK) as they're spoken, with re-pulses on the repeats. The MOOD and BLOOD PRESSURE chips appear, then the RECOVERY DEFICIT bar fills to **20 WEEKS** with an impact and shake. |
| 77.8–85.3 | "right hormonal environment… lifestyle… sleeping… eating" | A quiet checklist on the left over the seat: ✓ HORMONES / LIFESTYLE / SLEEP / FOOD. The face stays clear. |
| 87.3 | "Test, food, sleep, progressive overload and time" | **Full-screen carousel look** (navy, warm glow, grain). The pinned title exits and five heavy blocks land bottom-up on each word, the last one heavier. "WHAT BUILDS MUSCLE." lands, with MUSCLE turning gold. |
| 93.9 | "the real muscle equation" | The kicker re-types as THE REAL MUSCLE EQUATION, "+" signs snap in, and a gold **= MUSCLE** bar slides under the stack. |
| 98.5 | "Comment the word muscle…" | **Handoff:** the = MUSCLE bar morphs into the **COMMENT "MUSCLE"** gold pill. The stack clears, then the end card builds: logo, COACH AGZ, @coach.agz, THE REAL MUSCLE EQUATION and the disclaimer. **SENT TO YOU · FREE** follows on "free". |

Panels open out of the gold edge rule and collapse back into it. That's the handoff between beats, so the face returns between every panel.

## Sound (synthesised, original; `sfx.py`)
- **Panels:** a whoosh into each panel and a sub thud on the landing frame.
- **Rows and flags:** digital ticks on key rows and flags only.
- **Scan sweeps:** on the stage wipe, the search query and the recovery fill.
- **Heavy impacts:** three, on UNPROVEN, 20 WEEKS and the last block.
- **No music.** The voice was raised +8.7 dB and limited, landing at −14.0 LUFS.

## Checks done
- **Transcript:** the final mix was re-transcribed and matches 404/409 words, mean drift 0.02 s. The 5 differences are ambiguous words that Whisper hears differently on each pass. The meaningful one ("until" → "so") was rechecked with a larger model and corrected.
- **Frames:**
  - QC stills of every beat.
  - Frame-by-frame strips of every fast transition: hook handoff, a punch-in, all panel opens and closes, the scan wipe, both shakes, the stack scene in and the end-card morph.
  - The full file decodes without errors, 3,068 frames.
- **Defects found and fixed:**
  - Fades drawn directly on the frame rendered at full opacity, because Pillow replaces RGBA pixels instead of blending. This broke the title handoff, checklist, stack exit and end card. They're now drawn on composited layers.
  - Line 1 of the hook collided with the headline during the handoff.
  - The checklist sat on top of the cap.
  - The end-card text overlapped the fading stack for about 4 frames.
- **Sound sync:** every heavy hit was measured. In the SFX track each is within 1 ms of its visual frame. In the full mix, 6 of 8 detect within ±33 ms. The other two read early because voice energy masks the detector; on the SFX track they're exact.
- **Not done:**
  - **Listening.** Audio was checked by measurement only, so the SFX levels against the voice need an ear.
  - **Subject cutout.** Nothing sits behind the head; no segmentation tool was available.
  - **Fonts** are stand-ins (Bebas Neue, Barlow Condensed, DM Sans, JetBrains Mono).
- **Content:** panel contents are illustrative depictions of what's said. No study, lab value or source is named or invented. The 3–6× binding range and "no aromatisation" are Coach AGZ's own spoken claims.

## Rebuild
`render.py <scratch>` expects `<scratch>/work/raw.mov` (stabilised 1080×1920, 30 fps), `<scratch>/work/words.json`, `<scratch>/fonts/` and `<scratch>/logo.jpg`.

1. `--events` writes the SFX cue list.
2. `sfx.py events.json sfx.wav 102.28` builds the SFX bed.
3. `--range n0 n1 out.mp4` renders frames.
4. `--still t…` renders QC stills.
