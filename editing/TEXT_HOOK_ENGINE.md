# ON-SCREEN TEXT HOOK ENGINE

Run this on every video edit, before rendering anything else. The text hook (title text) is the overlay on screen from frame 0. It is the highest-leverage element in the edit and works as a second, independent hook layer next to the spoken hook and the visual hook.

---

## 1. Gather inputs first

- Word-level transcript of the **edited cut** (not the raw take)
- **Spoken hook**: everything said before the first natural pause (usually 0:00–0:04)
- **Lock-in zone**: the 2–4 sentences right after the spoken hook (roughly 0:04–0:12)
- **First frame**: where the face and eyes sit, how busy or bright the background is
- `hooks/winners.md` if it exists: top-performing title texts and power phrases mined from Sandcastles exports. If it exists, pattern-match against it. If not, use the rules below and note that the file is missing.

## 2. Extract the raw material

Pull these from the transcript:

- **SUBJECT**: the proper noun, compound, biomarker, or technical term (Primo, ApoB, Cystatin C, hematocrit, GH). This is the attention magnet.
- **PAIN**: the problem the video solves or warns about
- **OUTCOME**: the result the viewer wants
- **STATE CHANGE**: anything new that changes how this works going forward
- **SPECIFICS**: every number, dose, timeframe, lab value, or count said in the video

If the transcript has no specific number, do not invent one. Never fabricate a stat, value, or claim. Every word on screen must be something the video actually delivers.

## 3. The formula

**TEXT HOOK = SUBJECT REPEATER + exactly ONE of:**

- **A. Pain point reminder**: names the problem being avoided
- **B. Dream outcome teaser**: names the result the viewer wants
- **C. Future state change**: signals something new changed how this works

Every hook must open a curiosity gap. The viewer knows the problem or the prize, not the answer. The answer lives in the video.

Fallback for story or non-technical videos with no named subject: use an identity callout as the subject (Enhanced lifters, Anyone on TRT, Your first cycle) plus A, B, or C.

## 4. Hard rules (any violation = rewrite)

1. **Two lines max.** Three lines only in Premium mode (section 7) with one dominant line. Never three equal lines.
2. **Break lines on natural phrase units** (section 6).
3. **No punctuation** except quotation marks and parentheses. No periods, commas, question marks, exclamation points, colons, dashes, em dashes, or ellipses. Not punctuation, so allowed: hyphens inside a name (BPC-157, GT-20029, hs-CRP, IGF-1), apostrophes inside a word, and number symbols ($ % +).
4. **No connecting words**: and, or, but, so, that, which, because, therefore, however, then, while, although. These are trigger phrases, not sentences. This bans grammatical connectors only. Compound names (Test, Primo, Deca, Tren) are subjects and always allowed.
5. **Specific beats vague.** "22 days" beats "a few weeks." "500+ panels" beats "hundreds of panels." Use the exact figure from the transcript.
6. **Compress with power phrases** (section 5). Turn a sentence into a 1–3 word punch.
7. **Glance-readable**: 3–11 words total, max 26 characters per line, readable in under 1.5 seconds.
8. **Emphasize the subject**: ALL CAPS plus brand accent color. Everything else in white, sentence case. Keep standard casing where casing carries meaning (ApoB, hs-CRP); emphasize those with color only.
9. **Align with the spoken hook, don't transcribe it.** Same subject, same promise, compressed. If the spoken hook already states the subject, the text hook adds the pain, outcome, or state change the spoken line doesn't.
10. **No weak words**: very, really, actually, literally, basically, amazing, game changer, secret sauce, you won't believe, must watch.
11. **Stay on the video's topic.** Never swap in a different compound, marker, or angle the video doesn't cover.

## 5. Power phrases

A power phrase is a 1–3 word bundle that amplifies a pain or outcome and compresses a full sentence into a punch.

**Mining:** read `hooks/winners.md` top-down by views. Pull phrases that carry extra charge. A phrase that shows up in more than one top performer is double-validated; prioritize it.

**Remix, never copy.** Keep the psychology, swap the words.

- "the marker nobody checks" → "the lab your doctor skips" / "the number gyms ignore" / "the test nobody orders"
- "silently wrecking your kidneys" → "quietly killing your kidneys" / "slowly cooking your liver"

**Final hook = winning format (twisted) + power phrase (twisted) + this video's subject.**

Starter bank (replace with mined phrases as the winners file grows): nobody checks · your doctor misses · silent damage · red flag · the real reason · wrong number · hidden cost · stop guessing · read it right · non-negotiable

## 6. Line break test

Read the hook out loud. Break where you'd naturally breathe. Never separate an article from its noun, an adjective from its noun, a number from its unit, a compound or marker name, or a fixed phrase.

- ✅ ApoB just replaced / your cholesterol test
- ❌ ApoB just replaced your / cholesterol test
- ✅ Your doctor misreads / TESTOSTERONE labs
- ❌ Your doctor / misreads TESTOSTERONE labs

## 7. Typography modes

**NATIVE (default):** one size for both lines. Clean bold sans, white with a dark stroke or soft shadow, or white text on a black rounded box. Two lines max.

**PREMIUM (brand):** condensed brand font matching the existing graphic cards. Three lines allowed only if one line is clearly dominant (at least 1.8× the size of the others) and the rest are accent lines.

**Both modes:** subject term in brand accent color. If any part of the text loses contrast over the brightest area of the background, add a stroke, shadow, or box.

## 8. Placement

- Upper third, centered, above the face. The viewer goes eyes → up to the text → back down. Never cover the eyes or mouth.
- Safe zone at 1080×1920: keep text clear of the top 250px, bottom 420px, right 140px, left 60px.
- Word-synced captions stay low and never overlap the text hook. The text hook is the dominant element during its hold.

