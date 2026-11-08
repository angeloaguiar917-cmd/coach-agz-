# Reel 03: "Real muscle on GEAR · 3 months vs 5 years" (1080p30)

**Source:** Drive `1OgV5GIAG-zA8v1fRuaqhxomiAoMcTGBc` ("Long form expect"): 1080×1920 HEVC, 60 fps, 7:45, one continuous selfie take.
**Output:** `coach-agz_realistic-muscle-gains_1080p30.mp4`: 1080×1920, 30 fps, 7:16, HEVC (hvc1) + AAC, sized under 100 MB so it downloads straight to a phone. `…_h264.mp4` is the same edit in H.264 for players that can't open HEVC.
**Style:** test-06 clinical evidence look and overlay palette, every-word captions with the red active-word block, gold left rule. The footage itself is untouched (no grade).

## Paper edit
`cut.py` holds the cut list; `timeline.json` maps every output second back to the source.

| Change | Source | Why |
|---|---|---|
| Cut "Alright boys… we gotta set the right expectations… why are you comparing yourself to somebody… 5 years on social media" | 0:49–1:03 | Repeats the "3 months vs 5 years" point already made at 0:13, and the expectations line comes again at 1:10 |
| Cut "Plus, fellas, fellas," | 1:09 | False start |
| Moved the CTA ("If you want my muscle growth tracking framework, comment GROWTH…") from mid-video to the end, before "Appreciate you guys" | 6:13 → 7:10 | It interrupted the genetic-ceiling section; a CTA lands better as the close. "That being said" dropped |
| Dead air: every silence of 0.22 s or more trimmed to about 0.12 s | throughout | 66 frame-aligned pieces, 8 ms audio crossfades |

## Text hook (engine run, see `edit_log.json`)
**Real muscle on GEAR / 3 months vs 5 years** (subject + outcome). Frame 0, held to 3.3 s, 0.15 s fade, then the topic band.

## Overlay map: 26 moments, 5 layouts, no layout used twice in a row
Layouts:
- **Top strip:** glass strip over the wall and cap. The face stays live.
- **Panel:** frosted panel over blurred footage.
- **PIP:** the footage shrinks into a framed "LIVE" window on brand navy, then expands back.
- **Corner card:** crimson-bar overlay card.
- **Full takeover:** the graphic fills the whole frame.

| Time | Layout | Graphic type | What it shows |
|---|---|---|---|
| 0:03 | Top strip | Waffle chart | 100 lifters, 70 fill red: "TRT / GEAR 70 · NATURAL 30" |
| 0:12 | Top strip | Timeline bars | YOU 3 MO vs HIM 5 YRS on a months axis, bloodwork ticks, "20× THE TIME" |
| 0:23 | Panel | X-ray schematic + dual sparkline | Muscle cross-section swells with H2O, then glycogen; tissue line SLOW vs scale line FAST; verdict "SWELLING ≠ NEW TISSUE" |
| 0:36 | PIP | Step chart + load meters | Dose steps up while gains plateau; heart and kidney load bars go red |
| 0:48 | Corner card | Digital readout | Scale counts to +15.0 LB, flagged "≠ PRO STAGE" |
| 1:03 | Full takeover | Dot field | 10,000 lifters, one lights up: "1 IN 10,000" |
| 1:08–4:02 | Top band | Chapter tracker | 3 MO · 6 MO · 1 YR · 5 YR, active chapter lit gold; hands off into the results chart |
| 1:13 | Top strip | Checklist | Training, nutrition, recovery, health monitoring tick in; "LOCKED IN 24/7" |
| 1:21 | Corner card | Sparklines | Strength, fullness, bodyweight rising |
| 1:29 | Panel | Document scan + stacked bar | Trial summary (+13.4 lb FFM, 10 wk), then what that mass is made of; MUSCLE segment hatched "UNMEASURED"; AR / MPS / hypertrophy chips |
| 1:55 | PIP | Vertical bar chart | 10 WK 13.4 vs 20 WK ~17; top of the bar hatched "NOT ALL TISSUE" |
| 2:12 | Panel | Line chart projection | Real log curve vs a red dashed "if it kept accelerating" line that runs off the chart to 600 LB; "PROJECTION ≠ PHYSIOLOGY" |
| 2:33 | Top strip | Block stack | Year-1 drivers drop in one by one; training age bar fills |
| 2:48 | Crimson card | Mechanism flow | Tension → mTOR → MPS → hypertrophy |
| 2:56 | PIP | Bell curve | 12-week gain distribution; 20–30 LB zone flagged "NO STUDY"; social-media outlier; genetics, history and size chips |
| 3:15 | Top strip | Diminishing bars + compounding maths | Gain per year Y1–Y5 shrinking, cost per lb rising; "15 LB every 3 MO × 20 quarters = +300 LB" ✕ |
| 3:44 | Panel | Area chart + monitor rows | Cumulative CV load rising while every year's labs and EKG pass; HCT, lipids, BP, kidney, heart rows tagged TRACK |
| 4:02 | PIP | **Range bar chart (hero)** | 3 MO 3–8 · 6 MO 5–12 · 1 YR 10–20 · 5 YR 20–40 LB, assumptions ticked |
| 4:42 | Corner card | Strip plot | First-cycle gains cluster; a +40 LB outlier flagged; "AVERAGE MALE" band |
| 5:01 | Top strip | Gantt | 10 years of on/off blocks; "STILL BUILDING" |
| 5:23 | Panel | Comparison columns | Client wants +20–30 ✕ vs realistic +5–12 ✓; DAY 90 vs YEAR 5 bars; "KEEPABLE > FAST" |
| 5:37–5:50 | None | Slow push-in | Room for the heavy line ("…leave your kids with no father") |
| 5:52 | PIP | 2×2 quadrant | Response × tolerance; marker lights hyper-responder, then hyper-tolerator, then BOTH "1 OF 1 · ELITE" |
| 6:07 | Panel | Race bars + checklist | Hyper-responder on a low dose vs Coach AGZ with everything locked; "¼ THE GROWTH", "4×" |
| 6:50 | Top strip | Signal schematic | Input waveform → GEAR amplifier → output, average vs elite |
| 6:58 | Corner card | Donut | 80–85% ring "without elite genetics", "↑ STILL PROGRESS" |
| 7:10 | End card | PIP + logo | "FREE · MUSCLE GROWTH TRACKING FRAMEWORK", gold COMMENT "GROWTH" pill |

