# Full test 02: "Anavar vs a six pack" (1080p)

**Source:** Drive `1_PmKSkcV3GwJy2QDJa2MrI1YUm_QElEF` ("RAW Ai TEST: Var v 6pack"), 1080×1920 HEVC, 60 fps, 4:45 car selfie with many retakes.
**Output:** `coach-agz_anavar-vs-six-pack_1080p.mp4`. Not committed (79 MB); sent in chat.
- Video: 1080×1920, 30 fps, H.264 High@4.2, 4.5 Mbps, fast-start.
- Audio: AAC 192k, about −14.6 LUFS, true peak −1.5 dBFS.
- Length: 2:14.

## Brief (Coach AGZ, 2026-11-21)
- Use the saved setup and style; 1080p, downloadable to a phone.
- Use **different overlay types**, with no repeating one panel style the way full test 01 did.
- Keep the face recognisable.
- More graphs and graphics: vibrant, on brand, eye-catching.
- Add a visual hook.

## What changed vs full test 01
- **No full-frame blur/darken behind graphics.** The face sits at y≈560–1380, so graphics live in three places:
  - the dark headliner above the cap (the "top dock", y 284–664);
  - side tiles over the seats;
  - one corner-circle PiP scene.
- **Captions moved below the chin** (y≈1392).
- **One overlay type per beat.** Nothing repeats back to back, and the only deliberate repeats are handoffs: the agenda tracker returns at "now we simplify", and the natural-T switch returns at "suppresses your testosterone".
- **Compositing fix:** fades and translucent fills now actually blend. Earlier renders drew straight onto an RGBA frame, where Pillow overwrites rather than blends, and Pillow 12 also ignores text alpha. So exits popped and dimmed elements were full strength.

## Paper edit (`keep.json`, 25 pieces, source seconds)
| Source | Line |
|---|---|
| 0:00 | Hook: 50 mg Anavar vs a six pack, which is worse |
| 0:08 | "Break it down by science and mechanics…" |
| 0:29 | Third take: neither safe, same three systems |
| 0:43 | First take: "Everyone calls it mild…" |
| 0:53 / 0:57 | Liver vs other orals, HDL/ApoB (repeat of "crushes your HDL" removed) |
| 1:04 | ApoB, BP, natural T shut down, no test base |
| 1:17 / 1:33 | Six pack = 80 g; liver clears it first; fat, GGT, trigs, visceral (duplicate "fat builds up" removed) |
| 1:44 / 1:53 | Carcinogen and poison (stumble removed); "same three systems, different weapons" |
| 2:13 | Third simplify take; Man A on Anavar |
| 2:28 / 2:36 | "very different than" then the clean "guy ripping six packs" take, through "liver failure" |
| 3:03 / 3:14 | Gas station, then "totally illegal" (aborted "a f…" line removed) |
| 3:22 / 3:37 | Visible vs six years; retake of "pooping out your liver and your kidneys" |
| 3:58 / 4:04 | Roadmap: "you do not guess", then "you test, you analyze, you pivot, you optimize" (doubled "you" removed) |
| 4:10 | CTA with "absolutely free" (the 4:30 take drops "free") |

Silences of 0.25 s or more inside a take are trimmed to about 0.12 s. Pieces alternate 100% and 108% framing to hide the jump cuts.

## Overlay map (edited-cut time)
| Time | Type | Content |
|---|---|---|
| 0:00 | Text hook (frame 0) | "50mg ANAVAR vs 6 beers / both hit the same 3 systems" |
| 0:01–0:07 | **Visual hook:** VS contender cards plus a 110% punch-in on "Anavar" | Card A: 50 mg every day, tablets drop in. Card B: six pack every night, cans drop in. "WORSE ?" tags on "worse". |
| 0:08 | Agenda tracker (pills) | 01 Science + Mechanics, 02 Simplify, 03 Optimize |
| 0:11 | Ring-gauge triad (HUD) | Liver / Lipids / Testosterone rings fill red as named; VAR and ALCOHOL attack lines; "VAR SOLO · NO TEST BASE" |
| 0:23 | Dual-needle dial (crimson card) | Reputation needle on MILD; lipid needle whips to HARSH |
| 0:27 | Ranking bar chart | Liver strain, relative: Anadrol, Dbol, Winstrol, Anavar |
| 0:30 | Column chart + ECG | HDL collapses, ApoB climbs; arrow to heart, then an ECG trace draws |
| 0:38 | Side monitor tiles | BP LED meter rising; natural-test switch flips OFF; "test base: EMPTY" |
| 0:47 | Pictogram + count-up | Six cans drop, compress; 80 G counts up |
| 0:51 | Document slap | Rx label: ETHANOL 80 g, take 6 after work, refills unlimited |
| 0:53 | Priority queue | Liver processing queue: alcohol jumps to 01, fat burning on hold |
| 0:55 | X-ray + sparklines (evidence panel) | Liver outline fills with fat; GGT / triglycerides / visceral fat tickers |
| 1:02 | Hazard placard | WHO IARC Group 1 carcinogen (same group as tobacco, asbestos); POISON |
| 1:05 | Side tile recall | Natural-test switch flips OFF for alcohol |
| 1:07 | Radar chart | Damage profile: VAR vs ALCOHOL on liver / lipids / testosterone |
| 1:11 | Agenda tracker returns | 02 Simplify lit (handoff) |
| 1:16–1:33 | **PiP scene** (navy carousel look; face shrinks into a gold-ringed circle) | Two timelines. Man A: panels every 8 weeks, HDL drop caught, corrected. Man B: no data, years tick 0 to 5, hospital icon, verdict bar "FIRST DATA POINT: LIVER FAILURE" |
| 1:37 | Paper documents | Gas-station receipt (Rx none, bloodwork none), stacking up on "every single day"; Schedule III sheet stamped ILLEGAL |
| 1:42 | Tall body-scan tile | Visible (tracked dots) vs fog with a year counter; scan reveals the liver, then the kidneys, in red |
| 1:56 | Roadmap path | Guess (struck), Test, Analyze, Pivot, Optimize |
| 2:02 | CTA card | Oral-cycle bloodwork panel checklist ticks in, FREE tag, then a gold COMMENT "PANEL" bar |

Persistent elements:
- Gold left rule, with the disclaimer running vertically along it.
- Topic band "ANAVAR vs a six pack" from the end of the hook to the midpoint (1:07).
- Every-word captions with a red active-word block; "f*cking" is censored.

## Checks done
- **Cut:** re-transcribed (medium.en). One doubled "you" at the take join (1:58) was found and removed. "By its eyes" was re-checked in isolation as "by science".
- **Visuals:** stills at every overlay, plus 10 fps frame strips around the hook, card entries, stage swaps, the Rx slap, the queue jump, the hazard, the PiP entry/exit, the stamp, the body tile and the CTA swap.
- **Defects fixed during build:**
  - Hook text bloom.
  - Ring triad too low on the cap.
  - ApoB bar running into the card's kicker text.
  - "VS" flash colliding with captions (removed, along with its impact sound).
  - CTA rows showing through the comment bar.
  - Global alpha bug, so fades now work.
- **Audio:** −14.6 LUFS, true peak −1.5 dBFS. SFX placed on landing frames in code. **Not listened to.**
- **Not done:** listening. Fonts are stand-ins (Bebas Neue / Barlow Condensed / DM Sans / JetBrains Mono via fontsource).
- **Illustrative values:** the relative liver-strain bars, radar shape values, receipt and document details.
