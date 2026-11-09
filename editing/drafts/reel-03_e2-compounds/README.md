# Reel 03: "3 compounds for E2" (Primo · Masteron · EQ), 1080p

**Source:** Drive `1DwfnUXWXIeJsI8DgH-3T0KNEr-O-EcLL` ("3 e2 lowerin compounds", 1080×1920 HEVC 60 fps, 1:57, one take in the car).
**Output:** `coach-agz_3-compounds-for-e2_1080p.mp4`, 1080×1920, 30 fps, H.264 High + AAC, faststart (plays and saves on a phone), 1:56, −14.3 LUFS, true peak −1.4 dBFS.

## Cut
One clean take, so no retakes to remove. Seven pauses of 0.27–0.40 s were trimmed to about 0.12 s (`trim.json`, 1.3 s removed). Punch-ins alternate 100/108% at each jump cut.

## Text hook (TEXT_HOOK_ENGINE, see `edit_log.json`)
"3 compounds for **E2** / last one wrecks new users", fully visible on frame 0 and held to 6.0 s. Then a **locked-lineup band** runs until the midpoint: "3 compounds for **E2**" with slots 01 / 02 / 03. The names stay redacted and unlock only when spoken: PRIMO at 0:12, MASTERON at 0:32, and EQUIPOISE (red) at 0:56. Version 1 listed all three names in the band from 0:06, which gave the payoff away. Coach AGZ's feedback fixed that, and it is now a rule in `TEXT_HOOK_ENGINE.md`.

## Overlays: a different type for every beat
| Time | Beat | Overlay type |
|---|---|---|
| 0:00 | Hook | Text hook, plus three numbered slots; #03 flags red "NEW USERS" on "last one" |
| 0:11 | Primobolan | Glass **spec card** with a crimson bar: aromatizer **spectrum** with a marker on LOW–MOD and "BEST FIT", then CLASS / AROMATIZES / E2 EFFECT cells |
| 0:21 | AIs without bloodwork | Frosted takeover **line graph**: E2 trend, AI pill drops, the line crashes below the DIALED-IN band, JOINTS / LIBIDO / MOOD chips |
| 0:29 | Masteron | **Kinetic title**: "02" plus MASTERON slam, with "MASS BUILDER" struck through |
| 0:35 | Mechanism | **Picture-in-picture** carousel scene (the footage shrinks into a window): receptor schematic (AR dock, signal, ER "OPPOSED", SERM-LIKE), then a **bar chart** (side effects BLOCKED vs systemic E2 UNCHANGED). The window expands back to full screen as the handoff out |
| 0:56 | Equipoise | **Verdict bar** slam across the cap, "BEGINNERS ✕" |
| 1:00 | E2 control all over the place | Full-screen navy **carousel cutaway** with a **scatter plot**: an EXPECTED trendline vs scattered users, "NO RELIABLE PATTERN" |
| 1:10 | Undecylenate ester | Cyan **scan monitor**: a release curve keeps tailing past the LAST INJECTION marker, with a WEEKS → MONTHS ruler |
| 1:19 | Fixing it | Gold-top card: an **icon stack** (ancillaries + supplements + compounds) and a **12-week calendar** that fills to 8–12 |
| 1:29 | Hematocrit | **Dial gauge**: the needle swings into red ELEVATED, then a slow RECOVERY crawl, "NOT OVERNIGHT" |
| 1:34 | Bloodwork roadmap | A **paper lab report** slides up. Rows highlight as named, a "How you feel" symptom row is added, a CROSS-REFERENCE bracket links them, then the "LABS + SYMPTOMS = ROADMAP" verdict bar |
| 1:44 | Measure → decide | **Process stepper** chevrons |
| 1:48 | CTA | End card: logo, a two-item checklist, and a gold `COMMENT "LABS"` pill landing on "comment", plus the disclaimer |

The footage itself is untouched (no grade). Vibrance lives in the overlays only (test-06 palette).
Captions show every word, with a red block on the active word. They sit at about y1392 because the mouth is at about y1290 in this framing.

## QC done
- **Word timing:** whisper medium.en with word timestamps, run on the raw take and on the trimmed cut. The two agree to within 0.03 s (p90). Drug names were corrected (Primobolan, Masteron, SERM, undecylenate).
- **Visuals:** checked overview frames every 2 s and frame strips at the hook exit, the Primo exit into the graph, the jump cut into Masteron, the PIP handoff, and the cutaway into the ester monitor. Fixed: hook and band overlapping, a Primo glow trail, cutaway dots bleeding into the next scene, a 1-frame clean flash, label collisions.
- **Sound:** 7 key impacts were measured landing on their target frames (0 ms off).
- **Not done:** listening (levels measured only). The lab values and the scatter dots are labelled SAMPLE / ILLUSTRATIVE. Fonts are stand-ins (Bebas Neue, Barlow Condensed, DM Sans, JetBrains Mono).

Build: `python3 render.py <scratch> <n0> <n1> out.mp4` (4 chunks in parallel), `python3 sfx.py <scratch>`, then mix with loudnorm to −14 LUFS.
