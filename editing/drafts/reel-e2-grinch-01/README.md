# Reel: "E2 Grinch" — getting emotional on cycle isn't automatically high E2 (native 1080p + phone copy)

**Source:** Drive file `1LVYHNxKPrhz-4OgxNEZ-s4a1JyusAyn8`, 1080×1920 HEVC 60 fps, 1:49.9, car selfie, single take with three in-camera jump cuts (24.1, 27.0, 92.8 s).
**Output:** `coach-agz_e2-grinch_1080p_phone.mp4`, 1080×1920, 30 fps, two-pass ~2.5 Mbps (phone-sized), plus the CRF 16 master `coach-agz_e2-grinch_1080p_master.mp4` (86 MB). Checks: 3,337 frames decode, −14.2 LUFS, peak −1.9 dBFS, L/R identical; QC sheet of 26 frames from the phone file.

## Order of work
1. **Audio:** voice in the right channel only (left −108.6 dB), 111 clipped samples. Dual-mono at the mix (`fix_audio.py`, pan c1).
2. **Cut:** clean take, no retakes. Only two 0.24 s gaps, left in (pace is already dense). 111.2 s including the 1.3 s end hold.
3. **Transcript:** windowed medium.en; focused re-passes with small.en and medium.en. "below" restored in the CTA ("comment the word E2 below"); "Intelligent Framework" kept as said (both models agree).
4. **Text hook engine** (`edit_log.json`): **Crying over the Grinch / blame your E2**. Runners-up "Emotional on cycle / don't blame E2", "High E2 / doesn't mean an AI".

## Tone: comedic open, then educational
- **0–15 s (Grinch story):** footage only, text hook on frame 0, captions, one punch-in on "Grinch". No graphs, no overlays, no topic band.
- **From "But honestly" (15.05 s):** topic band **E2** is not your enemy, then the deep-vibrant overlay set.
- The camera-in-face close-up (24.1–27.0 s, "Estradiol is not your f*cking enemy") is left clean as a punchline.

## Overlay set (every format different, deep violet/magenta/electric palette)
| Time | Speech | On screen |
|---|---|---|
| 15.1–24.1 | getting emotional ≠ high E2, high E2 ≠ AI | Two cause→effect chains that snap: EMOTIONAL → HIGH E2, HIGH E2 → NEED AN AI |
| 27.0–33.1 | sexual function, brain, bone, muscle | Radial hub: E2 hexagon with four icon nodes |
| 33.1–37.0 | crush it too low | U-curve graph: OPTIMAL band, the dot slides into TOO LOW |
| 37.0–42.7 | over a decade, 500 panels | Floating card: fanned lab sheets, 10+ YEARS, odometer counting to 500+ PANELS |
| 42.7–45.9 | 3-point framework, free | Glowing triangle graph with three nodes, FREE stamp |
| 45.9–51.4 | 1 bloodwork | Lab panel bars (sensitive E2, total T, free T, SHBG) with ratio brackets; mini triangle map |
| 51.4–57.1 | 2 biofeedback | Radar chart: libido, mood, sleep, side effects |
| 57.1–62.4 | 3 performance | Line graph across the day: strength, recovery, mental clarity |
| 62.4–66.6 | business decisions, family | Floating glass tiles with icons |
| 71.1–76.1 | cross-referencing patterns | Venn of the three pillars, PATTERN core, orbiting "other health markers" |
| 76.1–82.9 | one moment, one number, red alert, average guy | Lab report scan (values blanked), snapshot brackets, RED ALERT stamp, NOT A DIAGNOSIS |
| 82.9–92.7 | your biology, pivot, optimize, ratios, nobody's the same | Fingerprint scan with tags, then a grid of prints with YOU highlighted |
| 92.8–end | CTA | Blueprint end card: flagged E2 row, ESTROGEN OPTIMIZATION BLUEPRINT with three checks, COMMENT "E2", disclaimers |

## Caption notes
11-YEAR-OLD, 3-POINT and CROSS-REFERENCING joined; swears starred.

**Content:** overlays show only what Coach AGZ says. No lab values are shown (the report rows are blanked, the bars are illustrative). Disclaimer plus "not medical advice · work with your doctor" on the end card.