## 9. Timing

- **Fully visible on frame 0.** No typewriter effect, no word-by-word reveal, no delayed entry. This also makes it the cover frame.
- **Hold:** minimum 3.0 seconds. Default end = the later of 3.0s or the end of the spoken hook + 0.5s. Cap at 6.0s.
- **Exit:** 0.15s fade, or a hard cut on a jump cut.
- Never pull the text hook before 3.0s for any reason. If a card or B-roll enters early, the text hook stays on top.

## 10. Visual hook alignment

- The first zoom punch-in or movement lands on the spoken subject word, within the first 1.5s.
- If the opening frame is static, add one small move: a punch-in, a lean, or a slow 100→104% scale on the text over its hold.
- One move is enough. Don't stack effects.

## 11. Lock-in zone check

After picking the winner, read the lock-in zone (the 2–4 sentences after the spoken hook).

- **Claim confirmation:** does it pay off the exact promise of the text hook? If not, rewrite the hook to match what the video delivers. No bait and switch.
- **Trust anchor:** is there proof in that window (a lab value, a panel screenshot, the 500+ panels reviewed, a study, a client result)? If not, flag it and suggest a proof card from available assets for that window. Never invent proof.

## 12. Workflow and output

1. Write 5 candidates, at least one each from formulas A, B, and C.
2. Check each against section 4. Discard any with a violation.
3. Score survivors 1–5 on: subject clarity, curiosity gap, specificity, power phrase strength, glance-readability, spoken-hook alignment. Pick the highest. On a tie, pick the more specific one.
4. Run the lock-in check (section 11).
5. Write this block to the edit log, then render the winner:

```json
{
  "text_hook": {
    "formula": "subject+pain | subject+outcome | subject+state_change",
    "lines": ["High HEMATOCRIT", "do this before phlebotomy"],
    "emphasis": ["HEMATOCRIT"],
    "mode": "native | premium",
    "start": 0.0,
    "end": 3.6,
    "position": { "anchor": "top-center", "y_px": 300 },
    "animation_in": "none",
    "animation_out": "fade_0.15s"
  },
  "runners_up": [
    ["line 1", "line 2"],
    ["line 1", "line 2"]
  ],
  "lock_in_check": {
    "claim_confirmed": true,
    "confirmed_at": "0:05",
    "trust_anchor": "panel screenshot at 0:07 | MISSING"
  },
  "flags": []
}
```

6. In chat, report only: the winning lines, two runners-up, and any flags.

## 13. Examples (enhanced athlete niche)

| Line 1 | Line 2 | Formula |
|---|---|---|
| High HEMATOCRIT | do this before phlebotomy | Subject + Pain |
| Keep your hair | on MASTERON | Subject + Outcome |
| CYSTATIN C just replaced | your kidney test | Subject + State change |
| 500+ BLOODWORK panels | same red flag every time | Specific + Subject + Pain |
| Protect your brain | on TREN | Subject + Outcome |

**Fixes:**

- ❌ "Here's why your doctor is reading your testosterone labs wrong!" (full sentence, punctuation, no compression)
  ✅ Your doctor misreads / TESTOSTERONE labs
- ❌ "ApoB matters more than cholesterol, and here's why" (comma, connector, vague)
  ✅ ApoB beats / total cholesterol
- ❌ TREN / IS WRECKING / YOUR BRAIN (three equal lines, nothing emphasized)
  ✅ Protect your brain / on TREN

---

## Implementation notes (how this fits the existing @coach.agz edit)

- **Edit log location:** write the section 12 JSON block to `editing/drafts/<video-folder>/edit_log.json` (key `text_hook`), next to that video's render files.
- **Order of work:** cut the video first (takes, stumbles, dead air), transcribe the edited cut, run this engine, then build captions and graphics and render.
- **Accent colour:** the subject term uses the brand overlay gold (`v-gold #FFC21A`, see `brand/BRAND.md`). Premium mode uses the brand condensed headline font (Bebas Neue stand-in until the real font file is supplied).
- **Replaces the old pinned title for the first 3–6 s.** Earlier tests used a title band pinned at the top for the whole video (`MASTERON · PRIMO · EQ ARE NOT AN AI`). That band is all caps, so it breaks rule 8 (only the subject in caps), and it starts with a slide-in, so it breaks rule 9 (fully visible on frame 0). From now on the frame-0 text hook follows this engine. After the hook exits, a small topic band returns at the top and stays until the video's midpoint. From the midpoint on, the top of the frame stays clear. This is a testing setting (Coach AGZ, 2026-11-03), so revisit it once results come in.
  - The band is a compact strip in the old title's position (y ≈ 212–372), styled to rule 8: subject in caps plus accent colour, the rest sentence case.
  - It enters as the hook fades (0.15 s) and exits with a 0.15 s fade at the midpoint, or on the nearest jump cut.
  - **The band must never deliver the payoff** (Coach AGZ, 2026-11-09). Its job is retention: it restates the open question, not the answer. If the video reveals items (a list, a ranking, the "last one"), the band shows them as **locked slots**. Each slot unlocks only when that item is spoken, and the payoff item stays locked until its reveal. Never put the answer list in the band text. Reference: `editing/drafts/reel-03_e2-compounds/` ("3 compounds for E2" with slots 01 / 02 / 03; 03 stays red and locked until "Equipoise" at 0:56).
- **Captions vs hook:** captions already sit low (y ≈ 1335 in 1080-space) and the hook sits in the upper third, so they don't overlap.
- **`hooks/winners.md`:** this file doesn't exist yet. See `hooks/README.md`. Until it's built from Sandcastles exports, flag `winners.md missing` on every run and use the starter power-phrase bank.
