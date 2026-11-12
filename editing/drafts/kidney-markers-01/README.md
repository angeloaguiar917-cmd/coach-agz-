# Kidney markers v01 (1080p30)

**Source:** Drive `1cf2RsVI_TWmpyPI_tKNKevXQiM1jIYMT` ("Kidney markers", 1080×1920 HEVC, 60 fps, 1:19.6, single take in the car).
**Output:** `coach-agz_kidney-markers_v01_1080p30.mp4`. It's 1080×1920 at 30 fps, 1:18.7 long and 69 MB. Video is H.264 High@4.2 (about 7 Mbps), audio is AAC 192k. The file is fast-start, so it plays and saves on a phone. Loudness is −14.1 LUFS, peak −1.4 dBFS.

## Brief
Use the saved setup and style, keep it at 1080p and make it downloadable to a phone. Vary the overlay types instead of repeating one panel. Keep enough face time that the speaker is recognised. Use graphs and more graphics, vibrant and on-brand.

## Cut
- Single clean take. Seven silent gaps were trimmed to about 0.12 s (1.0 s removed in total), with 8 ms audio fades.
- The end was trimmed 0.3 s after "Appreciate you guys".
- Left in on purpose: at 0:04.6, "might not be to actually telling you". I couldn't confirm a clean cut point without listening.

## Text hook (see `edit_log.json`)
- **Hook:** "High **CREATININE** / before you panic". It uses Barlow Condensed so the line can be in sentence case. It's visible from frame 0, holds to 5.0 s, then fades in 0.15 s.
- **Topic band:** "Lifters with high **CREATININE**" runs from 5.0 s to the midpoint (39.35 s). After that the top of the frame stays clear.

## Overlay map: 13 moments, 11 different layout types
| Time | Spoken point | Layout type | Graphic |
|---|---|---|---|
| 0:01.6 | "red alert" | Frame-edge alert | The whole frame pulses red with brackets and a RESULT FLAGGED tag |
| 0:10.6 | Elevated creatinine ≠ failing | Document card (top) | Renal panel (EXAMPLE values): creatinine row flagged H, then FLAG ≠ FAILURE and NOT A DIAGNOSIS |
| 0:15.4 | Where creatinine comes from | Split screen, graphic on top; footage drops down | Flow from CREATINE (muscle) through metabolism to CREATININE, then the kidneys, then "cleared from blood" |
| 0:20.1 | Bodybuilder, creatine, training | Side rails | Left: three stacking chips. Right: a vertical CREATININE gauge that climbs past REF to HIGH. KIDNEY DAMAGE NOT SHOWN |
| 0:28.2 | eGFR calculated from creatinine | Full graphic with a circular face PiP (iris transition) | eGFR formula box, creatinine input counter, and a semicircle gauge whose needle falls 98 → 58 (EXAMPLE). LOOKS WORSE |
| 0:34.4 | "What does that mean? Let's simplify" | Face only | Punch-ins at 110% and 118% |
| 0:37.4 | One biomarker in isolation | Inspection card | Five-marker panel with all but creatinine dimmed. IN ISOLATION |
| 0:40.5 | Cystatin C, UACR, BP, trends | Split screen, graphic on the bottom; footage rises and the card rides up with it | Four tiles that light on each word: filtration funnel, ALB:CREAT ratio, pressure trace, trend sparkline |
| 0:46.6 | Cystatin C ignores muscle mass | Side panel (gold rule grows into the panel, footage slides right) | Bar chart: a muscle-mass slider drives creatinine up (RISES) while cystatin C stays flat (STABLE) |
| 0:51.4 | Urine albumin | Floating object, no card | Urine dipstick with a cyan scan sweep. The ALB pad changes colour, then POTENTIAL DAMAGE SIGNAL |
| 0:54.3 | Other side of the spectrum | Spectrum strip | PANIC ↔ VERIFY ↔ IGNORE. The marker swings to IGNORE, then SAME MISTAKE |
| 0:59.6 | Red flag isn't a diagnosis / don't ignore | Two-column comparison | LAB FLAG vs DIAGNOSIS, a reference-range marker, NOT MADE FROM ONE FLAG, then ~~IGNORE IT~~ → RETEST · FULL PANEL |
| 1:08.1 | Ratios, all markers at once | Radar chart | Six-axis radar draws on with RATIOS and READ TOGETHER |
| 1:11.5 | CTA | End card | Logo, the free checklist with ticks, a gold COMMENT "KIDNEY" pill and the disclaimer |

**Face time:** the face is full-frame or near full-frame for the whole video except 0:28.2–0:34.6 (about 6 s). It stays visible as a gold-ringed PiP there.
**Footage:** no grade. Only position and scale change (punch-ins, splits, side shift, PiP).

## QC done
- **Captions:** built from a transcript of the edited cut. All 292 words are present, and "Coach Axe" is corrected to AGZ.
- **Stills:** 22 stills across every scene. These fixes were made:
  - Side-panel captions recentred onto the footage.
  - The LOOKS WORSE tag moved.
  - Radar fill and labels adjusted.
  - The rails exit moved before the PiP.
  - Spectrum labels pulled clear of the brackets.
- **Rendered file:**
  - Overview sheet every 1.5 s.
  - Frame strips around the doc → split, PiP in and out, card → bottom split, and bottom split → side panel transitions.
  - Fixes made there: the PiP now closes as an iris with no rectangular window edges, and the dashboard exits faster.
- **Decode and audio:** a full decode passed. Loudness was measured.
- **SFX:** placed by construction on each landing frame (`sfx.py`). Onsets weren't measured separately.
- **Not done:** listening (music isn't used; check SFX levels by ear). All lab values, eGFR numbers and gauge readings are illustrative and marked EXAMPLE on screen. Fonts are stand-ins (Bebas Neue, Barlow Condensed, DM Sans, JetBrains Mono).

## Rebuild
`render.py <scratch> chunk n0 n1 out.mp4` expects `<scratch>/fonts/` and `<scratch>/k/` holding `assembled.mov` (the trimmed cut from `cut.py` + `trim.json`), `words.json` and `logo.jpg`. Then mix `sfx.py` → `sfx.wav` with the voice and run loudnorm to −14 LUFS.
