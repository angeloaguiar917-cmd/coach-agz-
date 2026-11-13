# Reel 02: "Body fat on TRT: your hidden E2 factory" (1080p)

**Source:** Drive `18Ii2e9b6mRKuZb2GAErHxKZt9TdLsx7n` ("Fat e2 2"). 1080×1920 HEVC, 60 fps, 34.6 s, one selfie take in the car.
**Output:** `coach-agz_fat-e2_1080p30.mp4`. 1080×1920, 30 fps, H.264 High + AAC, faststart (plays and saves on a phone). About 33.8 s, −14 LUFS.
**Setup:** the saved full-test setup (test-06 overlay palette, every-word captions with the red lit word box, gold edge rule, bloom, synthesized clinical SFX). The footage is not graded.

## Brief for this one
- More overlay variety: no single overlay type repeated back to back.
- Graphs, more graphics, vibrant, on brand.
- **Keep the face recognisable.** The face fills the frame from about y 500 (cap) to y 1420 (chin), so:
  - captions moved down from y 1335 (the mouth on this footage) to y 1418 (beard and neck)
  - every overlay sits above the cap, on the side seat area or over the shoulders
  - the two scenes that need the full frame move the face itself: a split screen and a face bubble

## Cut
Single clean take, no misspeaks. Six silent runs of 0.22 s or more were trimmed to about 0.12 s (`trim.json`), which removed 0.83 s.
Punch-in alternates (100 / 107 %) at each jump cut. One push-in (100 → 105 %) lands on "body fat" for the hook.

## Overlay map (edited time): 8 different types
| Time | Line | Overlay type | What it shows |
|---|---|---|---|
| 0.0–3.0 | hook | **Frame-0 text hook** (premium) | "BODY FAT on TRT / your hidden E2 factory" above the cap, then the topic band until 0:16.9 |
| 3.2–5.8 | "a lot more estrogen" | **Side HUD meter** | E2 serum spectrum tube (low / OK / high) fills to high on "more estrogen" |
| 5.9–11.1 | "fat tissue holds… aromatase… converts" | **Split screen** + mechanism schematic | Footage slides into the top half on a gold divider. Fat-cell cross-section draws on, a cyan scan sweeps it, aromatase lights in each cell, T flows in, E2 flows out |
| 11.1–14.5 | "more fat, more conversion, higher E2" | **Full-screen graph + face bubble** | Face shrinks into a gold-ringed bubble. Body-fat wedge grows along the x-axis, the aromatase curve draws, the E2 curve and fill draw, "E2 ▲ HIGH". Labelled "illustrative trend, not lab data" |
| 14.6–19.4 | "bloated, emotional, puffy nipples" | **Side alert stack** | "E2 side-effect scan": water retention (droplet filling), mood swings (erratic trace), gyno signs (pec schematic, red detection brackets) |
| 19.6–24.0 | "same exact dose… it's the conversion" | **Top dashboard, two dials** | Body A (lean) vs Body B (higher body fat). Identical syringes and "=" CONSTANT; 1 vs 5 aromatase; the E2 dials swing to IN RANGE vs HIGH |
| 24.3–27.9 | "never starts with an AI… starts with bloodwork" | **Corner evidence objects** | Anastrozole Rx bottle, red X stamp, "NOT STEP 1" (impact and recoil). Lab order with tube; E2, total T, free T, SHBG and CBC tick off, "STEP 1" |
| 27.9–end | "Comment the word E2… free framework" | **CTA comment field + doc** | COMMENT pill, comment bar types "E2" and sends, the framework doc flies to the side, checks tick, red "FREE" stamp |

Handoffs: the split divider becomes the bubble frame; the bubble expands back into the full shot on the jump cut.

## Text hook
See `edit_log.json`. Winner: **BODY FAT on TRT / your hidden E2 factory** (subject + pain). Runners-up: "Same TRT dose / higher E2 from BODY FAT" and "Bloated on TRT / it's your BODY FAT".

## Files
- `render.py`: frame renderer (stills mode for QC, chunk mode for the render)
- `sfx.py`: SFX bed
- `words_final.json`: caption words in edited time (from a vocabulary-prompted pass; "At the end of the day", "Your fix" and "E2" fixed against a verbatim pass)
- `trim.json`: removed and kept source ranges

Fonts are stand-ins (Bebas Neue, Barlow Condensed, DM Sans, JetBrains Mono from Google Fonts). The anastrozole label, lab order rows and graph curve are illustrative depictions, not real data.

## QC done
- **Transcript:** the edited cut was re-transcribed. All words match the caption list; "At the end of the day", "Your fix" and "E2" were confirmed with a separate verbatim pass.
- **Visuals:**
  - stills at every scene
  - an overview every 1.5 s of the final file
  - 12-frame strips at the hook exit, split-screen entry, split → bubble, bubble → full, symptom exit / dashboard entry, and evidence → CTA
- **Fixes made during QC:**
  - PIL ignored alpha on text and fills drawn onto RGB frames, so fades popped and fills went solid. Text now goes through an alpha layer.
  - The caption dropped onto the T → E2 graphic during the split → bubble handoff.
  - The graph lingered over the face during the bubble → full handoff.
  - The hook and the topic band overlapped in their crossfade (the band now enters after the hook is gone).
  - The "E2 ▲ HIGH" tag collided with the bubble.
  - The dial verdicts landed 2 frames before the cut (they now swing on "conversion").
- **Audio:** −14.4 LUFS integrated, true peak −1.3 dBFS. SFX are placed by word times. I have not listened to it.
- **Not done:** listening. The cover frame (frame 0) catches Coach AGZ looking down mid-word, so pick a custom cover in Instagram.
