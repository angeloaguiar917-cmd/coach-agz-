# Full test 02: "Tren micro year round" (in progress, not rendered)

**Source:** Drive `1lEcBtKd5b8V0xOxfFajNPcZCkvXJ3c9M` (1080×1920 HEVC, 60 fps, 1:41, already jump-cut).

## Done
- **Dead air:** 9 pauses of 0.22 s or more trimmed to about 0.12 s, frame-aligned, with 8 ms audio crossfades. The cut runs 98.93 s at 30 fps.
  - `trim.json` holds the cut points.
  - `assemble.py` builds the cut.
- **Stumble check:** a verbatim re-transcription found no stumbles.
- **Captions:** `words_final.json` holds the caption words, mapped to the cut.
  - Fixes: trenbolone, tren and "tren alone" (from a focused re-check).
  - Drift against the cut's own transcript: median 0.01 s. "365" and "We" were checked by speech-energy onset.
- **Text hook:** the engine was run, and the result is in `edit_log.json`.

## Not done
Graphics, captions burn-in, SFX, the final render and loudness mastering.
