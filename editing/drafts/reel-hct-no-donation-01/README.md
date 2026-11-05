# Reel: "HCT no Donation" (work in progress, not rendered)

**Source:** Drive file `10XsFfl3C5ZSVvaOyq9FyIU_yrhFhrmBC`, 1080×1920 HEVC 60 fps, 1:55.1.

**Done:**
- **Paper edit** (`trim.py`):
  - The retake is cut at 70.47–77.60 s. That was the first attempt at "a hematocrit of 57 generally means… 54 is a threshold for most guys"; the restart after the source's own jump cut is kept.
  - One dead-air trim.
  - Cut length 109.2 s, splice verified by re-transcription.
- **Audio check:** the voice is in the right channel only (left about −108 dB), with 113 clipped samples. It needs a dual-mono fix at the mix step.
- **Caption corrections queued:** FERRITIN (heard "ferrets"), DIHYDROQUERCETIN (heard "dihydrocorticin"), PRO MUSCLE LABS, "a hematocrit of 57", and 57% / 49% / 54% joined.

**Not done:** text hook, overlays, render and phone copy. The overlay build stopped partway. `render.py` here is still the previous Reel's engine, copied as a base and not yet adapted.
