# Reel: "Mast primo ai" — Masteron + Primo are not AIs (720p30 preview)

**Status:** first full edit, for review. Not a final export; a final would be 1080×1920.
**Source:** Drive file `1tpuu9OSqxBi-x2GE2OcFAjjksTlGCJbU` ("Mast primo ai"), 1080×1920 HEVC 60 fps, 53.1 s, walking selfie outdoors in direct sun, single take. It's a new, shorter script on the same topic as full test 01.
**Output:** `coach-agz_mast-primo-not-ai_720p30.mp4`, 720×1280, 30 fps, H.264 + AAC, 54.07 s (52.77 s of speech plus a 1.3 s end-card hold). −14.0 LUFS, peaks −1.8 dBFS.

## Saved setup applied
- **Look (test 06):**
  - Every-word captions with the red active-word block.
  - Evidence panels that grow out of the gold edge rule.
  - High-pop overlay palette and bloom.
  - Lit verdict bar with a 2-frame shake.
  - Footage ungraded.
- **Workflow (full test 02):**
  - Vocabulary-prompted and filler-preserving transcription.
  - Misspeak check (none found).
  - Dead air of 0.22 s or more trimmed to about 0.12 s: 2 trims, 0.37 s.
  - 108% punch-in alternating at each jump cut, plus two punch-ins on new points (19.98 s and 33.32 s).
  - Captions from the trimmed audio.
- **Light stabilisation:** vidstab, smoothing 20.
- **Framing:** the chin is at about y 1380 and the chest tattoo starts at about 1560, so captions sit at **y ≈ 1450**. That's on the upper chest, above the tattoo, which the clip-7 review flagged as hurting readability.

## Captions to confirm with Coach AGZ
Every transcription pass (small and medium, with and without prompts) hears these two words as below. They're captioned by meaning:

| Time | Heard | Captioned | Why |
|---|---|---|---|
| 26.7 | "**Everything**/**thing** actually got inhibited" | **NOTHING** actually got inhibited | The point is that aromatase is *not* inhibited; the "No-" is swallowed. |
| 33.6 | "it's **unimportant** to understand these mechanics" | it's **IMPORTANT** to understand | "…so to simplify it" follows. |

Other corrections:
- MASTERON (heard "Mastron").
- ARIMIDEX.
- OUT-COMPETE and ANTI-ESTROGEN joined into single words.

## Timeline (trimmed timeline)
| Time | Speech | On screen |
|---|---|---|
| 0.0–5.5 | "Masteron and Primo are not AIs… treat them like synergistic compounds" | **Hook title card:** a gold kicker types "MASTERON · PRIMO". **ARE NOT AIs.** lands, with "AIs" turning red when spoken. A gold tag **TREAT AS: SYNERGISTIC COMPOUNDS** slides in on "synergistic". |
| 5.5 | | **Handoff:** the headline shrinks into the **pinned title** (kicker + ARE NOT AIs). |
| 6.1–19.9 | DHT derivatives, bind the androgen receptor hard, out-compete estrogen, signal drops, E2 labs drop | **EVIDENCE 01 · RECEPTOR SITE:**<br>• MASTERON / PRIMOBOLAN chips tagged DHT-DERIVED.<br>• Six receptor slots fill with gold ligands on "bind hard" (BOUND · HIGH AFFINITY).<br>• E2 rings are pushed off (OUT-COMPETED).<br>• The ESTROGEN SIGNAL meter falls on "drops".<br>• An E2 LAB (SENSITIVE) row is tagged READS LOW. |
| 20.0–21.5 | "the part most guys tend to miss" | Talking head with a punch-in. |
| 21.5–32.7 | aromatase still signaling, T still converting, nothing inhibited… arimidex… block the signal downstream | **EVIDENCE 02 · AROMATASE:**<br>• TESTOSTERONE → AROMATASE → E2, with the enzyme lighting STILL ACTIVE.<br>• Gold particles keep flowing (T → E2 · CONVERTING).<br>• The enzyme is bracketed **NOT INHIBITED**.<br>• Comparison rows: ARIMIDEX · AI crosses out the enzyme (ENZYME BLOCKED); MASTERON · PRIMO caps the receptor after E2 (SIGNAL BLOCKED DOWNSTREAM). |
| 32.7–36.3 | "it's important to understand… simplify" | Talking head with a 110% punch-in. |
| 36.3–50.3 | AI shuts off the faucet; Mast, Primo, EQ cover the drain; water still coming in; wrong number | **EVIDENCE 03 · SIMPLIFIED**, Coach AGZ's faucet analogy as cyan line schematics:<br>• Left, AI · ARIMIDEX: the valve turns red and closes, and the stream stops (SUPPLY OFF).<br>• Right, MAST · PRIMO · EQ: the stream runs, a gold cover lands on the drain (DRAIN COVERED), and the basin keeps filling (STILL FLOWING).<br>• Verdict **E2 LOW ≠ PRODUCTION OFF**, with impact and shake. |
| 50.2–end | "Save this and share it and tell me what you think" | **End card:** logo, COACH AGZ, @coach.agz, MASTERON · PRIMO / ARE NOT AIs. A gold **SAVE + SHARE** pill lands on "save", then **TELL ME WHAT YOU THINK · COMMENTS** and the disclaimer. |

**Sound:** synthesised, `sfx.py`, 32 cues.
- Whoosh and sub thud on each panel landing.
- Scan sweeps on the receptor fill, the conversion flow and the water rising.
- Ticks on flags.
- One heavy impact, on the verdict.
- No music.

## Checks done
- **Paper edit:** the assembled cut was re-transcribed. It matches 186/186 source words, so nothing was clipped. The filler-preserving pass found no stumbles.
- **Captions vs final audio:** 178/184 match. The 6 differences are exactly the deliberate corrections above. Drift: median 0.00 s, p95 0.02 s, max 0.04 s.
- **Frames:**
  - QC stills of every beat.
  - Frame strips at the hook handoff, every panel open and close, the verdict and the end-card arrival.
  - Full decode, all 1,622 frames.
  - Chunk seams verified frame-exact against fresh renders.
- **Defects fixed during build:**
  - The E2 lab chip sat on the cap brim (no free side space in this framing). It's now the last row of EVIDENCE 01.
  - A label collided with the supply pipe.
  - Panel glow lingered on the cap for about 5 frames after a panel collapsed. Each panel's glow now fades and is masked with its panel.
  - A 2-frame face flash before the end card. The last panel now closes under it.
- **Sound sync:** every heavy hit is within 1 ms of its visual frame.
- **Audio:** the source has 100 samples at full scale (brief clipping, likely wind or loud consonants outdoors). It's left as recorded and **needs a listen**. Voice +2.4 dB, then the limiter.
- **Not done:**
  - Listening.
  - Subject cutout.
  - Real fonts (Bebas Neue, Barlow Condensed, DM Sans and JetBrains Mono are stand-ins).
- **Content:** the panels depict Coach AGZ's own claims and analogy. No lab values, studies or numbers are shown.

## Audio fix (2026-11-03): voice was right channel only
The source recording carries the voice in the **right channel only** (left silent, about −109 dB). The earlier version of this preview carried that through, so the voice played in one ear on headphones. It also skewed the loudness readings.
- **Fix:** the right channel is copied to both channels (dual-mono), then the voice is re-mastered with the SFX bed. Left and right are now identical.
- **Result:** −14.2 to −14.3 LUFS, peaks about −2.0 dBFS. Video, captions and timing are unchanged.
- The pipeline now checks channel balance before mixing.
