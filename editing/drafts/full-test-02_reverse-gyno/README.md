# Full test 02: "Reverse GYNO in 3 steps" (1080×1920, 30 fps)

**Source:** Drive `1Kzoip1xjdSzQobme25Kqhq0TuZKJypfq` ("3 steps reverse gyno w/o dosages"), 1080×1920 HEVC, 60 fps, 2:33, one clean selfie take in the car.
**Output:** `coach-agz_reverse-gyno_1080p30.mp4`, 1080×1920, 30 fps, H.264 High + AAC, faststart (plays and saves on iPhone/Android). Final file also uploaded to Google Drive.

## Brief from Coach AGZ
Saved setup and style, 1080p, downloadable to phone. **Different overlay types, no repeating the same one over and over. Keep the face recognisable.** Graphs, more graphics, vibrant and on-brand.

## Cut
- One clean take; a filler-preserving pass found no stumbles.
- Dead air: 22 silences ≥ 0.24 s trimmed to about 0.12 s (5.1 s removed), with 8 ms audio crossfades. Frame-exact.
- Ends on the CTA ("comment the word gyno below"). The recap after the CTA (2:21–2:33: "find it early, read the panel… bloodwork is the roadmap") was cut so the CTA is the last line. A 1 s end card holds on the last frame.
- Edited cut: 2:16.4 speech + 1.0 s end card = 2:17.4.

## Face rule (new for this edit)
Earlier edits blurred and darkened the whole frame behind every panel, which hid the face. Here the footage is **never blurred or darkened behind a graphic**. Graphics live around the face using three layouts:
1. **Full frame:** overlays in the headliner zone above the cap, the side flanks, or the chest.
2. **Split screen:** the footage slides up 400 px (face fully visible) and a panel opens below with a gold seam line.
3. **Picture-in-picture:** the face moves into a gold-framed "LIVE" card on the brand background while a big graphic plays.

## Overlay map (11 distinct types)
| Time | Layout | Type | What it shows |
|---|---|---|---|
| 0:00 | full | Text hook (engine) | "Reverse GYNO in 3 steps / before it turns surgical" |
| 0:10 | split | **Line/area graph** | Reversal window: reversibility falls over time; NOW marker → slides to MONTHS → SURGICAL ONLY zone |
| 0:22 | full | **Twin scan lenses** flanking the head | EARLY soft glandular (cyan, REVERSIBLE) vs LATE hard fibrotic (red, SURGICAL ONLY) |
| 0:05–1:08 | full | **Step tracker band** | Topic band + 01 FIND / 02 CORRECT / 03 TREAT pills that light as each step starts |
| 0:37 | PiP | **Decision tree → lab requisition** | ON TRT → E2; OTHER ANABOLICS (NPP, DECA) → PROLACTIN; then a paper lab form ticks E2 sensitive + prolactin, "DRAW BEFORE ANY CHANGE", ASAP stamp |
| 0:56 | full | **Range gauge (spectrum)** + trade-off chips | E2 marker HIGH → IN RANGE → crashes to zero; PRL row; DEAD JOINTS / NO LIBIDO / FLAT MOOD |
| 1:13 | split | **Mechanism schematic** | Biomarker fixed = stops growth / existing tissue won't shrink → SERM docks in the breast receptor, estrogen bounces off (Raloxifene, Nolvadex) |
| 1:32 | full | **Redacted document** | Paper "CLIENT FILE": name/photos/results redacted, POSTED = PERMANENT, PROTECTED stamp |
| 1:45 | PiP | **Big stat + dashboard chart** | E2 count-up to 120; bars (lump) + line (E2) across WK 0–4 with FOUND / CORRECTED / TREATED; GONE at week 4 |
| 2:04 | full | **Hazard meter + verdict bar** | MENT (trestolone): aromatisation meter OFF THE SCALE; "NO PLAN = NO MENT" |
| 2:11 | full | **CTA** | Free protocol + bloodwork list docs, FREE pill, then gold COMMENT "GYNO" bar; end card with logo, handle, disclaimer |

## Data honesty
Only the case numbers that were spoken are shown as numbers: E2 120, a lump present 2–3 weeks, gone within 4 weeks. The week 1–3 bars and line are an illustrative trend, labelled "ILLUSTRATIVE TREND" on screen. The reversal-window curve has no numbers.

## Files
- `render.py`: compositor (`stills` / `chunk` modes); `sfx.py`: synthesized SFX bed.
- `transcribe.py`: Whisper word-timestamp transcription; `words_final.json`: corrected caption words; `trim.json`: the cut.
- `edit_log.json`: text hook engine output.
