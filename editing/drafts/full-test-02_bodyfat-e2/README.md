# Full test 02: "Body fat & E2 on TRT" (1080p30)

**Source:** Drive `1qSYB-nobpVU2wUSjnwrYLTzr4483UUyE` ("Bf TRTe2 2"): 1080×1920 HEVC, 60 fps, 31.45 s, one clean take in the car.
**Output:** `coach-agz_bodyfat-e2_1080p30.mp4`: 1080×1920, 30 fps, H.264 High (yuv420p) plus AAC 48 kHz, with faststart so it plays and saves on a phone. (Drive upload from the session is capped at 10 MB, so it was sent directly instead.)
**Style:** test-06 overlay palette (vibrant overlays, footage left as shot), brand gold rule, Bebas, Barlow Condensed and JetBrains Mono stand-in fonts.

## Brief for this one
- Use a **different overlay type on each beat**, with no repeated card style.
- **Keep the face recognisable.** Graphics stay in the dark headliner area above the cap and in the side gutters. The only layout change (the graph scenes) keeps the face in an 84% window, not blurred or pushed back.
- Add graphs, more graphics, vibrant and on-brand.

## Overlay map
| Time | Line | Overlay type |
|---|---|---|
| 0:00 | "So why exactly does higher body fat raise estrogen on TRT?" | Frame-0 text hook card, premium (`edit_log.json`) |
| 0:03.8 | "one enzyme, aromatase" | Side **scan widget**: rotating wireframe enzyme, scan line, AROMATASE tag |
| 0:06.4 | "aromatase lives in adipose tissue" | **Microscope lens** over an adipose slide (Voronoi fat cells); aromatase sites light up. Handoff: the enzyme flies into the lens. |
| 0:08.5 | "converts testosterone to estradiol" | **Process flow** T → AROM. → E2 with particle flow. Handoff: the lens shrinks into the hex. |
| 0:10.6 | "higher body fat increases conversion rate" | **Stacked layout** with a **line graph**: the curve draws as he speaks, against a lean baseline, then a RATE ▲ tag |
| 0:13.1 | "independent of the actual dose" | **Bar chart**: SAME DOSE ✓ on both columns, then lean vs higher-body-fat E2 bars |
| 0:15.9 | "water retention, sensitive nipples, emotional volatility" | 108% punch-in, an **E2 dial gauge** swinging into the red, and a **symptom card stack** with icons |
| 0:21.0 | "the labs will confirm it before any protocol change" | **Lab report document** drops in: range markers, CONFIRMED stamp, then the order steps "1 LABS ✓ → 2 PROTOCOL CHANGE" |
| 0:24.7 | "my E2 management checklist absolutely free" | **Freebie mockup**: boxes tick, then a FREE stamp |
| 0:27.8 | "comment the word E2 below" | Gold **COMMENT "E2"** pill, down chevrons, then the logo lockup |

## Notes
- **Burned-in text in the source:** the clip arrived with captions burned in for the whole video, plus a "BODYFAT and Estrogen?" title for 0–4.93 s.
  - A frosted navy caption plate covers the captions for the whole video, and the hook card covers the title. The hook holds to 4.95 s for this reason.
  - Send a clean export (without the app captions) next time and the plate can go.
- **Captions** come from a word-timed transcript of the audio (Whisper small.en): 94 words. They're Bebas, the active word on a red lit bar, with key words recoloured gold or red after they're spoken.
- **Graphs and the lab report are illustrative.** There are no numbers on screen: the curve shape, bar heights and the lab's IN RANGE/HIGH flags depict the point, not real data.
- **QC done:** stills before and after the build fixes; frame strips at every handoff (hook exit, enzyme → lens → flow, restack, graph → bars, labs, card → pill); exact-frame checks of the graph swap; chunk seams compared against the source footage (offset 0); full decode; −14.1 LUFS, peak −2.3 dBFS. **Not done:** listening, so check the SFX mix by ear.
- **Sound:** synthesised clinical SFX (sub hits, scan sweeps, ticks, two heavy impacts on CONFIRMED and COMMENT). Speech is kept at −14 LUFS. There's no music bed.

Rebuild: `python3 render.py <scratch> chunk n0 n1 out.mp4` (needs `<scratch>/src/raw.mov` and `<scratch>/fnt/`), then `python3 sfx.py sfx.wav` and mux.
