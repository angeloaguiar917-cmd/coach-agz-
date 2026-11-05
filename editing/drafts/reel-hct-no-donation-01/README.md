# Reel: "HCT no Donation" — dropping hematocrit without blood donation (native 1080p + phone copy)

**Source:** Drive file `10XsFfl3C5ZSVvaOyq9FyIU_yrhFhrmBC`, 1080×1920 HEVC 60 fps, 1:55.1.
**Output:** `coach-agz_hct-no-donation_1080p_phone.mp4`, 1080×1920, 30 fps, two-pass ~2.5 Mbps (phone-sized). The CRF 16 master stays in scratch if it is over GitHub's 100 MB limit.

## Order of work
1. **Audio check:** the voice is in the right channel only (left about −108 dB), with 113 clipped samples. Fixed to dual-mono at the mix (`fix_audio.py`, pan c1).
2. **Cut** (`trim.py`): the retake at 70.47–77.60 s is removed (cut at the energy dip before "A hematocrit"), plus one dead-air trim. 109.2 s including a 1.3 s end hold.
3. **Text hook engine** (`edit_log.json`):
   - **Winner:** **HEMATOCRIT** 57% to 49% / no blood donation
   - **Runners-up:** "Drop HEMATOCRIT / without donating blood", "Donating blood for HCT / the hidden cost"
   - **Flags:** `winners.md` missing.
4. Captions, neon overlay set, SFX bed, render, phone encode.

## Overlay set (all different formats, neon)
| Time | Speech | On screen |
|---|---|---|
| 0–6 | client 57% → 49% in 30 days | Frame-0 text hook, punch-in on "hematocrit" |
| 6–~55 | | Topic band **HEMATOCRIT** without donating (hidden during scenes) |
| 12.4–17 | mirror vs bloodwork | Floating split card: THE MIRROR · LOOKS GREAT vs THE BLOODWORK · HCT HIGH, TOTALLY DIFFERENT STORY |
| 17–23.5 | the usual playbook | Flowchart HCT UP → TRT CLINIC → DONATE BLOOD with travelling pulses |
| 23.5–37 | repeated donations | Three neon meters drain: IRON STORES, FERRITIN, ENERGY · PERFORMANCE; DOESN'T FIX THE CAUSE |
| 37–41.5 | not your first move | Floating card BLOOD DONATION / NOT YOUR FIRST MOVE |
| 41.5–52 | step 1 hydration | Test tube, plasma vs red cells; plasma drops when DEHYDRATED, HCT READS HIGHER, SAME RED CELLS |
| 52–60.5 | step 2 cardio | Scrolling ECG trace, PLASMA VOLUME bar EXPANDS, HCT ▼ LOWER, NO RED CELLS REMOVED |
| 60.5–69 | step 3 nutrition + supplements | Floating card with the three ingredient chips as spoken (no product graphic) |
| 69–80 | 57 / 54 lines | HCT scale 40–60 with the 57% PROMPT MEDICAL EVALUATION and 54% THRESHOLD lines, START DIGGING IN |
| 80–85 | investigate | 2×2 neon tiles: ANDROGEN EXPOSURE, SLEEP APNEA, HYDRATION, CARDIO RISK |
| 85–88.6 | two different things | LOWERING THE NUMBER ≠ FIXING THE PROBLEM |
| 88.6–97.5 | 40 vs 60 | Two bars: LOOK GREAT AT 40 + 6 MONTHS vs STRONG + HEALTHY to 60, STILL A UNIT AT 60 |
| 97.5–end | CTA | End card: DROP YOUR HEMATOCRIT THE RIGHT WAY FIRST, DONATION = LAST RESORT, COMMENT "BLOODS", SENT TO YOU, disclaimers |

## Caption notes
FERRITIN (heard "ferrets"), DIHYDROQUERCETIN (heard "dihydrocorticin"), PRO MUSCLE, "of 57", 57% / 49% / 54% joined, swear starred.

**Content:** overlays show only what Coach AGZ says. Disclaimer plus "not medical advice · work with your doctor" on the end card.
