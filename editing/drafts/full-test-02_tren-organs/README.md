# Full test 02: "3 Tren rules" (organs / cardio / microdose), 1080×1920

**Source:** Drive `1L9eym3Z9b3YWq9mMn_uR3peo2tOXF1LS` ("Tren shit organs 2"), 1080×1920 HEVC SDR, 60 fps, 1:20, one continuous walking selfie take.
**Output:** `coach-agz_tren-3-rules_1080p.mp4`: 1080×1920, 30 fps, H.264 High / AAC 48 kHz, `+faststart` (plays and saves on iPhone and Android), 1:18.5, about −14 LUFS.
**Status:** a full-length test in the test-06 overlay style, with a new layout system for face time. It isn't an approved Signature Style. The fonts are stand-ins.

## Cut
- It's a single clean take, so there are no retakes to remove. The five pauses over 0.3 s were tightened to about 0.12 s, frame-aligned with 8 ms audio crossfades (`trim.json` keep ranges). Total removed: 1.3 s.
- **Transcript fixes:** "Trenblum / Tremblone / trend" → Trenbolone / Tren; "tea" → T; "TREM" → TREN. "Keep it on" → "Keep an eye on", confirmed by an unprompted re-transcription of that phrase.
- **Needs a listen:** the last line transcribes as "absolutely for your appreciation guys". It's captioned as "absolutely FREE. I appreciate you guys". The end card does **not** say "free", in case that reading is wrong.

## Face time (feedback: make sure he's recognised)
Each output second falls into one of three layout modes:

| Mode | Share | What it is |
|---|---|---|
| Full frame | 38% (30.1 s) | Talking head with nothing over the face. Graphics sit only in the sky, the band or a slim side rail. |
| Shift | 55% (43.3 s) | The footage slides up 420 px, so eyes to chin stay whole above a graphic zone (y 990–1490). The move is a purposeful reframe; the camera holds while graphics build. |
| PiP | 7% (5.2 s) | A full-screen dashboard with him in a LIVE window. |

His face is on screen for 100% of the runtime. Graphic beats alternate with full-frame breathers: 0:00–0:11, 0:21–0:29, 0:39–0:44, 0:55–0:58 and 1:10–1:13 (output times are about 0.3–1.3 s earlier).

## Overlay types: 12 beats, no type repeated back to back
| Src time | Beat | Type |
|---|---|---|
| 0:00 | Text hook "3 TREN rules / before your organs pay" | Premium frame-0 title (Barlow Condensed, since Bebas has no lower case), 100→104% scale |
| 0:06 | Topic band + rule tracker 01·02·03; 03 pulses red on "third one… mistakes" | Persistent band with live chips. It exits at the midpoint, per the hook engine |
| 0:11 | **Graph 1: dose vs response.** Muscle curve plateaus, side-effect curve climbs, "COST > RETURN" shading | Split-screen chart panel, gold brackets |
| 0:21 | Recovery / appetite / sleep | Three ring gauges in the sky (top HUD); needles drop to red on "suffer" |
| 0:25 | Cardio | ECG trace sweeps across; NON-NEGOTIABLE 02 tag pill slams in |
| 0:29 | BP · ApoB · cholesterol · haematocrit · cardiac function | Full-screen dashboard + PiP: the ECG hands off into the panel, and spectrum rows tick in on each word |
| 0:34 | Greek god vs arteries | Two-column OUTSIDE / INSIDE comparison: physique bar ✓ vs an artery cross-section narrowing, with an ECG that goes irregular on "heart attack" + impact |
| 0:40 | Rule 03, high dosage | Slim side rail: a big "03" slam and a dose dial snapping into red |
| 0:44 | 2–3 h sleep, sweats, BP climbing | Phone object (sleep-tracker UI) rises into frame |
| 0:49 | Another supplement vs the underlying problem | Bottles drop and stack; bracketed SYMPTOM PATCH vs a HIGH DOSE ROOT CAUSE block; verdict bar BODY SIGNAL = CHANGE THE PROTOCOL |
| 0:58 | **Graph 2: blood level over 7 days.** Big doses spike and crash vs daily acetate microdose holding steady | Cyan scope / oscilloscope panel (a different frame style), daily dose ticks |
| 1:04 | SHBG, total T, free T, progesterone, prolactin, E2 | Paper lab-order document; each row is bracketed and ticked as it's said |
| 1:11 | Keep an eye on it consistently | Side rail: RECHECK cadence timeline |
| 1:14 | CTA | End card: logo, TREN PROTOCOL, and a gold COMMENT "TREN" pill that lands on "comment", plus the disclaimer |

- **Captions:** every word, in red-box Bebas. Accent words recolour gold or red as they're spoken; the box turns gold on positive keywords. In shift mode they move up to the seam just under the mouth. Profanity is starred.
- **Sound:** clinical only (sub hits, ticks, scan sweeps, soft monitor beeps, two impacts). Each one is placed on its visual landing and mapped through the cut.

## Honesty notes
- Both graphs, the dashboard target zones, the phone UI, the BP trend and the 7-day blood-level curves are **illustrative shapes**, labelled ILLUSTRATIVE on screen. No numbers were invented. The only figures on screen are ones he says: 3 rules and 2–3 hours of sleep.
- The lab-order document shows test names and "ordered" ticks, not values.

## QC done
- Stills reviewed at 26 points, then again after the fixes:
  - The band was hidden during PiP (it collided with the RULE 02 title).
  - The white-on-white DOSE tag was fixed.
  - The phone exit is now faster, so it clears before the bottles drop.
  - The gauges are bigger, with dark label plates for contrast against the sky.
  - The dashboard rows were moved off the PiP frame.
- **Post-render:**
  - Overview sheet every 1.5 s.
  - Frame strips (7 frames at 30 fps) at all 10 layout transitions.
  - In the full ↔ PiP transitions, the dashboard rows built over the face before the shrink, and the band overlapped the RULE 02 title on exit. Both were fixed, then that chunk was re-rendered and re-checked.
- **Output:** 78.53 s; −14.0 LUFS integrated; true peak −2.1 dBFS; H.264 High 4.2, 8.7 Mbps; AAC 192k; faststart.
- **Not done:** listening. Check the tail line and the SFX levels by ear.

## Files
`render.py` (frames, all timings in source seconds and mapped through `KEEP`), `audio.py` (cut + SFX), `edit_log.json` (text-hook engine block), `words_src.json`, `trim.json`.
