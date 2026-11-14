# "Masteron & the E2 trap" (1080p30, phone-ready)

**Source:** Drive `1JKTSbw86rvBXs-HciOywZQwFqocepdPy` ("Mast and e2 trap"), 1080×1920 HEVC 60 fps, 2:03.9, already jump-cut by Coach AGZ (indoor → outdoor → car).
**Output:** `coach-agz_mast-e2-trap_1080p30.mp4`. It's 1080×1920, 30 fps, H.264 High, yuv420p and AAC 48 kHz, with faststart so it plays and saves on a phone. Length 2:02.3, about −14 LUFS.

## Cut
- **Stumble removed:** "without any gyno, (no) without skyrocketing". The source already had a hidden cut at 120.58 s; I kept "correctly / without skyrocketing".
- **Pauses tightened:** the two real pauses (17.3 s, 96.1 s). The delivery is otherwise dense, with no other silence of 0.2 s or more.
- **Re-transcribed:** after cutting (442 words). Caption fixes:
  - Mastron → MASTERON, Drustone alone → DROSTANOLONE, CIRM → SERM, mass → MAST, 2 a.m. → 2AM.
  - "fuck" shown as F*CK.
  - "size of mechanics" captioned as **"science and mechanics"** (my best reading; please check by ear).

## Layout rule: the face stays visible
The last full test put a centre panel and a blur over the face. This one tracks the face (OpenCV) and lays every overlay out around it. No overlay covers the eyes or mouth, and the footage is never blurred behind a graphic.
- **Deck:** the footage slides up until the forehead meets the band, and a graphic deck rises below.
- **Side card:** the footage shifts sideways and a vertical card slides in on the other side.
- **PiP takeover:** a framed face window with the chart below.
- **Rail and upper strips:** used for the small beats.
- **Footage:** no grade or saturation change, per the standard.

## Overlay map (each type used once)
| Time | Type | Layout |
|---|---|---|
| 0:00 | Text hook "MASTERON hides symptoms / not the E2 number", then the topic band until 1:00.6 | Top |
| 0:03 | E2 thermometer filling, RISING / UNFELT tags | Left rail |
| 0:08 | Dual-line graph: E2 on bloodwork rising vs. sides felt flat, the gap hatched HIDDEN | Deck |
| 0:24 | PART 01 · MECHANISM chapter marker (gold rule extends) | Strip |
| 0:27 | Compound file: steroid ring schematic draws on, DHT-derived, aromatizes ✕, water 0, lean-look checks | Side card (right) |
| 0:36 | Two-lane mechanism: AI blocks aromatase (stopped) vs. Masteron (running), "NOT AN AI" stamp + impact | Deck |
| 0:44 | Blood vs. tissue: E2 particles bounce off a receptor shield; sides meter drops, systemic E2 meter rises | Deck |
| 0:52 | Twin spectrum gauges (bloodwork HIGH, felt LOW), BLIND SPOT bar | Deck |
| 1:00 | Timeline chart: block band ends at LAST PIN, E2 stays high, symptoms spike "all at once" + impact | PiP takeover |
| 1:14 | E2 control window bar: BEFORE (green) / AFTER = LATE (red) | Upper strip |
| 1:18 | Step 01: lab order document, sensitive E2 bracketed, "BEFORE LAST MAST PIN" stamp, CLEAN READ | Side card (left) |
| 1:27 | Step 02: Masteron clearance decay curve, THE LAG span, sides rise late, "react here = behind" | Deck |
| 1:37 | Step 03: E2 PLAN checklist vs. 2:00 AM clock with symptom ✕ list | Deck, two columns |
| 1:50 | Bloodwork roadmap: dashed route through panel nodes to a pin | Upper strip |
| 1:52 | CTA: logo, free exit plan (full panel ✓, titration plan ✓), COMMENT "MASTERON" | Deck end card |

## Sound
Synth clinical SFX (sub hits on layout entries, scan sweeps on draws, ticks on rows, three impacts with a 3-frame shake). Speech is loudness-normalised and the mix is about −14 LUFS. Not listened to.

## QC done
- **Stills during build:** 28 stills plus a second pass after fixes.
  - Fixed: the deck pushed the eyes behind the topic band, the compound card overflowed, the stamp covered the diagram, a red blob sat behind the PiP, labels collided on the lag and off-cycle graphs, and the watermark overlapped the top strips.
- **Final file:**
  - Overview every 2 s.
  - Frame strips at every hard layout change (7.97, 27.53, 60.6, 71.27, 78.17 s), the three impacts (39.84, 69.88, 112.84 s), the CTA entry and the render-chunk seams.
  - All clean, and no face covered.
- **Encode:**
  - 1080×1920 30 fps, H.264 High at about 6.4 Mbps, AAC 192k, faststart, 98 MB.
  - SSIM 0.991 against the CRF-16 master.
- **Known soft spot:** 0:52.6–0:53.3, where the READOUT deck is up for about 0.7 s before the first gauge appears.

## Not verified / placeholders
- Graph shapes and lab-order rows are illustrative (no real values shown).
- Fonts are stand-ins (Bebas Neue, DM Sans, Barlow Condensed, JetBrains Mono).
- No listening pass.

## Build
`assemble.py` → `assembled.mov`. Then `face.py` → `faces.json`. Then `render.py <workdir> chunk n0 n1 out.mp4` (4 chunks). Then `sfx.py`, and finally the mux.
