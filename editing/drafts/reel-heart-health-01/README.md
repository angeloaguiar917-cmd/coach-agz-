# Reel: "Hearty health" — feel fine ≠ heart fine (720p30 preview)

**Status:** first full edit, for review. Not a final export; a final would be 1080×1920.
**Source:** Drive file `1bnuWvQ-PREV_-X_a1EvBpTZGOOnw-KIw` ("Hearty health"), 1080×1920 HEVC 60 fps, 1:53.
- It's an assembly Coach AGZ had already cut together, with existing joins at 15.95, 53.57 and 61.67 s.
- Locations: getting out of the car, then walking outside, then in the car.

**Output:** `coach-agz_heart-health_720p30.mp4`, 720×1280, 30 fps, H.264 + AAC, 1:52.6 (111.3 s of speech plus a 1.3 s end-card hold). −13.9 LUFS, peaks −1.8 dBFS.

## Saved setup applied
- **Look (test 06):**
  - Every-word captions with the red active-word block.
  - Evidence panels that grow out of and collapse into the gold edge rule, with each panel's glow fading and masked with it (the fix from the Mast/Primo edit).
  - Cyan schematics.
  - Lit verdict bar with a 2-frame shake.
  - Footage ungraded.
- **Workflow (full test 02):**
  - Vocabulary-prompted and filler-preserving transcription. The suspect lines at about 58 s ("so it's both. There's two tools") and about 72 s ("your LDL goes down. LDL goes down, your ApoB goes down") were rechecked with two models; they're deliberate phrasing, not stumbles.
  - 11 dead-air trims (≥0.22 s → about 0.12 s) plus the lead-in cut below: 1.73 s removed in total.
  - 108% punch-in alternating at every jump cut.
  - Captions from the trimmed audio.
- **Lead-in:** the source opens on a clipped "And" fragment (0.00–0.04 s). The first 3 frames are cut, and "It's the guys…" was verified intact by re-transcription.
- **Light stabilisation:** vidstab, shakiness 5, smoothing 20, to steady the car-exit opening.
- **Captions:** y ≈ 1470, on the hoodie.

## The connected element
A persistent **TOOL strip** sits under the pinned title for the whole video:
1. Two empty slots appear on "two compounds" (8.4 s).
2. They take their mechanisms on "two mechanisms": **? · APOB / LDL** and **? · LV WALL / BP**.
3. They fill with **EZETIMIBE** (62.3 s) and **TELMISARTAN** (76.3 s) as each is revealed.
4. A gold **+** links them on "two tools together" (96.4 s).

The LV heart schematic from MECHANISM 02 returns at 87.8 s for the "existing LV mass" claim.

