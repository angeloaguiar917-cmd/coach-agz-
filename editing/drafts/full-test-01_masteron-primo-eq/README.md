# Full test 01: "Masteron · Primo · EQ are not an AI" (720p30 preview)

**Source:** Drive `1AnR6bfMBKQJ_kEk481RQTZ0jXHrMe3Da` (1440×2560 HEVC, 60 fps, 3:10, walking selfie with several retakes).
**Output:** `coach-agz_masteron-primo-eq_full-test_720p30.mp4`, 720×1280, 30 fps, 1:43, −14.2 LUFS, true peak about −1.5 dBFS.
**Status:** full-length test of the test-06 style. It isn't an approved Signature Style and isn't a final export; a final would be 1080×1920.

## Paper edit (best take of each line)
`segments.json` holds the source in/out points.

| # | Source | Line |
|---|---|---|
| 1 | 0:01 | Hook ("…not fucking aromatase inhibitors") |
| 2 | 0:09 | "Here's the exact mechanism…" |
| 3 | 0:30 | AI definition; the false start "So an aromatase inhibitor, so…" is trimmed |
| 4 | 0:44 | DHT derivatives competing for two receptors |
| 5 | 0:59 | AR pull; aromatization still on |
| 6 | 1:21 | EQ, the clean retake: parked in E1 |
| 7 | 1:29 | E2 drops, total load can stay elevated |
| 8 | 1:40 | "Number moved, pool doesn't shrink" |
| 9 | 2:06 | "In basic terms", the third and cleanest take, plus the factory line |
| 10 | 2:32 | Bloodwork, cut after "water retention" |
| 11 | 2:50 | Roadmap |
| 12 | 2:59 | CTA |

Cut: the first EQ attempt, three "in basic terms" retakes, the duplicate hook, "and so on and so forth", and the alternate "turn off the aromatization" line.

## Graphics (clinical evidence style, test-06 overlay palette, footage untouched)
- **0:00 Hook tag** "COMPOUND · CLASS": Masteron and Primobolan DHT-derived, Equipoise test-derived. "AROMATASE INHIBITOR? NONE" lands on "aromatase".
- **0:09 Mechanism 01:** T → aromatase → E2 flow. An AI chip blocks the enzyme ("ENZYME BLOCKED") and E2 output drops. The compounds are shown with "ENZYME UNTOUCHED" and the flow resumes.
- **0:21 Mechanism 02:** aromatization ON. Masteron and Primo marked DHT-derived, with no aromatization and no enzyme block. AR/ER receptor docks: AR fills to 84% and ER drops to 17%, flagged UNDER-OCCUPIED. Then BINDING CHANGED and PRODUCTION UNCHANGED.
- **0:48 Mechanism 03:** the flow splits to E1 and E2 and shifts to E1 (WEAKER). E2 on the panel reads LOW, but the total pool stays STILL ELEVATED: NUMBER MOVED, POOL UNCHANGED.
- **1:03 Summary:** cards for "where it lands" and "which form"; the aromatase factory RUNNING, NOT TAKEN DOWN, NOT TURNED OFF.
- **1:14 Bloodwork:** a generic lab report with E2 sensitive 14 L and total T 1,850 H, tagged READS LOW then NOT PROOF, against ACTUAL OUTPUT HIGH. "+ AI" is blocked with CONFIRM FIRST. Checklist: data, symptoms, side effects, water retention.
- **1:31 Roadmap:** an E2 trend chart draws, trend ↑, symptom checks, then the verdict slam "TREND + SYMPTOMS = THEN DECIDE".
- **1:37 CTA:** logo, "FREE · ESTROGEN MANAGEMENT FRAMEWORK", and a gold COMMENT "ESTROGEN" bar on "comment".
- **Throughout:** pinned title "MASTERON · PRIMO · EQ ARE NOT AN AI", every-word captions (drug names corrected), and alternating 108% punch-ins per take on talking-head shots.

## QC done
- **Cuts:** the assembled cut was re-transcribed; nothing was clipped, and one false start was found and trimmed.
- **Captions:** built from a vocabulary-prompted transcript of the cut. The final audio was re-transcribed: 352/352 words.
  - A focused re-check confirmed "androgen receptor" where the long-form pass misheard it.
  - Timing drift: median 0.0 s, max 0.14 s after fixing "absolutely" (0.62 s off).
- **Chunk seams:** frame-exact, verified against source frames.
- **Visuals:** an overview every 1.5 s, and frame strips at every panel in/out, the hook-tag exit, the verdict and the CTA.
- **Layout fixes during build:**
  - Missing arrow glyphs.
  - Title wording.
  - Tag collisions on Mechanism 02, the EQ pool and the lab report.
  - A stray flag stub.
- **Sound sync:** the panel hit, AI-block impact, lab thud, verdict impact and CTA thud were each detected within 1 ms of their target frames.
- **Not done:** listening. All lab and document values are illustrative placeholders. The fonts are stand-ins.

---
## Version 02: tightened (`coach-agz_masteron-primo-eq_full-test-02_720p30.mp4`, 1:37.2)
Feedback on v01: there were still dead spots needing jump cuts, and misspoken parts to cut.
- **Misspeaks removed** (found with a filler-preserving transcription pass; the clean transcript had hidden them):
  - At about 0:19, the abandoned first "When we take a look at… it, Mast-"; the clean restart is kept.
  - At about 0:51, the repeated "E1 has, E1 has"; "E1 has weaker…" is kept.
- **Dead air:** 0.45 s of lead-in, and every silent run of 0.22 s or more trimmed to about 0.12 s. That's 20 frame-aligned cuts, 6.2 s removed in total, with 8 ms audio crossfades.
  - One trim was dropped deliberately because it fell on the soft tail of "takes".
- **Punch-in** alternates at every jump cut, both take changes and trims.
- **Graphics and SFX** are remapped through the trim: each output frame draws overlays at its original speech moment. All SFX survived; none fell inside a cut.
- **Captions** were rebuilt from a transcript of the trimmed audio (the old caption times had pointed at the removed takes, and five words had been dropped).
  - "absolutely" and "and" were corrected by speech-energy onset.
- **QC:**
  - 352/352 caption words against 353 heard; no stumbles remain.
  - Caption drift median 0.00 s, p95 0.06 s.
  - The only pauses left are about 0.22–0.26 s around "takes. Neither".
  - −14.1 LUFS.
  - Cut frames inspected. Mechanism 01 now exits on a hard cut (its old blur-out was inside the removed stumble).
