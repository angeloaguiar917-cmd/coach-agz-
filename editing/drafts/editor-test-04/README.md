# Editor test 04: deeper, more vibrant colour (test only)

Feedback on test 03: make the colours deeper and more vibrant so they pop.
Same structure, timing and audio as test 03 (`../editor-test-03/sfx3.py`). 720×1280, 30 fps, 9.4 s. It doesn't approve the style or change final-video settings.

## Colour changes
- **Background push:** deeper, to `#050810` at 68%. Frosted panels at 86%.
- **Red:** `#E7472A` became `#FF3028` for flags, tags, the verdict bar and the caption block.
- **Panel frame, brackets and headers:** `#FFB830` electric gold. The brand gold `#C9A96E` stays on the edge rule and title.
- **X-ray:** `#28DCFF` cyan line art on `#020C1A`. The scan line is cyan too.
- **Checks:** `#2EE66E` green.
- **Documents:** full colour, not greyscale. The certificate has a deep red `#960E14` header band with white type.
- **Glow:** a screen-blend bloom (14 px and 40 px blur) on the gold frame, red flags, scan line and the verdict bar edge. On the verdict bar it's edge-only, to keep the white text crisp.

## Checks
Frame strips around every transition. The full file decodes without errors. The glow was checked at full 720 px for text contrast (it washed out the verdict text at first; fixed by making it edge-only). Audio is unchanged from test 03, which was verified (32/32 words, hits within 1 frame). Not listened to. The fonts are stand-ins.
