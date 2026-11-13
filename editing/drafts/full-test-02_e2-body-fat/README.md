# Full test 02: "E2 / body fat" (1080p30)

**Source:** Drive `1s2PFARuUlnzD_WB8dAjdnFOWhRfHOWNv` ("E2 fat short"): 1080×1920 HEVC, 60 fps, 31.5 s, one take in the car.
**Output:** `coach-agz_e2-body-fat_full-test-02_1080p30.mp4`: 1080×1920, 30 fps, H.264 High, AAC 192k, faststart (plays and saves on a phone), 30.2 s, −14.4 LUFS, true peak −1.4 dBFS.
**Status:** test of the saved style with more variety. Not an approved Signature Style.

## Direction for this one
Coach AGZ asked for different overlay types (no repeated panel), graphs, more graphics, vibrant colours on brand, and the face kept recognisable.
- No overlay sits on the face. Graphics stay in the free zones: the dark ceiling above the cap, beside the head, or below the chin. When a graphic needs more room, the footage moves into a split screen instead of being covered or blurred.
- The footage itself isn't graded.

## Cut
- One take with no misspeaks.
- Nine pauses of 0.22 s or more were trimmed to about 0.12 s (`trim.json`), which removed 1.17 s.
- Every jump cut alternates the punch-in between 100% and 107%.
- The split-screen exits hard-cut on the jump cuts.

## Text hook (engine run, see `edit_log.json`)
- **Winner:** "High **ESTROGEN** on TRT / it's not your dose". It's visible from frame 0 and holds to 3.87 s.
- **Visual hook:** a 106% punch-in on "body" at 1.14 s.
- **Topic band:** "Body fat raises **ESTROGEN**" shows from the end of the hook to the first jump cut after the midpoint.

## Overlay types (8, none repeated)
| Time | Type | What it shows |
|---|---|---|
| 0:00 | Text hook | Frame-0 title in the upper third |
| 0:03 | ID card and counter | A count goes 0 → 1 on "one". The AROMATASE molecule resolves (gene CYP19A1). |
| 0:06 | Split screen and mechanism diagram | Footage shrinks into a gold-framed window. The molecule flies onto a fat cell's membrane (handoff). T particles enter the cell and leave as E2. |
| 0:10 | Line graph | The fat cell shrinks into the x-axis (handoff). Fat cells grow along BODY FAT and the E2 conversion curve draws on "increases". Tagged "concept, not to scale". |
| 0:12 | Flanking meters | Two gauges sit either side of the face. TRT DOSE locks (SAME) while E2 OUTPUT rises. The link between them snaps on "independent". |
| 0:15 | AR detection callouts | Red brackets track the face (OpenCV), plus the chest, with leader lines to FLUID, TISSUE and MOOD tags. A live mood waveform turns unstable on "volatility". |
| 0:20 | Reverse split and lab report | Footage moves up and a desaturated lab scan slides in. The estradiol marker slides past its range to H, then CONFIRMED appears. Steps follow: 01 LABS ✓ → 02 PROTOCOL 🔒. |
| 0:23 | CTA sequence | A checklist card with redacted rows ticks in and a FREE stamp hits. Then the gold COMMENT "E2" pill appears, an arrow points to the comment button, and a DM-style toast says "sent you E2_checklist.pdf". |

Captions are every word in Bebas with the red active-word block (the saved style). They sit just under the chin, at y ≈ 1460–1580.

## Sound
- Clinical SFX on each landing, at most one heavy hit per beat: sub thuds, scan sweeps, digital ticks, a link snap, and impacts on CONFIRMED and the CTA.
- 8 ms crossfades at every trim.

## QC done
- **Stills:** checked at every beat.
- **Frame strips:**
  - the hook exit
  - the card → split → cell handoff
  - the graph → meters hard cut
  - the lab → CTA hard cut
  - the end card
- **Fixes made during the build:**
  - PIL drew translucent shapes onto the RGBA frame without blending, so fills came out solid. The frame is now RGB with masked pastes.
  - The split window is cropped to start at the cap.
  - The tags no longer collide.
- **Captions:** the final audio was re-transcribed and diffed against the captions. One word ("and" before "I'll") was missing and is now added. 94/94 words match.
- **Not done:**
  - Listening. The SFX levels and the feel of the mix need checking by ear.
  - The lab rows show no numbers on purpose, because none are said in the video.
  - The fonts are stand-ins (Bebas Neue, Barlow Condensed, DM Sans, JetBrains Mono).
- **Caption placement:** the captions sit partly inside the bottom 420 px UI zone. The face fills the frame down to about y 1480, so the only alternative was covering the mouth. Check this on the phone.

## Rebuild
```
python3 render_e2.py <scratch> <i> 4   # i = 0..3 (needs <scratch>/src/e2.mov and <scratch>/fonts/)
python3 audio_e2.py a48.wav mix.wav
# concat chunks + mix: volume 4.9 dB, alimiter 0.83, libx264 High crf 18, +faststart
```
