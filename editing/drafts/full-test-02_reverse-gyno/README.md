# Full test 02: "3 steps to reverse gyno" (1080×1920, 30 fps)

**Source:** Drive `1Tt6_B_dkgFsGB1g886ZXEb12rQjOG-Fa` (1080×1920 HEVC, 60 fps, 2:40, a single car selfie take).
**Output:** `coach-agz_reverse-gyno_1080p30.mp4` (uploaded to Drive; too large for git). 1080×1920, 30 fps, 2:32.5, H.264 High plus AAC, faststart, for phone playback and download.
**Status:** a full edit in the test-06 / full-test-01 style. Fonts are still stand-ins.

## Brief from Coach AGZ (2026-11-15)
- More variety in overlay types. Don't repeat one overlay type.
- Keep the face recognisable.
- Graphs, more graphics, vibrant colour that matches the brand.

## What changed from full test 01
- **The face is never covered.** In test 01, every scene blurred and darkened the whole frame behind a panel over the face. This edit rotates five layouts, and the face stays visible in all of them:
  1. **Normal:** the footage as shot, with on-footage tags.
  2. **Split:** the footage slides up so the face sits in the top half. A graph panel fills the bottom. The face is tracked with OpenCV, and its position is held steady for each scene.
  3. **Circle window:** a full graphic scene, with the live face in a gold circle at the top centre.
  4. **Rectangle window:** the live face in a top-right window, with content on the left and below.
  5. **Top card:** a frosted card in the empty headliner space above the head. The footage stays untouched.
- The footage morphs between layouts (scale, position and mask animate together). That's the handoff between scenes.
- No colour grade on the footage. Vibrance goes on the overlays only.

## Overlay types used (eleven)
| Time | Line | Layout | Overlay type |
|---|---|---|---|
| 0:00 | Hook | normal | Frame-0 text hook (TEXT_HOOK_ENGINE), then a topic band until the midpoint |
| 0:02 | "nipple's been sore… poking… shower" | normal | Chest scan brackets, a 7-day "days sore" strip and action tags |
| 0:08 | "best time to reverse… surgical" | split | **Line graph**: reversibility over time, with a YOU · NOW marker, protocol window, fibrotic zone and SURGERY ONLY slam |
| 0:20 | "soft, tender, glandular… hard and fibrotic" | circle | Tissue scan comparison: glandular lobules shrink (REVERSIBLE) against a fibrous mass (NO PROTOCOL, then SURGERY) |
| 0:31 | "three steps" | top card | A 3-step roadmap rail. Its mini stepper carries into each step scene. |
| 0:36 | Step 1: find the driver | split | **Decision-flow diagram** (TRT / other anabolics / NPP-Deca to E2 or prolactin), then a lab order with tick boxes and a PULL FIRST stamp |
| 0:54 | Step 2: correct, don't crash | top card | **Spectrum gauges** for E2 and PRL. Markers slide into range, then E2 is NUKED TO ZERO and cost chips appear (dead joints, no libido, flat mood). |
| 1:12 | Step 3: treat the tissue | rect window | Receptor schematic (a SERM docks, E2 is BLOCKED; Raloxifene and Nolvadex tags), then a **dosing bar chart** (W1–2 at 2×, W3–6 at 1×) |
| 1:35 | Client privacy | split | A client file with redaction bars, POSTED = FOREVER, and a CONFIDENTIAL stamp |
| 1:50 | Client case | small circle | A **big stat** (E2 counts up to 120), a FELT FINE chip and a lump chip, then a **combo chart** (E2 line into range plus lump bars shrinking to GONE · 4 WKS). Marked illustrative. |
| 2:07 | MENT | top card | A hazard label, an aromatization meter pegged off the chart, and a DON'T KNOW IT · DON'T RUN IT slam |
| 2:14 | CTA and recap | split | Logo, free protocol, a COMMENT "GYNO" slam, then a 4-item recap checklist and a BLOODWORK = THE ROADMAP bar |

## Cut
- A single take, so no retakes needed cutting. 31 pauses of 0.2 s or more were trimmed to about 0.12 s (7.4 s removed), with frame-exact cuts selected by frame index.
- Every cut sits inside a silence detected at −32 dB, so no speech was removed.
- Punch-ins of 108% alternate at each cut on talking-head shots.

## Captions
- Word captions come from a vocabulary-prompted Whisper medium.en pass.
- Corrections: "antibiotics" → anabolics (×2), "in a bollocks" → anabolics, "relax if een" → Raloxifene, "nova deck" → Nolvadex, "ment / men" → MENT, "a robot eyes is" → aromatizes, "a hundred and twenty" → 120.
- "I was" before "step three" is unclear in the audio, so those two words are left uncaptioned.
- Accent words (GYNO, E2, prolactin, SERM names, MENT, bloodwork) show gold when they aren't the active word. Danger words (surgical, zero, hard, fibrotic, 120) show red.
- In split and window layouts, captions move up to the seam under the face.

## QC done
- Re-transcribed the trimmed cut against the source: 585 words against 588. The differences are Whisper variance on "MENT" and "comment the word".
- Caption timing drift against the trimmed transcript: median 0.01 s, p95 0.05 s.
- Video and audio length: 152.53 s each.
- Stills inspected across every scene. Fixed during the build:
  - Panel content was too small (bottom third empty), so every panel scene was enlarged.
  - The chest tag collided with the captions.
  - The LIVE label collided with the captions and the header.
  - The "nuked to zero" tag overlapped the title.
  - The YOU · NOW tag overlapped the axis label.
  - The CTA crossfaded into the recap too early.
- **Not done:** listening (the SFX are synthesised: scan sweeps, sub thuds, ticks and impacts). Please check the mix by ear.

## Placeholders and flags
- The lab order, client file and case chart are illustrative. The case chart is labelled ILLUSTRATIVE. The E2 value of 120 and "gone within 4 weeks" are as spoken. No units or doses were added.
- The step labels on the roadmap ("find the driver", "correct it", "treat the tissue") paraphrase the spoken steps.

## Files
- `render.py`: the frame renderer (layouts, scenes, captions, hook).
- `sfx.py`: synthesised SFX.
- `edit_log.json`: the text-hook engine output.
- `trim.json`, `words_final.json`: the cut and the captions.