## Timeline (trimmed timeline)
| Time | Speech | On screen |
|---|---|---|
| 0.0–7.2 | "the guys who feel healthiest on cycle… most heart damage. No pain, no warning" | **Hook title card:** kicker ON CYCLE · HEART HEALTH, then **FEEL FINE ≠ HEART FINE** (≠ turns red on "not"). PAIN · NONE and WARNING · NONE tick in, in red, as spoken. |
| 7.2 | "stay until the end" | **Handoff:** the headline moves into the pinned title. |
| 8.4 | two compounds… run them together… each fixes its mechanism | The TOOL strip appears (01 / 02 · TOOL ?). |
| 20.4–33.4 | steroids turn down LDL receptors… less cleared… ApoB climbs (particle count)… more plaque… statin works in the liver, not here | **MECHANISM 01 · LDL CLEARANCE:**<br>• A liver block whose LDL-receptor sockets retract and go red (DOWN-REGULATED).<br>• LDL particles pile up in a blood lane (LESS LDL CLEARED).<br>• The APOB meter climbs (= PARTICLE COUNT).<br>• An artery fills with plaque (PLAQUE BUILDS).<br>• A STATIN tag (ACTS IN LIVER), then the receptors are bracketed: DOESN'T FIX RECEPTORS. |
| 35.8–53.3 | not just BP: vascular resistance ↑, pressure ↑, LV wall thickens, function falls, no symptoms; lowering BP doesn't reverse the wall | **MECHANISM 02 · LEFT VENTRICLE:**<br>• A cyan LV cross-section whose wall thickens.<br>• Meters: VASCULAR RESISTANCE ▲, BLOOD PRESSURE ▲, FUNCTION ▼, SYMPTOMS: NONE.<br>• Blood pressure then drops in gold, but the wall is bracketed WALL STAYS THICK.<br>• Verdict **BP DOWN ≠ WALL FIXED**, with impact and shake. |
| 53.3–61.1 | two mechanisms, two tools | Talking head. Strip slots take their mechanisms. |
| 61.1 | ezetimibe blocks gut absorption → less reaches the liver → liver pulls LDL from blood → LDL ↓, ApoB ↓, no hormonal interference | **TOOL 01 · EZETIMIBE:**<br>• GUT → LIVER flow, with a gold gate on "blocks" (ABSORPTION BLOCKED).<br>• The liver receptors light up and the blood lane empties.<br>• LDL ▼ and APOB ▼ meters.<br>• ✓ NO HORMONAL INTERFERENCE. |
| 75.8 | telmisartan blocks angiotensin II → vessels relax → pressure, wall stress ↓ | **Scan wipe in the same panel to TOOL 02 · TELMISARTAN:**<br>• Vessel walls with angiotensin II receptors (red → gold BLOCKED).<br>• The vessel widens (RELAXED).<br>• BLOOD PRESSURE ▼ and LV WALL STRESS ▼. |
| 82.1–87.7 | no heart-rate suppression like a beta blocker… | Talking head. |
| 87.8–95.3 | hypertension studies: telmisartan can reduce existing LV mass, not just prevention | **LV MASS callback:** the same heart, with its wall thinning on "reduce", the EXISTING LV MASS meter ▼, **CAN REGRESS**, and NOT JUST PREVENTION. The header reads "HYPERTENSION STUDIES · TELMISARTAN", as Coach AGZ states it; no specific study is named or invented. |
| 95.4–100.6 | two problems, two tools together; education; bloodwork decides | Talking head. The strip links with a gold **+**. |
| 100.6–end | CTA | **End card:** logo, COACH AGZ, @coach.agz. THE FULL / **HEART HEALTH** (red) / PROTOCOL + FRAMEWORK build as spoken, then the gold **COMMENT "HEALTH"** pill on "comment" and SENT TO YOU. Disclaimer below. |

**Sound** (synthesised, `sfx.py`, 54 cues):
- Whoosh and sub thud on each panel landing.
- Scan sweeps on receptor, particle and wall changes.
- Ticks on flags.
- One heavy impact, on the verdict.
- Thuds on the ezetimibe gate, the AT2 block, CAN REGRESS, the strip link and the CTA pill.
- No music.

## Checks done
- **Paper edit:** the assembled cut was re-transcribed. All source words are present apart from the deliberately cut "And" fragment. The remaining differences are drug-name spellings varying between passes.
- **Captions vs final audio:** 379/388 match. The rest is transcriber variance: "ezetimibe" heard as "a zetimide", "II" as "too", "fellas" as "fellow", one "the/your", and the uncensored swears. Drift: median 0.00 s, p95 0.08 s, max 0.24 s.
  - Corrections: EZETIMIBE (heard as "a Z to my" and "a zetamide"), APOB, starred swears.
  - A "(static)" word hallucinated in the silent end hold was removed.
- **Frames:**
  - QC stills of every beat.
  - Frame strips at the hook handoff, strip entry, every panel open and close, the stage wipe, the verdict, the link, the end card and the pill.
  - Full decode, all 3,379 frames.
  - Chunk seams verified frame-exact.
  - No glow lingers after any panel closes.
- **Defects fixed during build:**
  - The STATIN and "doesn't fix" tags collided with the liver and blood boxes.
  - The WALL STAYS tag overlapped a meter label.
  - The angiotensin label rode up into the TELMISARTAN tag as the vessel widened.
  - A stray comma split "YOUR APOB".
- **Sound sync:** all heavy hits are within 1 ms of their visual frames.
- **Audio repair:** the source had 262 full-scale samples spread through the whole clip (61 flat-topped runs), so the clipping was baked in before upload. ffmpeg `adeclip` rebuilt only the clipped samples: 991 of 10.8 M changed, 6 flat-topped runs left. Voice +3.2 dB, then the limiter. **Needs a listen.**
- **Not done:**
  - Listening.
  - Subject cutout.
  - Real fonts (Bebas Neue, Barlow Condensed, DM Sans and JetBrains Mono are stand-ins).
- **Content:**
  - The panels depict Coach AGZ's own mechanisms and claims. No doses, lab values, study names or numbers are shown.
  - The meters and curves are illustrative.
  - The fixed disclaimer is on the pinned title and the end card.
