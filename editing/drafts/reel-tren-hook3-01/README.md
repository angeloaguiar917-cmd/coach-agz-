# Reel: "Tren hook 3" — Tren microdosing, new opening (native 1080p + phone copy)

**Source:** Drive file `16g-d_PpP8i8knQmcQvVZgH6kHDk9iuM7`, 1080×1920 HEVC 60 fps, 2:00.0. It's a third take of the micro-Tren script with a new opening ("instead of running 500 mg a week… so I don't kill somebody while maximizing the growth effects"). The source has its own cut at 65.1 s.
**Outputs:**
- `coach-agz_tren-hook3_1080p30.mp4`: master, 1080×1920, CRF 16. Kept in the repo only if under 100 MB.
- `coach-agz_tren-hook3_1080p_phone.mp4`: phone copy, 1080×1920, two-pass ~2.5 Mbps, about 40 MB. This is the one sent to download.

## Work
- **Audio:** both channels carry the voice, no clipping (quiet recording). Voice +9 dB, then the limiter: −14.3 LUFS.
- **Transcription:** gap-guarded windows. Three garbled stretches were re-transcribed in focus: "an extremely potent 19-nor" (32 s), "Because fellas, let's be real here" (45.8 s), "keep muscle while on a deficit" (81.7 s). There was no restart.
- **Cut:** 3 dead-air trims (0.43 s). The "and" on a trim boundary was restored in the captions.
- **Text hook:** see `edit_log.json`. Winner: "Skip **500 MG** of **TREN** / do this instead".

## Overlays: variety by design
Ten formats, with no single style repeated back to back:
- **New for this take:**
  - Opening side card: **500 MG/WK** struck out on "so I don't…", then **GROWTH ▲** on "maximizing" (6.0–9.9 s).
  - Heat-strip timeline: the 400 → 500 → 600 mg years fill as a gradient strip, with four glowing side-effect icon badges below (10 s).
  - Radar chart in the protocol: 600 MG vs 25–50 MG across partitioning, nitrogen, fat oxidation and low sides; each axis lights up as it's named (99 s).
- **Carried over from micro-Tren v2:** full-screen evidence scene (10+ ring, report sheets, 500+), 19-nor molecule strip, dose-response curves, sleep-tracker card, DNA card, rating gauges and receptor docks, dose tube and activation donut with the struck-out icon callback.
  - These are re-timed onto this take by aligning the two transcripts word for word (348 anchors, `prev_take_words.json`), so each graphic lands on the same spoken word.
- Graphs are shape-only and marked ILLUSTRATIVE. Every number is Coach AGZ's own.

## Checks done
- **Full decode:** 3,627 frames at 1080×1920, for both the master and the phone copy (40.1 MB, two-pass 2.5 Mbps, faststart).
- **Frames:** strips at the hook exit, the opening-card exit, every panel open and close, the evidence scene in and out, the sleep and DNA cards, the radar build and the end card. No face flashes, no glow left over.
- **Fixed in review:**
  - A stale panel header.
  - The radar was too small, and its legend collided with the NITROGEN label.
  - The callback and ILLUSTRATIVE tag crowded the radar.
  - A NumPy-float crash in the time warp.
- **Sound sync:** all thuds and the impact within 1 ms of their frames. −14.3 LUFS, peaks −1.8 dBFS. No music. Not listened to.
- **Master file:** the CRF-16 master is 102 MB, over GitHub's 100 MB file limit, so only the phone copy is committed. The master stays in the session scratch area. Large masters will need Git LFS or Drive.

**Not done:**
- Listening.
- Subject cutout.
- Real fonts (stand-ins).
- `winners.md`.
