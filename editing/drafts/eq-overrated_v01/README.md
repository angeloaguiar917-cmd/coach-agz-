# EQ "overrated" Reel — v01 (1080×1920, 30 fps, 1:26.9)

Source: Drive "EQoverated" (`15IxWfNE9d9QDs2UwqUz84WU7q1HrV86U`), 1080×1920, 60 fps, 1:28.
Output: `coach-agz_eq-overrated_v01_1080p30.mp4` — H.264 high / AAC, −14.2 LUFS, TP −1.4 dBFS,
+faststart (phone-downloadable). Footage left ungraded; all vibrance is in the overlays (BRAND.md).

## Direction applied
- **No opening text hook** (owner instruction; overrides the frame-0 TEXT_HOOK_ENGINE). See `edit_log.json`.
- **Overlay variety** — ten distinct types, never the same card twice (QUALITY_STANDARD §1, §3):
  1. EQ on a cracking **gold pedestal** + x-ray vial, spec strike-throughs, hype-vs-payoff bars
  2. **Numbered flow stepper** (science → simplify → optimize)
  3. **Microscope lens** — red cells multiplying, RBC output meter
  4. **Dual-trace line graph** over 20 weeks — hematocrit climb vs gains crawl, "THE GAP", heart-load trace
  5. **Radial gauge** — E2 reading unstable, locks at steady state (wk 8–10)
  6. **Lab panel** sliding in — wk 4/5/6 in range, wk 10 "CRASHED" rubber stamp
  7. **Washout calendar grid** — weeks fill red, 10/12/16 marked, padlock "STUCK"
  8. **Ancillary bottle stack** — piling up "just to control E2"
  9. **Responder vs non-responder** cards + full-cycle progress + verdict bar
  10. **Branded CTA end card** — logo, `COMMENT "EQ"` gold pill
- **Face kept recognizable** — overlays live in the top band / side columns / lower third,
  placed from a face track (`faces.json` in the build dir); footage is never covered over the face.
- Word-synced phone-safe captions (Bebas), accent words recolour gold/red on the spoken word.
- Persistent gold left rule, @coach.agz handle, and the **FOR RESEARCH & EDUCATIONAL PURPOSES ONLY** footer.
- Clinical SFX only (sub hits, scan sweeps, digital ticks, one heavy impact per beat).

## Cut
Three small jump cuts (two dead-air gaps + one mumbled "and do get it"); see `keep.json`.
Captions transcript: `cut_words.json`.

## Rebuild
`r_core.py` + `r_sc_a.py` + `r_sc_b.py` + `r_main.py` render the graphics; `sfx_eq.py` builds the SFX.
Needs `assembled.mp4` (from `keep.json`), `logo.jpg`, and `fonts/` (open-source stand-ins, gitignored).
  `python3 r_main.py render 0 2606 out.mp4`  then mux with speech + `sfx_eq.wav`, loudnorm to −14 LUFS.

## Review done
Rendered-video QC: overlay stills across all ten types, face clearance, caption sync, graph legibility,
final-mux frames, loudness (−14.2 LUFS), true peak (−1.4 dBFS), faststart. Audio not listened to — lab/panel
values are illustrative placeholders; fonts are stand-ins. Please spot-check the sound by ear.
