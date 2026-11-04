# Reel: "Gram vs 6pack" take 2 — outdoor, 42 drinks a week (720p30 preview)

**Status:** first full edit, for review. Not a final export; a final would be 1080×1920. Built on the saved setup and `editing/TEXT_HOOK_ENGINE.md`; the engine output is in `edit_log.json`.
**Source:** Drive file `13nhuwmyLQYanj8CwA_cuUa5xs2JcfhUm`, 1080×1920 HEVC 60 fps, 1:28.1, single take walking outdoors. It's a new script on the same topic as `reel-gram-vs-sixpack-01`.
**Output:** `coach-agz_gram-vs-sixpack-02_720p30.mp4`, 720×1280, 30 fps, H.264 + AAC, 1:29.1 (87.8 s of speech plus a 1.3 s end-card hold).

## Order of work
1. **Audio check first:**
   - The source voice is in the **right channel only** (left about −111 dB), so it was made dual-mono at the stabilisation step, before anything else.
   - The source has 101 full-scale samples (baked-in clipping), left as recorded.
2. **Cut:**
   - Windowed medium.en transcription of the source, with spot rechecks by small.en.
   - No stumbles.
   - One dead-air trim (81.50–81.91 s → about 0.12 s): 0.27 s removed.
   - The cut was re-transcribed in windows: 308 words.
3. **Text hook engine** on the cut's transcript (`edit_log.json`):
   - **Winner (A · pain):** **1 GRAM** vs **42 DRINKS** / your heart pays either way
   - **Runners-up:** "42 DRINKS a week / vs 1 GRAM of TEST" and "1 GRAM of TEST / cardiac remodeling risk"
   - **Flags:**
     - `winners.md` missing.
     - Trust anchor missing in the lock-in zone.
     - Hold capped at 6.0 s.
     - The hook was chosen to differ from take 1's "same red flags".
4. Captions, graphics, sound, render.

## Text hook and top-of-frame
- **Text hook:**
  - Frame-0 hook, 0.00–6.00 s, then a 0.15 s fade.
  - Premium mode (Barlow Condensed), boxed lines over the bright sky.
  - **1 GRAM** and **42 DRINKS** in caps and v-gold; the rest sentence case.
- **Visual hook:** a 108% punch-in snaps in on "a thousand milligrams" at 0.26 s.
- **Topic band:** **1 GRAM** a week vs **6 BEERS** a night, from 6.0 s to the midpoint (44.57 s; there's no jump cut within 1.5 s, so it fades at the midpoint).
- **Captions:** y ≈ 1450 (upper chest).

## Timeline (trimmed timeline)
| Time | Speech | On screen |
|---|---|---|
| 0.0–6.0 | "…a thousand milligrams of testosterone a week or a six-pack every single night…" | **Text hook**, with the punch-in. |
| 6.8–21.4 | gram side + long-term | **SIDE A · 1 GRAM TEST / WEEK:**<br>• HEMATOCRIT CLIMBS ▲, BLOOD PRESSURE RISES ▲, HDL CRASHES ▼, APOB CAN INCREASE ▲, NATURAL PRODUCTION SUPPRESSED ▼.<br>• Then a gold LONG-TERM divider, with CARDIAC REMODELING RISK ▲ and CARDIOVASCULAR DISEASE RISK ▲. |
| 21.4–25.4 | "Now, my friends, the six-pack every night" | Talking head. |
| 25.4–38.2 | 42 drinks a week… | **SIDE B · 6 BEERS / NIGHT:**<br>• A big gold **42** DRINKS A WEEK (6 A NIGHT × 7).<br>• LIVER DISEASE RISK ▲, TRIGLYCERIDES ELEVATED ▲, HYPERTENSION RISK ▲, SLEEP DISRUPTED ▼, CANCER RISK INCREASED ▲.<br>• Verdict **GROUP 1 CARCINOGEN**, with impact and shake. |
| 38.2–40.1 | "here's where it gets interesting" | Talking head. |
| 40.1–47.4 | both damage the cardiovascular system; stigmatized vs Super Bowl | **A vs B · SAME HEART:** CARDIOVASCULAR DAMAGE flagged in both the **1 GRAM** and **6 BEERS** columns, then STIGMATIZED vs SUPER BOWL AD, and verdict **SAME BODY · TWO STANDARDS**. |
| 47.4–64.0 | can't tell which kills faster without… / drinkers skip bloodwork 3–5 years | **Scan wipe to VERDICT · WHICH KILLS FASTER:**<br>• CAN'T BE CALLED WITHOUT: DURATION / INDIVIDUAL RISK / HEALTH OUTCOMES.<br>• WHAT IS KNOWN: 6 BEERS A NIGHT · LAST BLOODWORK, with the count stepping **3 → 4 → 5** YEARS AGO on the words.<br>• ONLY A BASIC PANEL · WHEN SICK. |
| 64.0–68.2 | "end of the day your organs don't care…" | Talking head. |
| 68.2–81.6 | get your bloodwork done; understand… | **WHAT MATTERS:**<br>• RUNNING **1 GRAM** OR DRINKING **EVERY NIGHT**, then **GET YOUR BLOODWORK DONE.**<br>• UNDERSTAND: ✓ what's happening in your system ✓ side effect mitigation ✓ your biomarkers ✓ how to optimize. |
| 81.7–end | "a six-pack isn't the way… neither is a gram every week for the rest of your life" | **End card:** logo, COACH AGZ, @coach.agz. NOT THE WAY, then 6 BEERS A NIGHT and 1 GRAM EVERY WEEK FOR LIFE, each struck through in red as spoken. Then GET YOUR BLOODWORK DONE and the disclaimer. There's no comment-keyword CTA, because none is spoken. |

## Caption notes
- **To confirm (64.5 s):** heard "**On** the day" / "**In** the day", clipped. Captioned **END OF THE DAY** by sense.
- "On basic terms" is captioned **IN BASIC TERMS**.
- "a gram a test" is captioned "gram **of** test".
- LONG-TERM joined into one word; swears starred.
- "Now, my friends" is as said (both models agree).

## Checks done
- **Captions vs final audio** (windowed pass): 299/307 before fixes. The differences are the deliberate corrections (OF, IN, END OF, LONG-TERM, starred swears, "gotta"/"got to"), plus one real miss: "cardiovascular **system**" (42.1 s) had been dropped by the cut's transcript. It was restored and that chunk re-rendered. Drift: median 0.00 s, p95 0.02 s, max 0.18 s.
- **Frame 0** shows the full hook.
- **Frames:**
  - Strips at the hook exit and band entry, every panel open and close, both shakes, the stage wipe, the band exit at the midpoint, and the end card with the strike-throughs.
  - Full decode, all 2,674 frames.
  - Chunk seams frame-exact.
- **Audio:**
  - Dual-mono, left and right identical.
  - −14.3 LUFS, peaks −1.8 dBFS (no AAC overshoot).
  - All heavy hits within 1 ms of their frames. A duplicate thud on the "42" (0.26 s after the panel landing) was removed: one heavy hit per beat.
  - No music.
  - The source clipping (101 samples) is left as recorded and **needs a listen**.

**Not done:**
- Listening.
- Subject cutout.
- Real fonts (stand-ins).
- `winners.md`.

**Content:** the panels show Coach AGZ's own claims and numbers (1 gram, 6 a night = 42 a week, 3–5 years, Group 1 carcinogen). No lab values or studies are shown. The arrows are illustrative.
