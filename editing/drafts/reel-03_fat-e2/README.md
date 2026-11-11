# Reel 03: "Fat e2" (1080×1920, 30 fps)

**Source:** Drive `1NrmdWG-0sUnVOsM789VE4jaI8bXQLhy8` (1080×1920 HEVC, 30 fps, 1:47, seated talking head in the gym).
**Output:** `coach-agz_fat-e2_1080p.mp4`: 1080×1920, 30 fps, H.264 High + AAC 48 kHz, faststart (plays and saves on a phone), about 1:41, −14 LUFS.
**Style:** test-06 overlay palette and clinical evidence look. The footage is ungraded. The fonts are stand-ins (Bebas Neue, Barlow Condensed, JetBrains Mono).

## Cut (`trim.json`)
- **Retake removed:** the first "meanwhile their E2 is climbing every single time they bump up because they're fatties". The clean second take is kept ("…because the aromatase activity has never actually dropped").
- **Dead air:** six silent gaps of 0.24 s or more trimmed to about 0.12 s. A trim was only made when the energy gap didn't overlap a word.
- **Total removed:** 5.97 s.
- **Punch-in:** alternates 100% / 108% at every jump cut.

## Text hook (see `edit_log.json`)
- **Hook:** "Puffy by week 3 on TRT / **BODY FAT** is the real cause" on frame 0, held 0–6.0 s, 0.15 s fade.
- **Topic band:** "**BODY FAT** is making your E2", shown until the first jump cut after the midpoint (53.3 s).

## Overlays: a different type for each beat
| Time | Speech | Overlay type | What it shows |
|---|---|---|---|
| 0:08 | feel fantastic 2–3 weeks, then puff up… sponge | **Line graph** (FIG 01) | A FEEL line climbs, holds a gold PEAK · WK 2–3 band, then breaks red at week 3 (BLOAT, MOOD ↓). A cyan WATER line takes off. |
| 0:20 | clinics say it's perfectly normal… it's not | **Paper document** | A tilted "patient follow-up · WK 3" note: complaint, "expected adjustment", "continue · reassure". It gets a bracket, then a red DISMISSED stamp (impact + shake). |
| 0:26 | adipose tissue = active endocrine organ, pumping aromatase | **X-ray scan** (FIG 02) | A cyan torso scan wipes in and an amber fat layer fills. Dose particles (T) enter, aromatase hexes spawn in the fat, particles leave as E2, and the E2 meter fills. The dose vial is crossed NOT THE SOURCE; the fat is bracketed SOURCE. |
| 0:43 | seen it thousands of times | **Case-file flick** | Case cards fan in on the right (TRT · E2 HIGH · BF% HIGH · WK 3 WATER), tagged SAME PATTERN. The face stays visible. |
| 0:46 | 200 mg → bump → 300 mg → chasing; E2 climbing; aromatase never dropped | **Bar + line chart** (FIG 03) | Dose bars count up to 200 MG and 300 MG, then a dashed "+ ?" bar. A red E2 line climbs over every bar. A flat amber AROMATASE ACTIVITY line is flagged NEVER DROPS. |
| 0:59 | can't out-dose a bad body composition | **Loop diagram** (lower card) | A DOSE ↑ → E2 ↑ → FEEL ↓ loop spins. A FAT hub lights the loop red. NO EXIT stamp (impact + shake). |
| 1:05 | drop body fat first, get lean, reassess T, bloodwork roadmap | **Roadmap** (FIG 04) | A gold route draws through 01 CUT BODY FAT (BF% gauge drains to LEAN, PRIORITY 01), 02 REASSESS T DOSE (dial turns down) and 03 BLOODWORK (tube fills). A map pin lands, then REPEAT loops back. |
| 1:15 | pull a full panel, check estradiol, stop guessing | **Lab requisition** (handoff: the roadmap panel collapses into it) | Checkboxes tick. ESTRADIOL (SENS) is bracketed gold MUST CHECK, then NO GUESSING. |
| 1:19 | less T / fewer compounds vs blasting; great 3 weeks, terrible after | **Side-by-side area charts** (FIG 05, a callback to FIG 01) | LOWER DOSE holds steady green with a check. BLAST spikes to WK 0–3, then crashes red for the REST OF CYCLE. |
| 1:31 | comment E2 | **CTA end card** | Logo and handle, FREE · ESTROGEN PROTOCOL + FRAMEWORK, a heavy gold COMMENT "E2" pill, and a static disclaimer. |

All chart shapes are illustrative, not patient data. No numbers are shown except the doses he says (200 mg, 300 mg). Case IDs are placeholders.

## Captions
Every word, from a re-transcription of the cut audio, with the red block on the active word at y≈1335.
Ambiguous words were checked with a second model:
- "if you **want** my full estrogen protocol" (medium.en, and small.en at temperature 0.4)
- "**Notice** most guys"

## Sound
Synthesised, clinical (`sfx.py`):
- sub hit on each panel landing
- scan sweeps on the X-ray wipe and the E2 line
- digital ticks on rows and flags
- impacts on DISMISSED and NO EXIT
- light thuds on the dose bars and the CTA pill

## Rebuild
1. Put the source at `<scratch>/src/fat_e2.mov` and the fonts at `<scratch>/fonts/`.
2. Build the audio: `assemble_audio.py` (voice) and `sfx.py` (effects).
3. Render the video: `render.py <scratch> chunk n0 n1 out.mp4`, in chunks.
4. Mux the audio with loudnorm to −14 LUFS.
