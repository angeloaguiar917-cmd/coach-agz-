# Reel: "Can 25mg Tren.hook" — Tren microdosing, question opening (native 1080p + phone copy)

**Source:** Drive file `1LLf9WBj_Y72QRIVwaVd1H1PZYNk3h7MV`, 1080×1920 HEVC 60 fps, 1:58.1. It's the fourth take of the micro-Tren script, with a new opening ("could running 25 mg of tren give you some of the upside without the nightmare of the 400 mg…"). The source has its own cut at 63.2 s.
**Outputs:**
- `coach-agz_25mg-tren_1080p_phone.mp4`: 1080×1920, two-pass ~2.5 Mbps, about 40 MB. Committed and sent.
- The CRF-16 master stays in the session scratch area (over GitHub's 100 MB file limit).

## Work
- **Audio:** both channels carry the voice, no clipping, quiet recording. Voice +9 dB, then the limiter: −14.3 LUFS.
- **Transcription:**
  - Gap-guarded windows.
  - The long pass dropped the whole ending (102.7 s on) and misheard "19-nor anabolic". Both were re-transcribed in focus: "…side effects that make Trenbolone so f*cking notorious. That being said… comment the word micro below… appreciate you guys."
  - "so" (104.5 s), which sat on a trim boundary by timestamp only, was restored at the cut point.
- **Cut:** 3 dead-air trims (0.47 s).
- **Text hook:** "**25 MG** of **TREN** / all upside no nightmare" (`edit_log.json`). The first draft line was 28 characters, so it was tightened to meet the 26-character rule.

## Overlays
Eleven formats, with no style repeated back to back.

**New for this take:**
1. **VS card** (6.0–8.1 s): 25 MG · UPSIDE ▲ vs 400 MG · NIGHTMARE ✕. It sits under the topic band, clear of the face and the bottom UI zone.
2. **Car dashboard** (8.2 s): an LED dose counter clicks 400 → 500 → 600 over a ghost "888", a gradient redline bar fills, and four warning lights come on as each side effect is named. Lights 3–4 are red, and they pulse.
3. **Area-to-scale dose bubbles** (83.6 s): a red 600 circle against a gold 25–50 circle sized by area, replacing the dose tube.

**Carried over from take 3 / micro-Tren v2:** evidence full-screen scene (10+ ring, report sheets, 500+), 19-nor molecule strip, dose-response curves, sleep-tracker card, DNA card, rating gauges with receptor docks, activation donut, the 600 vs 25–50 radar chart, and the struck-out side-effect callback.
- These are re-timed onto this take by word alignment against `prev_take_words.json` (351 anchors).
- Graphs are shape-only and marked ILLUSTRATIVE. Every number is Coach AGZ's own.

## Checks done
- **Full decode:** 3,569 frames at 1080×1920, for both the master and the phone copy (39.5 MB).
- **Frames:** strips at the hook exit, the VS card out, the dashboard in and out, the evidence scene out, the molecule strip, the bubbles, the radar build and the end card.
- **Fixed in review:**
  - The VS card first sat in the Instagram bottom UI zone, then over the mouth. It's now under the topic band.
  - The hook line was over 26 characters.
- **Sound sync:** all 12 heavy hits within 2 ms of their frames. −14.4 LUFS, peaks −1.9 dBFS. No music. Not listened to.

**Not done:**
- Listening.
- Subject cutout.
- Real fonts (stand-ins).
- `winners.md`.

---
## Variant B (A/B test): `coach-agz_25mg-tren_1080p_phone_B.mp4`
Coach AGZ asked for a version with **totally different overlays** and the hook "**25 MG** vs **400 MG** / the real **TREN** difference", to test on Instagram trials. The cut, captions, audio mix level and timing are identical to variant A, so the test isolates the hook and the graphics. Built by `render_b.py`; its edit log is `edit_log_variant_b.json`.

**Visual language:** no frosted panels, no gold corner brackets, no panel headers. Instead: full-screen data scenes over the pushed-back footage, kinetic type, free-floating graphics, a lower-third and a diagonal end card. There's a new accent set (mint, hot pink, lime, sky) alongside the brand gold. The topic band hides during full-screen scenes.

| Time | Variant A | Variant B |
|---|---|---|
| 6.0 s | VS card | **Balance scale**: the 400 MG weight crashes its side down, 25 MG rises (UPSIDE / NIGHTMARE) |
| 8.2 s | Dashboard + warning lights | **"THE OLD WAY" step-area chart**: the dose climbs 400 → 500 → 600 as a glowing pink step line with area fill; red forensic tags snap on for each side effect |
| 20 s | Report-sheet scene | **Kinetic type**: 10+ YEARS / COACHING / ANECDOTAL / + CLINICAL / **500+** / BLOODWORK PANELS slam in from alternating sides |
| 30 s | Molecule strip | **Lower-third bar**: TREN · 19-NOR, "extremely potent anabolic steroid" |
| 33 s | Dose-response curves | **Split-screen**: HIGH DOSE (red half) vs LOW DOSE (mint half), grouped bars for exposure, androgenic and side effects, "SAME SIGNAL?" |
| 49 s | Sleep-ring card | **Clock face** with a 30-minute wedge, "30 MIN OF SLEEP = NO GROWTH" |
| 65 s | Gauges + receptor docks | **Bar race** TEST 100 vs TREN 500 with a **5×** stamp, then **orbit diagrams**: ligands spiral onto the androgen receptor (affinity) and the glucocorticoid receptor (ANTI-CATABOLIC) |
| 84 s | Bubbles + donut + radar | **"THE NEW WAY" dose slider**: the handle slides from 600 into the 25–50 zone; **triple activity rings** fill for partitioning, nitrogen and fat oxidation; an empty red **0** ring for the notorious sides |
| 106 s | Centred logo + gold pill | **Diagonal split end card**: MY FULL TREN MICRODOSE PROTOCOL on navy, a giant **MICRO** keyword on gold, SENT TO YOU · FREE |

**Sound:** 45 cues (one whoosh and a sub thud per scene, ticks on data, impacts on the 500+ and 5× stamps). Same voice gain as A.

**Variant B checks:**
- **Decode:** 3,569 frames at 1080×1920, 39.4 MB.
- **Audio:** −14.4 LUFS (same as A), peaks −1.9 dBFS. All 11 heavy hits within 2 ms of their frames.
- **Frames:** strips at every scene in and out, the lower-third, the end-card build and the keyword stamp.
- **Fixed in review:**
  - Scene titles collided with the topic band (the band now hides during scenes).
  - The balance scale was too small and overlapped the band.
  - History tags were undersized.
  - The activity rings merged into one blob.
  - The clock labels were unreadable over the face.
  - The TEST value was dark-on-dark.
