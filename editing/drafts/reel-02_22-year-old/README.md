# Reel 02: "22-year-old me" (3 harsh realities) — 1080p v01

**Source:** Drive `1PY_iKz_Dsk9zPNHnSmnuSQfZqGyvTAaP` ("22 year old"), 1080×1920 HEVC, 60 fps, 1:37.6, one car selfie take.
**Output:** `coach-agz_22-year-old_v01_1080p30.mp4`. 1080×1920, 30 fps, H.264 High + AAC, faststart (plays and saves on a phone). 1:34.6, about −14 LUFS.
The MP4 isn't committed (size); it's sent in chat. Rebuild with the scripts below.
**Style:** the saved full-test-01 / test-06 setup (clinical evidence look, high-pop overlay palette, red active-word Bebas captions, gold left rule, footage untouched). New this time: no overlay type is used twice.

## Cut
- 13 dead-air trims (silences ≥ 0.22 s cut to ~0.12 s, 8 ms crossfades), plus the 1.2 s pause after "bloodwork is the roadmap" taken down to ~0.5 s. 3.0 s removed. `trim.json`.
- Punch-in alternates 100 % / 108 % at every jump cut.
- No misspeaks or retakes in this take.

## Text hook (see `edit_log.json`)
`STEROIDS at 22 / the damage you can't see`, Barlow Condensed (stand-in), visible from frame 0 to 4.4 s with a slow 100→104 % push. Then a topic band with a **3 HARSH REALITIES tracker** (01 HEART, 02 LABS, 03 YEARS lights up as each is covered) until the midpoint cut at 46.9 s.

## Overlay plan (13 different types)
| Time | Line | Overlay type | What it shows |
|---|---|---|---|
| 0:04.7 | "22-year-old Angelo" | Slot counter card | REWIND, digits roll and land on 22, FILE: ANGELO |
| 0:08.6 | heart overtime, RBC, blood volume | Evidence panel: live ECG trace + gauges | ECG speeds up into red (OVERTIME), RBC bar breaks out of its gauge (THROUGH THE ROOF), blood volume SPIKED |
| 0:15.1 | infection 24/7, chronic inflammation | Radial 24-hour dial | ring fills all 24 hours, ALWAYS ON → CHRONIC; FORCED TISSUE GROWTH / INFLAMMATION tags |
| 0:25.5 | 224 lb, +18 lb in 10 weeks | Scale readout + line chart | counter to 224 LB, line WK 0 → WK 10, +18 LB / IN 10 WEEKS |
| 0:31.0 | tank vs bloodwork | Split screen | left: THE MIRROR (live crop of him) LOOKS LIKE A TANK; right: organ-function trend DECLINING, hematocrit marker past ref range to 58 HIGH, liver enzymes OFF THE SCALE |
| 0:41.3 | trading years for aesthetics, over and over | Paper receipt | TRANSACTION: BOUGHT AESTHETICS, PAID WITH YEARS, REPEAT x2 x3, NO REFUNDS stamp |
| 0:48.8 | die at 50 vs average at 80 | Dual-path lifespan chart | PEAK AT 22 → ENDS AT 50 vs AVERAGE AT 80, FALSE CHOICE slam |
| 0:56.3 | not safe, right way / wrong way | Lower-third toggle | ANABOLIC STEROIDS / NOT SAFE, then a RIGHT WAY ↔ WRONG WAY switch |
| 1:04.4 | cost, biomarkers, bloodwork, side effects | 2×2 checklist | four ticks, OUTCOME CHANGES bar |
| 1:10.8 | crisis you can't see until damage is done | Threshold area chart | damage curve rising through a hatched SILENT ZONE, FIRST SYMPTOM where it crosses |
| 1:17.8 | bloodwork is the roadmap, EKG/ECG… | Route map | 5-stop route on a topo map: BLOODWORK, EKG / ECG, BIOMARKERS, CROSS-REFERENCE (links), SIDE-EFFECT PROFILE |
| 1:26.7 | 35+, no labs until broken | Calendar grid | 36 empty months, LABS PULLED: 0, last cell cracks red: SOMETHING BREAKS |
| 1:33.0 | "don't be that guy" | End card | logo, BLOODWORK IS THE ROADMAP, @COACH.AGZ, disclaimer |

Cards sit over the cap / upper frame so the eyes and mouth stay clear; full panels push the footage back as before.
The 58 hematocrit, 224 lb, +18 lb and 10 weeks are his spoken numbers. Trend shapes, reference ranges and the 36-month grid are illustrative, not data.

## Sound
Clinical bed only (`sfx.py`): sub hits on panels, ECG beeps on each R-peak, scan sweeps on chart builds, digital ticks on tags, impacts on THROUGH THE ROOF, FALSE CHOICE, FIRST SYMPTOM and SOMETHING BREAKS. Mixed under speech, −14 LUFS, peak −1 dBFS.

## Captions
Built from a transcript of the edited cut (363 words). Corrected: 22-year-old, 24/7, "tanking. Mirror", hematocrit, "die at 50 than", EKGs. "Fucking" shows as F*CKING.

## Files
`render.py` (frames), `sfx.py` (sound), `trim.json` (cut), `words_final.json` (captions), `edit_log.json` (text hook).
