# HGH / carpal tunnel: "Why HGH numbs your hands" (1080p)

**Source:** Drive `1qOH6RUCFto9htVJlQhdLiGsNha34Od0S` ("Carpal Tunnel HGH", 1080×1920 HEVC, 60 fps, 1:42). It was already jump-cut, with no gap over 0.4 s, so the cut is kept as supplied.
**Output:** `coach-agz_hgh-carpal-tunnel_1080p30.mp4`, 1080×1920, 30 fps, H.264 High, yuv420p, AAC 192 kHz stereo, faststart (plays and saves on iPhone and Android). Mastered to about −14 LUFS.
**Style:** the full-test-01 setup (test-06 overlay palette, every-word Bebas captions with the red lit word box, gold left rule, bloom). The footage is not graded.

## Overlay variety (feedback: don't repeat the same overlay type)
Each beat uses a different layout and a different graphic type. Your face stays in frame for the whole Reel: the window shrinks or moves, but it never goes behind a full panel.

| Time | Layout | Graphic type |
|---|---|---|
| 0:00–0:06 | Full frame | Frame-0 text hook (native box), from `edit_log.json` |
| 0:06–0:14 | **Face bubble** + full-screen graphic | Body schematic: wrist pin, dashed signal path to the kidneys ("ORIGIN ?"), then a 3-node method rail |
| 0:14–0:28 | **Split screen**: face window on top, graphic below (morphs out of the bubble) | Kidney HOLD/FLUSH valve with Na+ ion stream; GH and IGF-1 tags; **Na+ HELD bar graph** 50→86%; then a tubule-wall view where the ENaC gates open, sodium crosses and water follows; FLUID bar |
| 0:28–0:47 | **Portrait face card** + side diagram | Hand X-ray (numb fingers pulse red, scan line, CARPAL TUNNEL bracket); cross-section where 9 tendons count in with a big counter, then the median nerve lands; median-nerve finger map (thumb, index, middle, half the ring finger) with the pinky marked ULNAR NERVE |
| 0:47–0:56 | Full frame + **top card** above the head | Mini cross-section (ligament goes rigid, fluid swells, nerve flattens and turns red, blood-flow dots stop) next to a **nerve pressure line graph** crossing the NERVE LIMIT line; then TINGLING, NUMBNESS and GRIP chips and a falling grip-strength meter |
| 0:56–0:59 | Full frame, clean | Breathing room for the "flopping around" line |
| 0:59–1:06 | Full frame + floating icons (no panel) | Stepper: Na+ → water drop → nerve between closing walls, squeezed, with an impact |
| 1:06–1:14 | Split screen | Risk mixer: FLUID / NERVE SENSITIVITY / GH DOSE sliders driving a **symptom-risk gauge** into HIGH |
| 1:14–1:26 | Face bubble | **GH dose titration line chart**: HIGH (NUMB/TIGHT markers), DROP (stepped), STABILIZE band, REBUILD steps to the dashed **4 IU** target |
| 1:26–1:29 | Full frame | Small amber CHECK warning light that blinks on "attention" |
| 1:29–1:33 | Full frame | Green protocol checklist: titrate slow, sodium + water, watch symptoms |
| 1:33–1:42 | End layout: face window + CTA card | Logo, FREE · FULL GH PROTOCOL, COMMENT "GH" bar lands on "comment", disclaimer |

The layouts morph into each other (bubble → split → card → full) instead of hard-swapping, as the "make it connected" rule asks.
The topic band "Why **HGH** numbs your hands" runs from the end of the hook to the 0:46.9 jump cut, the one nearest the midpoint.

## Captions
- Built from a turbo-model transcript, checked against a second (medium) pass.
  - Word timing agreement: median 0.04 s, p95 0.10 s.
  - Three sentence-start words were moved to the medium-pass onset.
- Corrections: "science and mechanics", "titrate the dose back up to about 4 IUs", "titrate slow", "pinky", "IGF-1".
- Accent words recolour gold once spoken (HGH, GH, IGF-1, kidneys, sodium, carpal tunnel, median, 4 IU).

## Values shown
- The only number on screen that you say is **4 IU**.
- The Na+ HELD and FLUID percentages, the pressure curve and the dose-chart shape are illustrative. The dose chart is labelled "illustrative shape".
- The anatomy matches what you say: 9 tendons plus the median nerve; thumb, index, middle and half the ring finger. The ulnar label on the pinky is the anatomical reason the pinky is spared.
- **ENaC** is named as the "tiny sodium channels". Change it if you'd rather keep that generic.

## Not done / limits
- Cutout "text behind head" was tried and dropped: the segmentation can't separate the black cap from the black headliner (`qc` showed a blob eating the text).
- Fonts are stand-ins (Bebas Neue, DM Sans, JetBrains Mono, Barlow Condensed).
- Not listened to: SFX sync was placed by timestamp only. Please check the mix by ear.

Build: `render.py <scratch> frames n0 n1 out.mp4` (reads a 30 fps intermediate of the source); `sfx.py out.wav`; audio is loudnorm (−14) + SFX, limited.
