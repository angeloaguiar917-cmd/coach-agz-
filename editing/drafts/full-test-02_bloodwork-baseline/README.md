# Full test 02: "Online protocols / zero data on you" (1080p30)

**Source:** Drive `1Ijl8wEUSXqbeEvCmi3fkUWZi8sflEJ2t` (1080×1920 HEVC, 60 fps, 1:46, one take in the car).
**Output:** `coach-agz_bloodwork-baseline_full-test-02_1080p30.mp4`: 1080×1920, 30 fps, H.264 High + AAC, faststart (plays and saves on a phone), 1:43.9, −14.2 LUFS, peak −1.2 dBFS, 82 MB.

## Brief
Use a different overlay type for each beat (feedback: earlier edits repeated the same gold-bracket panel). Keep the face recognisable, so no full-frame blur behind graphics. Add graphs and more vibrant graphics, all in the brand palette.

## Cut
No retakes or stumbles. 14 dead-air trims of 0.24 s or more, 2.3 s in total, with 8 ms crossfades (`trim.json`). The punch-in alternates 100/107.5% at every cut.

## Overlay types (each used once except split/full, whose content differs)
| Time | Line | Overlay type | Graphic |
|---|---|---|---|
| 0:00 | Hook | Frame-0 text hook (TEXT_HOOK_ENGINE) | Online PROTOCOLS / zero data on you |
| 0:05.8 | "dressed up in confidence" | Floating glass card, left | Bar meter: CONFIDENCE fills to 100%, DATA ON YOU flat at 0%, MISMATCH |
| 0:07.7 | "no idea what your bloods look like…" | HUD scan on the face plus a readout list | Cyan tracked brackets, 7 marker rows tick in as spoken (all ???), scan line sweeps, anomaly blip, rising risk sparkline |
| 0:23.6 | "made a recommendation… zero data" | Paper document | "Protocol recommendation" slip, UNVERIFIED stamp, DATA INPUTS 0/7 bracketed |
| 0:29.4 | "might work for most guys… 10 times worse" | Full-screen scene, face shrinks into a PiP circle | Bell curve: WORKS FOR MOST band, YOU? pin drops into the tail, 10× |
| 0:40.0 | "two guys, same age…" | Split screen (face top, panel bottom) | GUY A/B match rows, then a divergence line chart: FINE vs CRASHED |
| 0:48.3 | "different enzyme expressions…" | Full-height sidebar (footage reframed left) | Radar chart, 6 axes light up as spoken, then a selector: COMPOUND ✕ / PERSON ✓ |
| 1:05 | "reviewed over 500…" | Top stat card | 500+ count-up with a 500-dot grid |
| 1:09 | "the real pattern…" | Same card (handoff) | The dots gather into a donut: guys who got hurt, 100% flying blind; HCT/LIPIDS/LIVER ▲ |
| 1:18 | "go get your blood drawn first" | Chest strip | 3-step stepper: BLOOD DRAW ✓ FIRST, READ BASELINE, PROTOCOL locked |
| 1:28 | "bloodwork is the roadmap" | Full scene with PiP top-right | Route map through the marker waypoints, OPINION/BRO SCIENCE/GUESS dead ends crossed out |
| 1:34 | CTA | Split screen | BASELINE panel guide sheet ticks, COMMENT THE WORD "BASELINE" |

The topic band (with a "500+ panels reviewed" proof chip) runs from the end of the hook to the midpoint and hides during full-screen scenes. Footage is ungraded.

## QC done
- Hook engine run first: see `edit_log.json`.
- Captions are built from a medium.en transcript of the trimmed cut. A split "physiology" was merged, and "That" was restored at 1:33.9.
- Stills were checked at every scene, plus a 2 s overview of the final render. Fixes made: captions over the mouth in split mode (moved to the seam), the chart label hitting the rows, the sidebar title clipping, labels showing before their cue (a Pillow alpha-0 text quirk), and frosted plates not fading with their content.
- Not done: listening to the mix by ear, and frame-by-frame checks of every transition.
- Graph shapes (bell curve, radar values, divergence lines) are illustrative. The only numbers shown are ones the video says (0, 10×, 500+, 100% "every single time"). Fonts are stand-ins.

Build: `assemble.py` steps are in `render.py`'s header. Render with `python3 render.py <workdir> <fonts> <f0> <f1> out.mp4`; SFX with `sfx.py`.
