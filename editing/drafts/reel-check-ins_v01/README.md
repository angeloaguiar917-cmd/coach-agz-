# Reel: "The guys who check in" (v01, 1080p)

**Source:** Drive `1SmPveeMgbLfZ-TYHVZJMUJvW5kIY3n9A` (1080×1920 HEVC, 60 fps, 1:01, kitchen selfie, one take).
**Output:** `coach-agz_check-ins_v01_1080p.mp4`: 1080×1920, 30 fps, H.264 High + AAC, faststart (plays and saves on iPhone/Android), 52.5 s, about −14 LUFS.
**Status:** draft for review. Fonts are stand-ins (Bebas Neue, Barlow Condensed, JetBrains Mono, DM Sans).

## Cut
- Dead air: every silent run over 0.25 s trimmed to about 0.16 s (frame-aligned, 8 ms audio fades). Two beats kept on purpose: after "one thing" (0.42 s) and before "…you know" (0.40 s).
- Stumble removed: "Consistently. Not— it's not that…" becomes "Consistently. It's not that…".
- 1:01 → 52.5 s (includes a 2.6 s end card over the silent tail of the take).
- Re-transcribed after the cut: no remaining stumbles.

## Face rule
Your face is never covered. Two layouts:
- **A (full talking head):** graphics live only in the band above the cap (y 230–490) and captions sit on the hoodie (y ≈ 1384).
- **B (split deck):** the footage eases into a framed window at the top (85 %, cap to collarbone visible), and a graphics deck rises underneath. Captions sit on the hoodie inside the window.

## Overlay map (every section uses a different overlay type)
| Time | Layout | Overlay type | What it shows |
|---|---|---|---|
| 0:00–0:05 | A | Text hook (frame 0) | "My best **CLIENTS** / never skip a week" |
| 0:05–0:11 | A | Timeline tracker + clock | SUBMITTED (this AM) → RESPONSE (11:58 PM → 12:00 AM) → READY (tomorrow ✓) |
| 0:11–0:17 | A | Data scan | Client-file grid scanned by a cyan sweep; one row locks gold, PATTERN FOUND. Punch-in on "very simple". |
| 0:18–0:25 | B | Photo evidence | Two before/after cards (AFTER wipes in on "crush" / "transformations"), then the client DM with the bubble bracketed |
| 0:25–0:30 | B | Range-bar chart | 5 markers (HCT, E2, LDL-C, ALT, eGFR) slide into the dialed-in zone, ✓ each, ALL MARKERS IN RANGE bar |
| 0:30–0:36 | B | Grid + line graph | 12-week log fills ✓; gold progress line climbs; ON/OFF row (✕ gaps) with a flat sawtooth line; red dims on "No, consistently" |
| 0:36–0:43 | B | Chat proof + dot plot | Client WhatsApp chat lands, shrinks; M–S message stack: 1 per day on "every day", stacks on "multiple times a day" |
| 0:43–0:50 | A | Monitor → log | Red flatline, PROGRESS 0.0 on "zero", BLAMES COACH; on "well, you know" it flips to that client's log: mostly ✕, CHECK-INS MISSED |
| 0:50–0:52 | B | Diverging graph + end card | CHECKS IN (gold, climbing) vs SKIPS (red, flat), logo, @coach.agz, disclaimer |

Captions: every word, Bebas, red lit block on the active word, groups of up to 3 words.

## Images used
- Two client before/after sets (cropped; the third person at the right edge of set 1 was cropped out; the app's "Paused" chip and expand icon removed).
- Client DM ("That finishes my cut and blast…"), cropped to the photo + message, gallery UI removed.
- Client WhatsApp chat, cropped to the three messages.

## Sound
Synthesised clinical SFX (`sfx.py`): sub hits on landings, one impact per beat (AFTER reveal, verdict bar, CHECK-INS MISSED), soft ticks on rows/cells, scan sweeps on line draws, monitor beeps and a flatline tone on "zero". Speech kept clear; mix normalised to −14 LUFS.

## Notes and flags
- Bloodwork bars and the progress/contact charts are **illustrative depictions** (no numbers shown); they aren't a specific client's labs.
- No spoken CTA in this take, so the end card has no comment keyword.
- `hooks/winners.md` still missing.

## Rebuild
`cut.py` (segments) → transcribe cut → `render.py <workdir> chunk n0 n1 out.mp4` → `sfx.py` → mux. `render.py <workdir> stills t…` for QC frames.
