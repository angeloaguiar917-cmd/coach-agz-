# Full test 04: "Tren vs sleep" (1080p)

**Source:** Drive `1DXiRYesVKTp-Ygk_R-ReyAQEHOR4Kc4d` ("Tren v sleep"): 1080×1920 HEVC, 60 fps, 0:53. One take, walking outside and then in the car.

**Output:** `coach-agz_tren-sleep_full-test-04_1080p30.mp4`
- 1080×1920, 30 fps, H.264 High@4.2 with AAC audio.
- `+faststart`, so it plays and saves straight to a phone.
- 53.2 s long: 52.2 s of speech plus a 1 s end-card hold.

**Brief:** the saved setup (test-06 overlay palette, untouched footage, every-word captions, text hook engine), with varied overlay types: graphs, more graphics, vibrant, on brand.

## Cut
- No retakes or misspeaks.
- Four silent runs of 0.22 s or longer were trimmed to about 0.12 s, removing 0.8 s in total.
- The punch-in alternates between 100% and 108% at each trim.

## Text hook (see `edit_log.json`)
- `2 to 3 hours of sleep` / `wasting your TREN cycle` is visible from frame 0 until 6.0 s.
- The topic band "Your sleep on TREN" then runs until the midpoint (26 s).

## Overlays: 7 moments, 7 different types
| Time | Type | What it shows |
|---|---|---|
| 0:03 | **24-hour clock + CNS meter** | A gold 8-hour target arc. On "two to three hours" a red 2–3 h arc fills in and the centre shows "2–3 HRS ASLEEP". On "central nervous system" the CNS meter climbs to red OVERDRIVE. A "CYCLE WASTED" stamp slams on "wasting". |
| 0:11 | **KPI tiles** (top strip) | "What Tren does": PROTEIN SYNTHESIS and NUTRIENT PARTITIONING tiles. A curve climbs in each and a green UP arrow lands on each spoken word. |
| 0:15 | **Overnight hormone chart → 3-hour cut** | Curves draw on a 22:00–06:00 axis as each is named: GH pulses, testosterone, recovery, insulin sensitivity. "Asleep · 8 hrs" bar. On "only getting three hours" a red line slices the night at 01:00; the rest is shaded and greyed: "AWAKE · 5 HRS LOST", "SIDE EFFECTS: ALL". The verdict bar slams "SIDES ONLY = NO GAINS". |
| 0:27 | **Two-column comparison** | TREN · NO SLEEP: ✕ high hematocrit, high blood pressure, anxiety, no recovery, irritability. A VS badge lands on "versus". TRT · 8 HRS SLEEP: ✓ TRT, food, training, recovery. Each row ticks in on its spoken word. |
| 0:38 | **Lab range bars** (top strip) | GROWTH ▲. Cortisol and lipids markers slide from HIGH into OPTIMAL on blue/green/amber spectrum bars. |
| 0:41 | **Priority ladder** | 01 SLEEP (gold, "MOST ANABOLIC"), with a FIX bar that fills and checks. "THEN" arrow down to 02 COMPOUNDS, which stays padlocked and dim until "compounds". |
| 0:47 | **CTA end card** | Logo, "FREE · SLEEP PROTOCOL FOR ENHANCED GUYS" and a moon icon. A gold `COMMENT "SLEEP"` pill lands on "comment", then a 1 s hold with the disclaimer. |

Full panels alternate with top strips, so the face comes back at 0:11 and 0:38.

## Sound
- Clinical SFX: sub thuds on panel landings, scan sweeps on builds and strips, and digital ticks on rows.
- Impacts on "wasting", the verdict, and the VS badge.
- Speech is normalised to about −14 LUFS.

## Notes
- **Values:** Chart values (hormone curve shapes, marker positions) are **illustrative**. The only figures on screen are the ones you say: 2–3 hrs, 3 hrs, 8 hrs, plus 5 hrs lost (8 − 3).
- **Fonts:** Stand-ins.

## QC done
- **Format:** 1080×1920, 30 fps, H.264 High@4.2 with AAC 192k, faststart. 26.7 MB, 1,595 frames, 0:53.
- **Audio:** −14.2 LUFS, true peak −1.3 dBFS.
- **Visual review:**
  - Stills of every scene, plus a contact sheet at 1 frame per second.
  - 15 fps frame strips at three handoffs: clock → KPI strip, overnight → comparison, and priority → CTA.
- **Fixed during review:**
  - The hook box overlapped the panel top, so I lowered the panel to y 502 and raised the hook to y 276.
  - The 3-hour cut fired at 3.5 s; "three hours" had matched "two to three hours", so I re-cued it to "only getting three".
  - The clock legend collided with the 00 label.
  - Scene and strip overlaps at 15 s, 27 s and 41 s.
  - The CTA entered over the exiting priority panel.
- **Captions:**
  - Every word comes from a medium.en transcript of the cut audio.
  - A focused re-check confirmed "always want" and "Then fix".
  - "trend" is displayed as TREN, and numbers as digits.
- **Not done:** listening. Check the SFX balance by ear.
