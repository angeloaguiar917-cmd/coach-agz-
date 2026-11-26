# EQ "overrated" Reel — work in progress (no render yet)

Source: Drive "EQoverated" (`15IxWfNE9d9QDs2UwqUz84WU7q1HrV86U`), 1080×1920, 60 fps, 1:28.
Owner-supplied raw selfie take, one continuous shot in a car.

## Status
Cut and caption transcript are done. The overlay renderer and final export are NOT done.
No `edit_log.json` and no text hook (owner asked for no opening text hook on this one).

## What's here
- `keep.json` — the edited timeline: frame ranges kept from the source at 30 fps.
  Three jump cuts: two dead-air gaps and one mumbled "and do get it". Result ≈ 1:26.9.
- `cut_words.json` — word-level transcript of the **edited cut** (for captions), 323 words.

## Rebuild the cut (from repo root)
Download the source by ID (see `editing/examples/README.md` for the Drive pattern), then
select the `keep.json` frame ranges at 30 fps for video and trim+concat the same ranges
for audio with ~6 ms fades. The transcript in `cut_words.json` already matches that cut.

## Still to do
- Overlay graphics with variety (per `QUALITY_STANDARD.md` §1, §3): a different overlay
  type per beat — not one repeated type. Keep the face recognizable; keep graphics clear
  of the face track. Vibrant overlays only, footage left ungraded (`BRAND.md`).
- Phone-safe word-synced captions.
- Clinical SFX on contacts.
- Final export at 1080×1920, H.264 yuv420p, +faststart so it's phone-downloadable.
