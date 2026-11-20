# Full test 02: "Heart health on cycle" (ezetimibe + telmisartan), 1080p

**Source:** Drive `1M80U7LkVqeSsQ0a-yHFn_BQSDNNEE4xO` ("Hook 1 heart Health", 1080×1920 HEVC, 60 fps, 2:02, one continuous car selfie take).
**Output:** `coach-agz_heart-health_1080p.mp4`: 1080×1920, 30 fps, H.264 High + AAC, faststart (plays and saves on a phone), 1:56, about −14 LUFS.
Delivered to the same Drive folder as the source.

## Cut
- One clean take, so no retakes to remove. 27 dead-air pauses (−28 dB, ≥0.22 s) trimmed to about 0.12 s each: 5.97 s removed. Frame-aligned cuts with 8 ms length-preserving audio crossfades (`segments.json`).
- The cut was re-transcribed: every word survived. Caption fixes: "azetomibe/Azetamide" → EZETIMIBE, "Telmesartan" → TELMISARTAN, "APOV" → APOB, "6 p.m." → 6 PM.

## Text hook (TEXT_HOOK_ENGINE.md)
Winner: **"2 compounds protecting / your HEART on cycle"** (premium, HEART in v-gold, frame 0 to 5.3 s). Runners-up and flags are in `edit_log.json`.
Then the topic band ("Your HEART on cycle" plus a chapter chip) shows until the 0:58 midpoint and hides whenever a graphic layout takes over the top of the frame.

## Overlay variety (feedback: no repeating one overlay type; keep the face recognizable)
No full-frame blur or dark push over the face on talking-head beats. Graphic-heavy beats use one of three layouts that keep the face visible:
**lift** (footage slides up 480 px, a deck rises under the chin), **PiP right / PiP left** (the face moves into a gold-framed card while a diagram fills the frame), and **talk** (overlays sit in rails and strips around the face).

| Time | Overlay type | Layout |
|---|---|---|
| 0:00 | Text hook | talk |
| 0:03 | Health-plan checklist rail: estrogen ✓, prolactin ✓, lipids ✕, BP ✕, UNMANAGED | talk, left rail |
| 0:08 | ECG monitor strip, beats then flatline on "quietly", NO WARNING SIGNS | talk, chest strip |
| 0:12 | Two redacted compound cards → MECHANICS / SIMPLIFY / OPTIMIZE stepper | talk |
| 0:19 | Chapter slab 01 LIPIDS | talk |
| 0:21 | Animated bar chart: HDL crashes, LDL and ApoB climb | lift |
| 0:26 | Dual line chart: physique vs CV risk, WHAT YOU SEE / WHAT YOU DON'T | lift |
| 0:30 | Ezetimibe file (redaction lifts) + intestine cross-section: NPC1L1 gates blocked, absorption meter drops, liver pulls LDL | PiP right |
| 0:41 | Big-stat tiles LDL ↓ APOB ↓ | talk |
| 0:44 | Chapter slab 02 BLOOD PRESSURE | talk |
| 0:48 | Pressure gauge into red, workload meter, LV cross-section wall thickens | lift |
| 0:54 | Compound file lower third, TELMISARTAN un-redacts, ARB | talk |
| 0:58 | AT1 lock-and-key (Ang II bounces off), vessel relaxes, BP trend falls | PiP left |
| 1:04 | Tilted clinical-study document with highlighter sweep + LV mass shrinking | talk |
| 1:10 | "That is huge": 112% punch-in, screen held clear | talk |
| 1:13 | Stacked bonus chips: insulin sensitivity, androgen receptors (some studies), part 2 | talk |
| 1:20 | Two-column compare: ezetimibe vs telmisartan | lift |
| 1:29 | Priority re-rank: bigger / stronger / looks struck, HEART to #1 | talk, left rail |
| 1:39 | Analog clock to 6:00 PM, EVERY DAY (calm beat, room left around it) | talk |
| 1:43 | End card: logo, cardiovascular bloodwork breakdown, checklist, COMMENT "HEALTH", disclaimer | lift |

Handoffs: redacted compounds at 0:12 un-redact on their own file cards; the LV ring from 0:48 returns shrinking on the study at 1:08; chapter slabs collapse into the top-band chip.
Palette: test-06 high-pop overlay palette with bloom. Footage is not graded.

## Sound
`sfx.py` synthesises 66 clinical cues (sub hits, scan sweeps, digital ticks, ECG beeps and a flatline tone, impacts on the compound reveals and the CTA), each placed on its visual landing. Mixed under speech; final loudness-normalised.

## QC done
- Stills reviewed across every scene; fixed chapter-slab/caption collision, chart label overlaps, ezetimibe diagram overlapping the PiP, rank-card overflow.
- Found and fixed a compositing bug where PIL ignored text alpha on RGB frames (faded text stayed on screen); translucent text now goes through a layer.
- See the final frame-strip and sync checks in the chat report.
- **Not done:** listening. Values on charts are illustrative (no numbers were invented; charts show direction only). Fonts are stand-ins (Bebas Neue, Barlow Condensed, JetBrains Mono, DM Sans).
