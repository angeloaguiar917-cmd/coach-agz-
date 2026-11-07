# Reel: "TRT weekly rollercoaster" — once-a-week injections vs smaller, more frequent shots (native 1080p + phone copy)

**Source:** Drive file `1GcftrF0TvkJafB6GXEaAkFqcorHSM8hY`, 1080×1920 HEVC 60 fps, 1:30.1, three locations (indoor, outside, car) with in-camera cuts at 4.5, 18.7, 21.8 s.
**Output:** `coach-agz_trt-weekly-rollercoaster_1080p_phone.mp4`, 1080×1920, 30 fps, two-pass ~2.5 Mbps (phone-sized), plus the CRF 16 master `coach-agz_trt-weekly-rollercoaster_1080p_master.mp4` (62 MB). Checks: 2,741 frames decode, −14.3 LUFS, peak −1.8 dBFS; phone copy 29 MB; QC sheet of 15 frames from the phone file.

## Order of work
1. **Audio:** voice in both channels (−25.6 dB RMS), no clipping; channels kept as recorded (`fix_audio.py ... keep`), mastered to −14.2 LUFS.
2. **Cut:** clean take, no retakes, no dead air. 91.4 s including the 1.3 s end hold.
3. **Transcript:** windowed medium.en (306 words); "Your" restored before "natural hormone production" (small.en focused pass).
4. **Text hook engine** (`edit_log.json`): **Weekly TRT injections / the hormone rollercoaster**. Runners-up "TRT once a week / your doctor got it wrong", "TRT 3-4x a week / end the rollercoaster".

## Overlay set (brand neon: v-gold, v-red, cyan, green, amber on deep navy; every format different)
| Time | Speech | On screen |
|---|---|---|
| 0–6 | weekly injection advice is terrible | Frame-0 text hook, punch-in on "TRT" |
| 6.1–16.3 | inject Monday, spike Tue/Wed, crash Saturday | Week calendar MON–SUN with an OPTIMAL band: syringe on Monday, curve spikes into WAY TOO HIGH, CRASH by Saturday |
| 16.3–18.6 | not stable, not optimal | Floating tiles STABLE ✕, OPTIMAL ✕ |
| 18.8–21.8 | recipe for feeling like sh*t | Floating recipe card: 1 injection a week, 1 big spike, 1 hard crash; serves most of the week |
| 21.8–28.3 | peaks, body panics, converts to estradiol | Overflow tank past "what the body handles", PANIC light, aromatase pipe into a filling estradiol tank, E2 ▲ |
| 28.4–36.9 | water retention … day 6 irritable, exhausted | Symptom blocks drop and stack while a DAY counter runs to 6; PROTOCOL NOT WORKING? |
| 40.1–45.5 | ride peaks and troughs | A rollercoaster track (three weekly cycles) with a cart riding it, PEAK / TROUGH tags |
| 45.5–52.2 | natural production steady all day | 24-hour dial with a steady green release ring |
| 52.3–57.3 | inject once a week, expect to feel good? | Floating: 1 SHOT · 7 DAYS, only Monday lit |
| 57.3–70.2 | every day ideal; business owners, family men; 3–4x at least | Bar chart of peak-to-trough swing by frequency (1X, 2X, 3-4X, DAILY; illustrative): DAILY = IDEAL, 3-4X = AT LEAST, client chips |
| 70.3–80.6 | smaller, more frequent: stable, less E2, no rollercoaster | Before/after: faded weekly sawtooth vs flat 3-4x line inside the band, three ticked wins |
| 80.6–end | CTA | End card: COMPLETE INJECTION PROTOCOL week grid, COMMENT "PROTOCOL" gold pill, SENT TO YOU · FREE, disclaimers |

## Caption notes
Swears starred (F*CKING ×3, SH*T).

**Content:** overlays show only what Coach AGZ says. The level curves are illustrative shapes (no values or units); the frequency chart is labelled ILLUSTRATIVE. Disclaimer plus "not medical advice · work with your doctor" on the end card.
