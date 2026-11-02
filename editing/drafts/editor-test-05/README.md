# Editor test 05: maximum vibrance, pop and contrast (test only)

Feedback on test 04: more vibrant, more pop, more contrast.
Same structure, timing and audio as test 03/04. 720×1280, 30 fps, 9.4 s. It doesn't approve the style or change final-video settings.

## Changes vs test 04
- **Footage grade (whole video):** contrast ×1.18, saturation ×1.28, a gentle S-curve, and a vignette centred on the face.
  - Measured on a talking-head frame: 11.5% of pixels at ≤4/255 (the black tank top and car interior crush to black) and 1.1% at ≥251 (the window).
- **Background push:** `#020308` at 80%. Panels at 92% opacity.
- **Accents:**

| Colour | Test 04 | Test 05 |
|---|---|---|
| Red | `#FF3028` | `#FF221C` |
| Gold | `#FFB830` | `#FFC21A` |
| Cyan | `#28DCFF` | `#00E5FF` |
| Green | `#2EE66E` | `#1EFF6E` |

- **Strokes:** thicker panel frame (3 px at 80%, brackets 7 px), flag brackets 7 px, tags 32 px mono on 48 px bars.
- **Bloom:** double strength (×2.0 and ×1.5 layers). The X-ray has a three-layer cyan bloom.
- **Documents:** pure white paper, near-black ink, and a saturated `#D20A14` certificate header.

## Checks
Frame strips around every transition, a full decode, and the clipping measurement above. Audio is unchanged from test 03 (verified there). Not listened to. The fonts are stand-ins.
