# Reel: "Gear muscle timeline" (work in progress, not rendered)

**Source:** Drive file `1Q_eaPSUUjErwTvheSYa2hMp4-YeZf5G7`, 1080×1920 HEVC 60 fps, 2:52.8, single take with one in-camera jump cut (42.8 s).

**Done:**
- `trim.py`: no trims (no retakes, no dead air). The cut is 174.1 s including a 1.3 s end hold.
- **Audio check:** the voice is in the right channel only (left −108.9 dB) and there are 70 clipped samples. It needs a dual-mono fix at the mix.
- **Transcript corrected** with focused small.en/medium.en passes. The long pass had garbled three stretches:
  - 41–43 s: "…when combined with training."
  - 52–68 s: the six-month section.
  - 155–161 s: "…the goal isn't to gain weight as f*cking fast as possible…"
  - Also joined "fat-free", starred the swears and removed one "none none" stutter.
- **Hook picked:** "3 months on GEAR / vs their 5 to 10 years".

**Flag:** at 108.8 s both models hear "five years of interrupted growth". He likely means "uninterrupted"; the captions follow what he says.

**Not done:** overlays, render and phone copy. `render.py` here is still the previous Reel's engine (GH timelines), copied as a base and not yet adapted.
