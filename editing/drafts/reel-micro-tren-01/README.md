# Reel: "Micro tren hook 2" — Tren microdosing (native 1080p)

**Status:** full edit for review. **Exported at native 1080×1920** at Coach AGZ's request ("keep it 1080p"); earlier drafts were 720p previews. Built on the saved setup and `editing/TEXT_HOOK_ENGINE.md`; the engine output is in `edit_log.json`.
**Source:** Drive file `1RPRd303Shvdb_r9HjgqK1XGQpfemKKuC`, 1080×1920 HEVC 60 fps, 1:58.3, single indoor take.
**Output:** `coach-agz_micro-tren_1080p30.mp4`, **1080×1920**, 30 fps, H.264 High (CRF 16) + AAC 192k, 1:59.0 (117.7 s of speech plus a 1.3 s end-card hold).

## Order of work
1. **Audio check:** both channels carry the voice (L/R −26.3/−26.4 dB) and there's no clipping. It's a quiet recording, so pauses are measured at −38 dB.
2. **Transcription:**
   - The windowed transcriber dropped whole stretches of words at window boundaries (22–30 s, 42–54 s, 62–80 s).
   - It was replaced by `transcribe_win.py` v2: 14 s windows / 3 s overlap, plus a gap guard that re-transcribes any >0.9 s hole containing speech energy. It leaves no speech gaps.
   - An audit of the previous two edits' captions found no such gaps there.
3. **Cut:**
   - No stumbles.
   - 5 dead-air trims: 0.63 s removed.
   - Captions use the source transcript mapped through the trim (the cut was silence-only). A second pass on the cut garbled one sentence, so it was used only to confirm one word ("so").
4. **Text hook engine:**
   - **Winner (C · state change):** I stopped running / **600 MG** of **TREN**
   - **Runners-up:** "25 MG of TREN / growth without the sides" and "TREN microdosing / changed my protocol"
   - **Flags:**
     - `winners.md` missing.
     - Hold capped at 6.0 s (the spoken hook is 7.7 s).
     - The trust anchor (500+ panels) lands at 0:18, just after the lock-in window.

## Top of frame
- **Text hook:** frame-0 hook, 0.00–6.00 s, then a 0.15 s fade. Boxed Barlow Condensed lines, with **600 MG** and **TREN** in v-gold.
- **Visual hook:** a punch-in on "trenbolone" at 0.76 s, then 108% alternates at each jump cut.
- **Topic band:** **TREN** microdosing until the jump cut at 59.17 s (the midpoint is 59.5 s).

## Timeline (cut timeline)
| Time | Speech | On screen |
|---|---|---|
| 0.0–6.0 | "if I had to run trenbolone acetate for the first time all over again…" | **Text hook**. |
| 8.3 | 400, 500, 600 mg… night sweats, destroyed sleep, terrible cardio, mood changes | **HISTORY · WHERE I CAME FROM:** red dose bars climb 400 → 500 → 600 on the words; NIGHT SWEATS / DESTROYED SLEEP / TERRIBLE CARDIO / MOOD CHANGES chips. |
| 18.3 | over a decade… anecdotal evidence… clinical research… 500 bloodwork panels | **Scan wipe to TRUST · EVIDENCE BASE:** ✓ 10+ YEARS COACHING ✓ ANECDOTAL EVIDENCE ✓ CLINICAL RESEARCH, then **500+** BLOODWORK PANELS REVIEWED (counts up), LAST COUPLE OF YEARS. |
| 28.0–33.3 | "tren is an extremely potent 19-nor anabolic steroid" | Talking head. |
| 33.3 | reducing the dose reduces exposure… preserve the androgenic effects… reduce the sides | **THE QUESTION · LOWER DOSE · SAME SIGNAL?** TOTAL EXPOSURE ▼, ANDROGENIC EFFECT held (PRESERVED?), SIDE EFFECTS ▼. |
| 43.7–63.0 | let's be real… 30 minutes of sleep… why microdosing is fascinating… what I do now | Talking head. |
| 63.0 | 19-nor, androgenic rating of 500 = 5× test, binds AR with 5× affinity, also glucocorticoid receptor → anti-catabolic | **MECHANISM · WHY A LITTLE IS A LOT:**<br>• 19-NOR, then ANDROGENIC RATING **500** = 5× TESTOSTERONE.<br>• AR affinity bars: TEST 1 vs TREN 5×.<br>• ALSO BINDS · GLUCOCORTICOID RECEPTOR, ANTI-CATABOLIC, KEEPS MUSCLE IN A DEFICIT. |
| 81.0–83.6 | "So what do we do?" | Talking head. |
| 83.6 | 25 to 50 mg a week to start… meaningful AR activation… partitioning, nitrogen retention, fat oxidation… not the sides | **PROTOCOL · THE MICRODOSE:**<br>• **25–50** MG / WEEK, TO START.<br>• MEANINGFUL AR ACTIVATION, TRACE AMOUNTS · HIGH AFFINITY.<br>• ✓ NUTRIENT PARTITIONING ✓ NITROGEN RETENTION ✓ FAT OXIDATION ✕ THE NOTORIOUS SIDES. |
| 105.9–end | CTA | **End card:** MY FULL **TREN MICRODOSE** PROTOCOL; COMPOUND SELECTION · ANCILLARIES · BLOODWORK MARKERS; **COMMENT "MICRO"** pill; SENT TO YOU · FREE; disclaimer. |

**Content:** every number on screen is Coach AGZ's own (400/500/600 mg, 500+ panels, rating 500, 5×, 25–50 mg). No studies are named. Bars and meters are illustrative. The disclaimer sits on the topic band and the end card.

## Caption notes
- **0.0 s:** both unprompted models hear "**And** if I had to run…", so it's captioned AND. (The vocab-prompted pass heard "Listen".)
- **8.3 s:** captioned "LISTEN, fellas". The passes split between "Listen", "And" and a garble, so it **needs a listen**.
- **Corrections:** 19-NOR, ANTI-CATABOLIC, TREN'S, "full **Tren** microdose protocol"; swears starred.

## Checks done
- **Captions vs final audio:** the final-audio pass was the weakest of the three (it garbled "potent 19-nor anabolic steroid" and "androgenic", and dropped "five" and "couple years alone"). Those phrases were confirmed by a separate shifted-window re-transcription of the source, so they stay. Drift: median 0.01 s, p95 0.05 s.
- **Frame 0** at full 1080×1920 shows the full hook.
- **Frames:**
  - Strips at the hook exit and band entry, every panel open and close, the HISTORY → EVIDENCE wipe, the band exit at 59.17 s, the end card and the pill.
  - Full decode, all 3,570 frames at 1080×1920.
  - Chunk seams frame-exact.
- **Audio:**
  - The source is two-channel, so it's kept as recorded.
  - Voice +9.1 dB, then the limiter: −14.3 LUFS, peaks −1.9 dBFS, left and right matched.
  - All heavy hits within 1 ms of their frames. No music. Not listened to.

**Not done:**
- Listening.
- Subject cutout.
- Real fonts (stand-ins).
- `winners.md`.
