# Reel edit prompt: copy, fill in the [brackets], paste

---

Edit this Reel for @coach.agz using my saved setup and style.

**Source footage:** [Google Drive link or file ID]
**Topic / compound:** [e.g. Tren, hematocrit, Anavar]
**CTA comment keyword:** [e.g. "ESTROGEN"]
**Anything specific to show:** [optional: numbers, labs or comparisons I mention that must be visualised]

### 1. Follow my saved setup (in this order)
1. Read `CLAUDE.md`, `editing/QUALITY_STANDARD.md`, `editing/brand/BRAND.md` and `editing/TEXT_HOOK_ENGINE.md` before you start. Look at the images in `editing/brand/reference/` and use `editing/drafts/full-test-01_masteron-primo-eq/` (v02) as the workflow reference.
2. **Cut first.** Pick the best take of every line, remove retakes, false starts, misspeaks and repeated words (use a filler-preserving transcription pass so stumbles aren't hidden), and trim every silence of 0.22 s or more down to about 0.12 s with short audio crossfades. Alternate a 108–115% punch-in at each jump cut.
3. **Transcribe the edited cut**, then run the Text Hook Engine: frame-0 hook, fully visible on frame 0, held 3–6 s, then the topic band until the midpoint. Write the JSON block to this video's `edit_log.json`. In chat, give me only the winning lines, two runners-up and any flags.
4. **Captions:** every word, timed to the trimmed audio, drug and marker names spelled correctly, placed low (about y 1335) and clear of the face and Instagram UI. Accent words recolour when spoken.
5. **Sound:** clinical SFX only (sub hits, scan sweeps, digital ticks, one heavy impact per beat), synced to the visual landing. Speech at about −14 LUFS, true peak under −1 dBFS.
6. **Ending:** branded end card with my comment keyword as a large gold tag pill.

### 2. Overlays: variety is required this time
Overlays depict the point. They don't quote my words, they stay clinical and aggressive, and they're never cartoonish. Use the high-pop overlay palette (`#FF221C` red, `#FFC21A` gold, `#00E5FF` cyan, `#1EFF6E` green for OK only, brand gold `#C9A96E` for the edge rule and titles), with bloom on edges and lines. Make them vibrant, eye-catching and on brand.

Pick from this menu and **mix the types**:

| # | Overlay type | Use it for |
|---|---|---|
| 1 | **Line / trend chart** that draws on, with a marker riding the line | Levels over time, a cycle or a recovery |
| 2 | **Bar chart** with bars racing up, one bar going red | Comparing compounds, doses or markers |
| 3 | **Gauge / dial** with the needle sweeping into a red zone | One marker's risk level (HCT, BP, E2) |
| 4 | **Spectrum scale** (blue / green / amber) with a sliding marker | Low / dialled-in / high |
| 5 | **Donut or ring chart** filling to a % | Receptor occupancy, percentages |
| 6 | **Bell curve / distribution** with "you are here" | Genetics, responders, normal ranges |
| 7 | **Big stat counter** that counts up and lands hard | The single key number |
| 8 | **Mechanism flow diagram** (boxes, arrows, a blocked step) | How the compound or pathway works |
| 9 | **Two-column comparison** with rows ticking ✓ / ✕ | X vs Y, what they say vs what happens |
| 10 | **Lab report / document panel** with red detection brackets | Bloodwork values, flags |
| 11 | **X-ray / cyan schematic scan** | Organs, vials, anything "inside" |
| 12 | **Checklist** ticking in with speech | Fixes, steps, protocols |
| 13 | **Schedule / dose table** | Weekly protocol, timing |
| 14 | **Kinetic keyword behind my head** (subject cutout, big Bebas word) | One punch word on a key line |
| 15 | **Shoulder tag / chips** (small, beside me) | Quick labels without leaving the talking head |
| 16 | **Full-screen navy/gold carousel scene** | A section title or a big reveal |

Variety rules (check before rendering):
- Use **at least 7 different overlay types** in the Reel, including **at least 3 different chart types** (from 1–7).
- **Never use the same type twice in a row**, and no type more than twice in the whole Reel.
- Alternate the size and placement: full panel, half-screen, a small tag on the shoulder, behind the head. Don't park every graphic in the same centred box.
- Vary the entrances as well (draw-on, count-up, scan wipe, focus pull, slide-and-settle, slam), and give each object its own weight.
- Use handoffs so one graphic turns into the next (a bar becomes a divider, a panel frame persists into the next scene).
- Give me a list of the overlays with timestamp, type and what it depicts before the final render, so I can see the variety.
- No numbers I didn't say. If a value is illustrative, label it as a placeholder in the notes.

### 3. Keep my face recognisable
- **Don't grade, saturate or add contrast to the footage.** Vibrance goes on the graphics only.
- Overlays never cover my eyes or mouth. Put cards beside me, below my chin or behind my head (subject cutout), not over my face.
- Dim the footage behind a graphic at **40% at most**, and keep the dim off my face (use a side or bottom gradient instead of a full-frame push).
- My face must be clearly visible for **at least 60% of the runtime**. A full-screen scene lasts no more than about 4 s, or keeps me visible in a picture-in-picture window.
- Check cutout edges around the head and hat in motion.

### 4. Export: 1080p, downloadable to my phone
- **1080×1920, 9:16, 30 fps** (or the source frame rate if it's 30 or below). Render at full 1080p. No 720p preview as the final.
- **H.264 (High profile), yuv420p, about 16–20 Mbps, AAC 48 kHz 320 kbps, `+faststart`**. No HEVC, because it doesn't play everywhere. Keep the file under 200 MB.
- Upload the final MP4 to my **Google Drive** and give me a share link that opens and downloads on my phone ("anyone with the link can view"). Also save the build files and `edit_log.json` in `editing/drafts/<video-folder>/`, then commit and push.
- Name it `coach-agz_<topic>_1080p.mp4`.

### 5. Review before you show me
Run the `QUALITY_STANDARD.md` §10 checklist on the actual rendered 1080p file:
- Frame strips at every overlay in and out.
- Caption drift.
- Sound sync.
- Clipped words.
- Overlaps.
- Face visibility (confirm the 60% and the never-over-eyes rules).
- The overlay variety rules above.

Tell me plainly what you couldn't check, such as listening to the audio.
