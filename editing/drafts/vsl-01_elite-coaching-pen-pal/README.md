# VSL 01: "Elite coaching, not a pen pal" (1080p30 export)

**Source:** Drive `1NGYByHp5u7xNq-7qLh4Vp2kmMrzQuksp` ("Coaching"), 1080×1920 HEVC, 60 fps, 4:17, one seated office take.
**Testimonials:** Drive folder `1FyJCaMW8-q8X9KbM9XTtQafjGcxyF4Ny` (6 before/after images, 6 chat screenshots).
**Output:** `coach-agz_vsl-01_elite-coaching_1080p30.mp4`. It's 1080×1920, 30 fps, H.264 High with AAC and faststart, so it plays and saves on a phone. Length 4:12, −14 LUFS, true peak −1.5 dBTP.
**Status:** first full 1080p version using the saved setup (QUALITY_STANDARD, BRAND, TEXT_HOOK_ENGINE). It hasn't been approved.

## Cut
- Removed the stumble "But it's just," plus its 0.6 s pause before "it's a different level". The cut point was checked on the energy profile.
- Trimmed 15 breaths/pauses of 0.33 s or more down to about 0.15 s, frame-aligned with 8 ms fades. 5.2 s removed in total.
- Captions correct "Trend" to TREN.

## Text hook (see `edit_log.json`)
- **Hook:** "Paying for **ELITE COACHING** / getting a pen pal". It uses native mode and is visible from frame 0 until 5.9 s, then fades over 0.15 s.
- **Topic band:** "ELITE COACHING not a pen pal" runs until the midpoint cut at about 2:06.
- **Punch-ins:** the first punch-in lands on "paying". Punch-ins alternate (106–112%) on key lines and at every jump cut.

## Overlay map (output time): 26 moments, 6 layouts, no layout used twice in a row more than twice
| Time | Type | Layout |
|---|---|---|
| 0:01.8 | Invoice: months "PAID", amounts redacted, TOTAL = THOUSANDS | lower stage |
| 0:05.3 | Phone chat: "Bloods are back", day counter 1→6, "last seen 6 days ago" | phone mockup |
| 0:08.0 | Lab report with a green LOOKS GOOD stamp slam, then red brackets and NO CONTEXT / NO PLAN / NO WHY | panel |
| 0:16.7 | Verdict: ELITE COACHING struck through, red bar "A PEN PAL" | free card |
| 0:22.4 | 3-step chevron pipeline: BREAK IT DOWN → SIMPLIFY → OPTIMIZE | top strip |
| 0:26.2 | Radial hub: YOU plus 7 nodes lighting on each word, gold ring "= COACHING" | panel |
| 0:39.5 | Reference-range spectrum (E2 "in range on paper") vs "how you actually feel" meters dropping red; "you're good dude" bubble crossed out | panel |
| 0:54.6 | Cross-reference web: biomarker card wired to 9 life factors | panel |
| 1:07.1 | Week calendar filling (business, work, team, vacation, family) + HORMONES block | full-screen carousel |
| 1:16.5 | **Step graph** "every step ↑" | lower stage |
| 1:21.2 | **Bar chart:** time to reply, typical coach 5–6 days vs Coach AGZ every day | panel |
| 1:35.6 | **Testimonial:** "gone to the limits and beyond", marker highlight | free card |
| 1:40.0 | **Testimonial:** shoulder "never felt better" | free card |
| 1:47.1 | **Histogram:** adjustments per week (tiny tweaks → every other day) | lower stage |
| 1:55.2 | **Gantt:** TREN · 16 WEEKS bar, then dashed NO PLAN, WK17 / WK20 / YEAR 2 "?" (timeline zooms out) | panel |
| 2:19.2 | Feedback loop: compound → bloods → body → titrate, with nutrition/carbs/protein/training inputs | panel |
| 2:38.0 | **Testimonial:** "you who provided the structure" | tilted top card |
| 2:48.2 | Chips: wife, kids, family, business, vacation → "protocol built around all of it" | lower stage |
| 2:59.6 | Two-column rule: PROTOCOL FIRST ✕ vs LIFE FIRST ✓, NEVER stamp | full-screen carousel |
| 3:10.0 | **Client results wall:** 6 before/afters | full-screen carousel |
| 3:22.7 | **Testimonial + bar chart:** "whole different level", 6 months on his own vs 7 weeks with AGZ | panel |
| 3:27.0 | **Testimonial phone:** his report message (IGF-1/ApoB), then "most in-depth feedback I've received" | phone mockup |
| 3:34.0 | **Testimonial:** "You have my absolute trust" | top card |
| 3:36.9 | Older client's before/after + **healthspan graph** + AT 70 / 80 / 90 | panel |
| 3:59.3 | Lower third: DM @coach.agz | free card |
| 4:09.5 | End card: logo + DM @coach.agz pill on "reach out" | free card |

## Privacy and accuracy
- Testimonial crops leave out client names, avatars and the campground/location details in `8.png`.
- In `7.png` only the coach's own report message and the "thank you" reply are shown; the quoted name below them is cropped out.
- **Illustrative, not real data:** the lab report values (E2 31, TT 912, HCT 49.8, cholesterol 188), the biomarker card, the invoice rows, the histogram bars and the healthspan curves.
- The "6 months vs 7 weeks" bar chart comes straight from the client's message (IMG_3056).
- The "5–6 days" figure comes from Coach AGZ's own hook line.

## Pipeline notes
- **Transcription:** whisper.cpp (pywhispercpp) with the medium.en model, converted from OpenAI's checkpoint without torch (`pt2ggml.py`). Word times come from DTW alignment (`wdtw.py`), shifted −0.18 s (checked against pause onsets).
- **Build steps:**
  1. `prep.py` builds the cut list, captions, hook and punch-ins.
  2. `render.py` renders the frames.
  3. `sfx.py` generates the sound design.
- **Sound:** a clinical palette, kept restrained:
  - sub-thud on panel entries
  - scan sweeps on lower-stage entries and bar growth
  - impacts on the LOOKS GOOD stamp, the PEN PAL bar and the NEVER stamp
  - soft ticks on list items

## QC done
- Stills reviewed at roughly 60 timestamps across every scene. Fixed:
  - hub node timing
  - label overlaps
  - the calendar headline overflow
  - testimonial highlight colour and placement
  - the client wall colliding with captions
  - the shoulder quote being too small inside the phone
  - Gantt label collisions
  - lowercase @coach.agz on the CTA
- Loudness measured: −14.0 LUFS integrated, −1.5 dBFS peak.
- **Not done:** listening (I can't hear audio), so check SFX levels and the speech cut at about 3:22 by ear. The fonts are still stand-ins.
