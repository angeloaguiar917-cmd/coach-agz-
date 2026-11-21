# Reel 02 - "Anadrol vs Superdrol" (1080p30 final)

**Source:** Drive `1qthpM8sdux_XgEZIIQsOToFHM5idYD9d` (1080x1920 HEVC, 60fps, 1:36, in-car selfie).
**Output:** `coach-agz_anadrol-vs-superdrol_1080p30.mp4` - 1080x1920, 30fps, 1:34, -14.6 LUFS, TP ~-1.5 dBFS. H.264 + faststart, phone-downloadable.

Built to `../../QUALITY_STANDARD.md` + `../../brand/BRAND.md`. Footage left as shot; only overlays/captions/reframing carry the pop. No on-screen text hook at the open (Coach AGZ's request for this edit) - see `edit_log.json`.

## Cut
`trim.json` - 10 silent gaps tightened (~2.1s removed), misspeaks left (delivery was clean). Captions corrected: Anadrol, Superdrol, oxymetholone, methasterone, "banned it in 2012", "drives your hematocrit", "a meet", f*ck.

## Overlays (11 distinct types, colour-coded: Anadrol=cyan, Superdrol=gold, red=danger)
See `edit_log.json` overlay_variety. Reframes: FULL talking-head, WIN (footage top / graphics lower third), SIDE (left rail), PIP (face circle). Gold left rule, @coach.agz watermark and research/educational disclaimer persistent.

## Sound
`sfx.py` - clinical bed (sub thuds on panel landings, ticks on rows, scan sweeps on chart/molecule draws, heavy impacts on BANNED / AVOID BOTH / acute-risk slam / CTA), mixed under speech, final -14.6 LUFS.

## Build
- `python3 -I render.py <scratch> stills <t...>` - QC stills (raw-timeline seconds)
- `python3 -I render.py <scratch> chunk <n0> <n1> out.mp4` - output frame range
- `python3 -I sfx.py <scratch>` - SFX wav
Needs scratch `/fonts` (Bebas/DM Sans/Barlow Condensed/JetBrains Mono stand-ins) and `/src/raw.mp4`.

## QC done
- Every scene inspected as stills; final encoded file re-checked at 8 fast-motion points.
- Face-clear verified (overlays never cover the face; gauges moved to the freed lower third).
- Loudness -14.6 LUFS integrated.
- **Not done:** listening to the SFX mix by ear (no audio playback tool here) - please check music/SFX balance. Lab values are illustrative placeholders.