**Camera:**
- Alternating 100% and 108% framing at every jump cut.
- Punch-in to 116% on "explode", 112% on "I'm sorry bro, but you're not".
- Slow 100→112% push through the heavy closing line.

**Sound:** synthesised clinical SFX (`sfx.py`, 90 events). Scan sweeps on strips and panels, a whoosh into a thud on PIP, ticks on checklist rows, a sub thud on each reveal bar, and one impact per verdict bar and on the 1-in-10,000 cut. Speech normalised, final mix about −14 LUFS.

## Changes from the saved setup (and why)
- **Captions moved down to y≈1398** (from 1335). In this framing the mouth and chin sit around y 1200–1400, so the old position covered his mouth. They're now just under the chin and still above the bottom UI zone.
- **The chapter tracker stays at the top past the midpoint** (until 4:02, vs a 3:38 midpoint). It's the navigation for the 3 mo → 5 yr breakdown and hands off into the results chart. Flagged in `edit_log.json`.
- Text hook in Barlow Condensed ExtraBold (stand-in), because Bebas has no lowercase and engine rule 8 needs sentence case.

## QC done
- **Cut:**
  - The edited cut was re-transcribed with Whisper medium. Every word was heard, and the text matches the plan.
  - One join clipped the onset of "Like" (6:13); I moved it back 1 frame, measured on the waveform.
  - 13,093 frames = 436.43 s, exactly.
- **Captions:** built from that transcript, with times remapped through source time after the join fix. Corrected:
  - androgen (heard as "antigen")
  - supraphysiological
  - 13.4
  - "1% of 1%"
  - Even
  - in optimized
  - we're
  - you'll
- **Visuals:**
  - Stills at every scene, a contact sheet every 4 s of the rendered master, and 15 fps frame strips at PIP in/out, panel handoffs, corner-card entry, the dot-field cut, the push-in and the CTA.
  - Fixed during review:
    - label collisions (dose/gains, 600 LB, quadrant under the PIP window, bell-chart axis, 5 YR value)
    - waffle cells blooming into a block
    - panels that sat empty for 1–5 s before their first item (now they open with a skeleton)
    - glow lingering after a graphic faded (an orange streak over the face on PIP exit)
    - PIP chart content showing over the expanding window
    - the slow push-in running 93 s instead of 13 s
  - Render chunk seams checked: frame-exact.
- **Delivery file:** HEVC Main, hvc1 tag (plays in iOS Photos and Safari), 1080×1920 30 fps, 1.58 Mbps two-pass + AAC 128k, faststart. SSIM 0.966 against the master on a graphics-heavy frame; text is crisp at full size.
- **Audio:** −14.4 LUFS integrated, peak −0.9 dBFS. SFX hit on their cue frames by construction (placed from the same cue table the graphics use).
- **Not done:** listening. I can measure levels but can't hear the mix, so check the SFX balance by ear.

## Check before posting
- **Citations** on the two trial cards ("Bhasin et al. · NEJM 1996 · 600 mg/wk" and "Bhasin et al. · 2001") were added by me to match the numbers you quote (13.4 lb in 10 weeks, ~17 lb in 20 weeks). Please confirm them.
- **Illustrative data, labelled as illustrative on screen:**
  - the fat-free-mass split
  - the bell curve
  - the gain-per-year bars
  - the 10-year on/off blocks
  - the risk area
  - the dose/plateau chart
- **Your own spoken figures:** 70%, 1 in 10,000 (your "1% of 1%"), ¼ the growth, 80–85%, and the 3–8 / 5–12 / 10–20 / 20–40 lb ranges.
- Fonts are free stand-ins (Bebas Neue, Barlow Condensed, DM Sans, JetBrains Mono).
