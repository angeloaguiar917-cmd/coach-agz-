# Reel: "Anavar vs beer" — 50 mg Anavar daily vs a six-pack every night (native 1080p + phone copy)

**Source:** Drive file `1EOCULdSPB2BSxxZTLRt1kkOW6Jg7eWRU`, 1080×1920 HEVC 60 fps, 0:46.3, car selfie, one in-camera jump cut (15.9 s).
**Output:** `coach-agz_anavar-vs-beer_1080p_phone.mp4`, 1080×1920, 30 fps, two-pass ~2.5 Mbps (phone-sized), plus the CRF 16 master `coach-agz_anavar-vs-beer_1080p_master.mp4` (34 MB). Checks: 1,353 frames decode, −14.3 LUFS, peak −1.7 dBFS; phone copy 15 MB; QC sheet of 14 frames from the phone file.

## Order of work
1. **Audio:** voice in both channels (−26 dB RMS each), no clipping. Channels kept as recorded (`fix_audio.py ... keep`), mastered to −14.2 LUFS.
2. **Cut** (`trim.py`): the 2.7 s pause after "so…" (34.6–37.6 s) trimmed to a ~0.6 s comedic beat before "maybe I'm just a big dumb bodybuilder"; the 0.5 s gap at 23.6 s tightened. 45.1 s including the 1.3 s end hold. The cut was re-transcribed to confirm the splices.
3. **Transcript:** windowed medium.en; the "so… maybe I'm just…" stretch re-timed with medium.en and small.en word timestamps (the long pass had placed "maybe I'm" inside the silence).
4. **Text hook engine** (`edit_log.json`): **50mg ANAVAR vs 6 beers / the real health cost**. Runners-up "ANAVAR vs a six-pack / worse for what", "50mg ANAVAR daily / your bloodwork timeline".

## Overlay set (brand neon: v-gold, v-red, cyan, green, amber on deep navy; every format different, and different from the gram-vs-sixpack Reels)
| Time | Speech | On screen |
|---|---|---|
| 0–6 | 50 mg Anavar vs a six-pack | Frame-0 text hook, punch-in on "Anavar" |
| 6.1–11.6 | cholesterol profile vs liver, cancer, CV, more | Two columns: capsule + HDL/LDL see-saw tipping (cholesterol profile worsens) vs beer can + three risk gauges needling up, + MORE |
| 11.6–15.9 | both carry real consequences; TRT clinic | Balance scale that settles level (capsule vs can), REAL HEALTH CONSEQUENCES, "the clinic said…" bubble struck through |
| 16.0–21.7 | worse for what, how long, whom | WHICH IS WORSE? struck through, then three icon tiles: target WHAT?, hourglass HOW LONG?, person WHOM? |
| 21.7–34.1 | bloodwork every 4–6 weeks vs 5–10 years | Swimlane timelines: Anavar lane with test tubes across the year; beer lane with one test 5–10 years ago, "nothing since", liver alert, UNTIL THE LIVER SPEAKS UP |
| 34.2–37.6 | "so… maybe I'm just a big dumb bodybuilder" | Left clean for the comedic beat |
| 37.7–end | CTA | End card: FULL BLOODWORK BREAKDOWN · ANAVAR document, COMMENT "ANAVAR" gold pill, FREE stamp, disclaimers |

**Content:** overlays show only what Coach AGZ says. No lab values; the arrows and gauge levels are illustrative. Disclaimer plus "not medical advice · work with your doctor" on the end card.
