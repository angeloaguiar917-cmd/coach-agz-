# Full test 02: "GH carpal tunnel" (1080p30, phone-ready)

**Source:** Drive `1fFI471CcCtDn2JFKejmy-DKjaOhHu8RH` ("HGH carpal 2"), 1080×1920 HEVC 60 fps, 1:28, one seated take.
**Output:** `coach-agz_hgh-carpal-tunnel_1080p30.mp4`. It's 1080×1920 at 30 fps, H.264 High with yuv420p and AAC 48 kHz, plus a `faststart` flag so it plays and saves on a phone. Length is 1:24.1, loudness −14.8 LUFS, true peak −1.5 dBFS.
**Style:** the test-06 overlay palette and clinical evidence look, with captions as in full test 01. The footage itself isn't graded, saturated or contrast-boosted.

## Cut
- Dead air: every silence of 0.25 s or more (detected at −38 dB) is trimmed to about 0.13 s. That's 16 frame-aligned jump cuts, 3.9 s removed in total.
- The audio is rebuilt sample-exact from the source, with 8 ms fades at each cut.
- No retakes or stumbles needed cutting. The take is clean.

## Overlay types (feedback: "don't use the same overlay type over and over")
Each beat uses a different type of overlay and layout:

| Time | Beat | Overlay type | Layout |
|---|---|---|---|
| 0:00 | Hook | Premium text hook: GH CARPAL TUNNEL / starts in your kidneys | Text over footage |
| 0:05 | "not your wrist joints / cartilage" | Two X-ray exhibit cards with scan sweeps, a red ✕ stamp and a RULED OUT tag | Top shelf over footage |
| 0:09 | GH → kidneys → sodium → water | Fluid-chain node row, kidney schematic, EXIT HELD gate, Na⁺ particles with water drops following, a body-fluid tank rising | Full-screen schematic; the footage irises into a face bubble |
| 0:17 | "most places can stretch… carpal tunnel cannot" | ROOM TO EXPAND horizontal bar chart; the carpal tunnel bar hits a hard wall (NO STRETCH) | Top shelf over footage |
| 0:23 | Rigid tunnel, bone, ligament, median nerve | Cross-section scope (bones, ligament, tendons, nerve squashing), a pressure-vs-fluid curve with "small + → big ↑", then a median-nerve hand map that pulses on "tingling" | Side split (graphics column on the left, footage on the right) |
| 0:37 | Renin-angiotensin-aldosterone | System flow GH → RENIN → ANGIOTENSIN → ALDOSTERONE, then a fluid-balance gauge swinging to HOLD and RETAIN ✓ / EXCRETE ✕ | Top shelf over footage |
| 0:47 | More sodium → water → pressure | Rising column chart breaking through a dashed TUNNEL'S LIMIT line (OVER LIMIT) | Full-screen chart with a face bubble (top-left) |
| 0:53 | "How do we fix it?" | Chapter card: a gold rule sweeps across, then THE FIX | Top band |
| 0:54 | Numb at night / during the day | 24-hour symptom dial plus a symptom log | Top shelf |
| 1:02 | Not permanent damage, responds to dose and sodium | Verdict bars (PERMANENT DAMAGE struck through, PRESSURE ✓) and DOSE / SODIUM toggle switches | Top shelf |
| 1:07 | Drop, stabilize, increase slowly | GH dose vs fluid line graph with a symptom threshold | Footage in a rounded window, graph below |
| 1:13 | Framework CTA | Framework document (Protocol, Dose adjustment, Sodium management), then a COMMENT "PANEL" gold bar with the logo | Top shelf |

## Face stays recognisable
- Your head was tracked (from the "A" logo on your cap) so the bubble layouts keep your face centred.
- No graphic covers your face. Cards sit above the cap, captions sit under the chin (y ≈ 1470), and the split, bubble and window layouts scale the footage down rather than covering it.

## Sound
Clinical SFX only: sub thuds on landings, ticks on chain nodes and rows, scan sweeps, and impacts on RULED OUT, NO STRETCH, OVER LIMIT, THE FIX and COMMENT. Speech is loudness-normalised.

## QC done
- The cut was re-transcribed: every word is present.
  - Caught and fixed during the build: an audio-fade offset that muted the end of each segment, and per-segment drift from the audio stream. The audio is now built sample-exact.
- Stills were checked at every scene. Layout fixes during the build:
  - Side-split column widened.
  - Missing arrow glyphs.
  - Dose-graph tag collision.
  - CTA document overlap.
  - Hand map redrawn.
  - X-ray art enlarged.
- Transition strips re-checked after moving graphics off the face during layout moves (they now clear in the first half of each move).
- Not listened to; levels only. The fonts are stand-ins (Bebas Neue, DM Sans, Barlow Condensed, JetBrains Mono). The charts are illustrative and labelled ILLUSTRATIVE where shapes imply values.
