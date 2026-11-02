# Editor test 01: 720p30 preview (test only)

**Status:** test only. It doesn't approve the style or change quality settings for final videos.
**Source:** Drive file `1jas8rV35KbgQm6dfmQSAsEE7pOssLVAw` (1080×1920 HEVC 60 fps, 16.4 s). Used 0.00–9.40 s.
**Output:** `coach-agz_editor-test_720p30.mp4`, 720×1280, 30 fps, H.264 + AAC, 9.4 s, −14.2 LUFS, true peak −1.4 dBFS.

## Contents
- **Captions:** every word, from a Whisper small.en transcript with word timestamps (`words.json`). Groups of 2–3 words follow the phrasing, a red block sits on the active word, and they're centred at y≈1335 in 1080-space.
- **Pinned title:** "BIG PHARMA DOUBLE STANDARD". The wording is a placeholder written by the editor.
- **Layered graphic:** the footage pushes back (blur and navy dim) behind two shadowed cards, "USA BIG PHARMA ✕ Don't trust it." and "CHINA'S BIG PHARMA ✓ Order everything.", plus a "NO QUESTIONS ASKED" stamp.
- **Connected handoff:** the spoken caption phrase flies on a slight arc into each card header. Spacing holds, the colour shifts cream→gold or red, and the red block travels with the last word and fades.
- **Sounds (synthesised, original):**

| Sound | Time | Frame | What it marks |
|---|---|---|---|
| Whoosh | 4.36 s and 7.38 s | | Start of each flight |
| Thud | 4.70 s | 141 | Header 1 lands |
| Thud | 7.70 s | 231 | Header 2 lands |
| Tick | 4.95 s and 7.95 s | | Rows draw on |
| Impact | 8.66 s | 260 | Stamp lands, with a 2-frame shake |

## Checks done
- **Transcript:** the final audio was re-transcribed. It matches the source 32/32 words, with at most 0.1 s word-time drift.
- **Frames:** inspected at 2 fps overall, and frame by frame around both handoffs, the stamp and the shake.
- **Defects found and fixed:**
  - Wrong caption grouping.
  - A spacing jump at the start of the handoff.
  - A caption collision at handoff 2.
  - An orphaned red block.
  - The stamp touching the frame edge.
  - A black edge, then gold-rule flicker, during the shake.
- **Sound sync:** thuds and the impact were detected in the final mix within 1 ms of their target frames. Ticks were within 10–70 ms (speech in the band muddies detection).
- **Not done:** listening. Audio was checked by measurement only.

The fonts are stand-ins (Bebas Neue, DM Sans, JetBrains Mono).
