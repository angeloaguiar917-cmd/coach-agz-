# Full test 02: "Heart health" (ezetimibe + telmisartan), 1080p30

**Source:** Drive `1SDghaagxtVeR_pmtaty6n5oHTsZ5Il0f` ("Heart health hook 2", 1080×1920 HEVC 30 fps, 2:04, single take in the car).
**Output:** `coach-agz_heart-health_full-test-02_1080p30.mp4`. 1080×1920, 30 fps, H.264 High@4.2 + AAC 192k, `+faststart` (plays and saves straight to a phone), 1:58.2, 94.7 MB, −14.2 LUFS, true peak −1.6 dBFS.
**Status:** full-length test in the saved test-06 style. Not an approved Signature Style.

## New for this edit (feedback from earlier tests)
- **Face stays recognizable.** The old full-screen blur push behind a centre panel is gone. Graphics only use space around the face; the footage itself moves into different layouts. It is never blurred, graded or covered over the eyes or mouth.
- **No repeated overlay type back to back.** The footage morphs between 7 layouts (0.45 s ease), and every beat uses a different graphic type.

| Time | Footage layout | Graphic |
|---|---|---|
| 0:00 | Full face | Frame-0 text hook (TEXT_HOOK_ENGINE), punch-in on "blood pressure" |
| 0:06 | Split: face lifts, panel below | Standard lab panel all IN RANGE (greys out on "unless"), EKG trace with LVH SIGNS flag, silent-phase timeline, red verdict slam SYMPTOMS = LATE STAGE |
| 0:13 | Full face, top cards | Two redacted compound slots, MECHANISM → SIMPLIFY → OPTIMIZE stepper |
| 0:20 | Brand scene, face in circle (bottom right) | Bar chart (HDL collapses, LDL/ApoB rise), CV risk donut, then dual line chart (CV risk vs physique) |
| 0:31 | Evidence-feed window | Slot 01 redaction wiped: EZETIMIBE. Cyan X-ray gut schematic: NPC1L1 gates block, liver clearance, LDL↓ ApoB↓ |
| 0:46 | Face in right column | BP dial gauge into red, workload meter, LV cross-section wall thickening (LVH) |
| 0:56 | Full face | Slot 02 reveal slam: TELMISARTAN (impact + shake) |
| 1:00 | Split | AT1 lock and key (ANG II bounces off), vessel dilates, BP trace falls |
| 1:06 | Full face, top card | Before/after LV rings regress, gold verdict REGRESSION DOCUMENTED |
| 1:13 | Face in left column | Glucose curve flattens, androgen receptor grid fills (tagged SOME STUDIES) |
| 1:22 | Face circle (top) | Two-column comparison: ezetimibe vs telmisartan |
| 1:30 | Full face, calm | Room to breathe, heartbeat line, 6:00 PM clock + 7-day strip |
| 1:45 | Split | CTA: logo, free breakdown rows tick, COMMENT "HEALTH" |

## Cut
30 frame-aligned trims (`trim.json`): every silence of 0.22 s or more trimmed to about 0.12 s, with 8 ms audio crossfades. The pause before "you're done" is kept at about 0.3 s as a beat. 5.8 s removed. No misspeaks found. Punch-in alternates 100/108% at each jump cut.

## Captions
Saved setup: Bebas, 1–3 words, red lit block on the active word. They sit low on full-face shots and at the seam in split shots. Built from a transcript of the trimmed audio, with terms fixed: Anabolics, ezetimibe, telmisartan, ApoB, NPC1L1, AT1.

## QC done
- **Captions:** the final audio was re-transcribed and matches 385/398 heard words. The rest are deliberate drug-name spellings plus "the"/"dosage(s)"-level ambiguities. A dropped "it" ("how it improves") was restored.
  - Drift: median 0.00 s, p95 0.10 s.
- **Sound sync:** SFX located in the final mix by cross-correlation. All hits land within +2 ms of target (constant AAC offset). The verdict impacts and screen shakes share their frame.
- **Visuals:** stills at every scene, an overview every 2.5–3 s, and frame strips at every layout morph and slam.
- **Fixed during review:**
  - Hook word washed out by bloom, and too wide for the safe zone.
  - Split captions sat on the mouth.
  - PiP circle overlapped the chart labels.
  - Line-chart curves overlapped each other.
  - Missing ↓ glyphs.
  - Clock card and LV card too close to the eyes.
  - Panels appeared before their morph landed.
  - Pillow 12 ignores fill alpha for `text()`. All text fades now blend through a coverage mask, and the base frame is RGB so shape fades blend too. This had made fading text pop on and off at full strength, and drew zero-alpha labels.
- **Full decode clean:** 3545 frames.
- **Not done:** listening by ear. Audio was checked by measurement only.

All schematic shapes are illustrative, with no lab values shown. The fonts are stand-ins (Bebas Neue, Barlow Condensed, JetBrains Mono).
