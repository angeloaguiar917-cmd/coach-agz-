# Reel: Tadalafil, "the underrated compound" (1080p final candidate)

**Source:** Drive `1gEMiIqvnFhJ2gXxqyztmakzkyedwIXVs` ("Tadalafil"), 1080×1920 HEVC, 60 fps, 1:40.5, one continuous walking take (turns a corner at about 0:47; no retakes).
**Output:** `coach-agz_tadalafil_1080p30.mp4`. It's 1080×1920 at 30 fps, 1:38.9, H.264 High@4.2 with yuv420p, AAC 256k and faststart (phone-safe), 67 MB. Loudness is −14.3 LUFS and the peak is −1.4 dBFS.

## Cut
- 8 dead-air gaps of 0.24 s or more trimmed (1.5 s removed in total), with 8 ms audio crossfades. `cut.json` holds the keep ranges; `cut.py` builds `assembled.mov`.
- The delivery was already tight: no stumbles or retakes were found in a filler-preserving pass.
- Punch-in: lands at 108% on "Tadalafil" at 0:00.84, then alternates 100/108% at every jump cut.

## Text hook (engine run, see `edit_log.json`)
"Your blast is missing / 5mg **TADALAFIL**". Native mode, frame 0, held to 5.3 s, 0.15 s fade. Then the topic band ("**TADALAFIL** the underrated compound") runs until the midpoint, and is hidden during the full-screen and split-screen scenes.

## Overlay map: a different overlay type on every beat
| Time | Line | Overlay type | Layout |
|---|---|---|---|
| 0:01 | "Tadalafil… underrated" | Rx bottle label (5 MG, PDE5 inhibitor) with red UNDERRATED brackets | Floating object, upper left |
| 0:05 | blast / AI / bloodwork / missing one piece | **Protocol stack builder**: 3 cyan slots tick ON, then a pulsing red "?" slot (MISSING), and boost beams into every slot | Sky strip, face clear |
| 0:13 | Tadalafil or Cialis… cardiovascular… billions… went that route | **Full-screen timeline** (navy/gold carousel look) with the speaker in a PIP. "BEDROOM ONLY" struck FALSE, 4 nodes, a $ ticker that lands on $ BILLIONS, and a REBRANDED stamp with a camera kick | Full screen |
| 0:27 | PDE5 inhibitor, opens vessels, keeps them open | **X-ray vessel cross-section**: the lumen widens, PDE5 is INHIBITED, and a hold meter fills (OPEN · HELD · LONG-ACTING) | Frosted cyan evidence panel |
| 0:33 | vasodilation → delivery; creatine, aminos, carbs | **Split screen**: the face moves to a top window, the vessel widens, nutrient chips flow into the muscle cell (DELIVERED), and a delivery gauge goes BASELINE → AMPLIFIED | Split |
| 0:45 | higher doses, stacking, heart and prostate, stress… Tadalafil reduces strain | **Line graph**: a red stress curve plots per step, with a CONSTANT STRESS flag, a dashed green "+ TADALAFIL" curve, and HEART/PROSTATE strain meters that drop on "reducing" | Charcoal card with a crimson bar |
| 0:58 | not a fix for reckless protocols… layer of protection | **Two-column comparison** sliding in from both sides: RECKLESS gets NOT A FIX; OPTIMIZED gets protection layers stacking plus ✓ optimized and ✓ intentional | Twin cards |
| 1:05 | year-round, low dose, 5 mg daily, vascularity, pumps, recovery | **Big-stat slam** "5 MG" with a camera kick, a 12-month calendar strip filling, and 3 benefit bars | Full-bleed type on the push |
| 1:14 | prostate markers stay in range even when others are elevated | **Lab report paper** with reference-range spectrum bars: PSA IN RANGE (green brackets); others HIGH | Tilted document |
| 1:18 | serious about long-term… leaving gains and health on the table | **Callback**: the stack from 0:05 returns. Its slot reads NOT USING, GAINS/HEALTH chips fall off, then the slot fills gold (TADALAFIL 5MG DAILY, 4/4 COMPLETE) | Sky strip |
| 1:26 | full labs… comment LABS… breakdown, framework… | **End card**: logo, lab bars, a gold COMMENT "LABS" pill landing on "labs", and 5 deliverables ticking in | Card |

Captions: every word in Bebas, with a red block on the active word. Key terms get accent colours (Tadalafil/5 mg gold, heart/prostate/stress red, PDE5/vasodilation cyan, billions green).

## QC done
- **Captions:** the final file was re-transcribed. 357/360 words match; the 3 differences are transcriber variance ("five" vs "5", spelling). Drift: median 0.00 s, p95 0.02 s.
- **Visuals:** stills at every scene, plus 10 fps strips around all 10 scene transitions. Two layout passes fixed overlays covering the mouth on the second location, tag collisions, and the PIP covering the title.
- **Sound:** 7 heavy hits were measured within 1 ms of their target frames.
- **Not done:** listening to the mix (no audio playback here).
  - Graph shapes are marked ILLUSTRATIVE.
  - Lab rows show range positions only, with no values.
  - Fonts are stand-ins.

## Check by ear / eye
- 1:33: the audio is mumbled; both models heard "how to dial if it works". The caption reads "HOW TADALAFIL WORKS"; confirm.
- 1:35: "what the doses used to be" is captioned as spoken.
- The Rx label reads "RESEARCH SUPPLY". Change it if you'd rather it read as a pharmacy label.
