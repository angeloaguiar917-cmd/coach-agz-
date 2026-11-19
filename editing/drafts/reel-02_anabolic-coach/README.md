# Reel 02: "How I know you're gay" (anabolic coach bit), 1080p

**Source:** Drive `1DncHT3F1nJz4LXnaCNhR540sEM2ihCyA` (1080×1920 HEVC, 60 fps, 25.5 s, one take).
**Output:** `coach-agz_anabolic-coach_1080p.mp4`: 1080×1920, 30 fps, H.264 High 4.2 + AAC, fast-start (plays and saves on a phone), 24.4 s, −14.0 LUFS, peak −1.4 dBFS.

## Cut
- `keep.json`: two trims only. 0.32 s of dead air before "or Tren", and 0.73 s of the pause before "Damn" (about 1 s kept, so the reaction still lands).
- The pauses inside "pictures … that you stare at … all day" are comedic timing, so they stay. The client photos play over them.

## Per user direction
- **No frame-0 text hook.** The engine was run for the log only (see `edit_log.json`).
- **Face stays recognisable.** No blur or darkening on the footage. In full-frame beats, cards sit in the top band above the cap. In image beats the footage becomes a sharp 64% window (face roughly 540 px tall) under the graphic.
- **A different overlay type on every beat** (below). Client photos come from the user's screenshots, cropped out of the gallery UI. Faces were already blurred by the user.

| Time | Line | Overlay type |
|---|---|---|
| 0:01 | "gay?" | 112% punch-in |
| 0:02 | "anabolic coach" | Credential ID plate (logo, VERIFIED tag) |
| 0:03 | "stare at half naked dudes all day" | Check-in inbox: thumbnails stream in with an unread counter, a cyan scan line on "stare", and a 24 h screen-time ring that winds up on "all day" |
| 0:05 | "dial in their bloodwork… healthy" | Three radial spectrum dials (HCT, E2, lipids). Needles swing from red to green on each word, then IN RANGE ticks. Labelled ILLUSTRATIVE. |
| 0:08 | "test, NPP, or Tren" | Line-schematic vials drop onto each word, plus a stacked "on board" bar. Tren is red. Research disclaimer included. |
| 0:10 | "lethal units" | Split screen: greyscale BEFORE, then the AFTER with a HUD target lock, a threat-level meter and a LETHAL UNIT verdict slam with a 2-frame shake |
| 0:13 | "take half naked pictures" | Camera viewfinder (REC, AF lock box framing the face), an iris shutter (no white flash), and the check-in photo as an angled polaroid |
| 0:16 | "compare… old half naked pictures" | Before/after wipe slider (client 01), then a push to client 02. The gold divider carries across. |
| 0:19 | "that you stare at all day" | DM receipt (client 03). "13-15 BF" is bracketed, a vertical body-fat range bar lands at the client's own 13–15% estimate, and the screen-time ring returns as a callback. |
| 0:23 | "Damn" | Slow push through the pause, a hard punch on "Damn", a gold caption block, then the COACH AGZ end plate |

Captions follow the saved style: Bebas, every word, a lit red block on the active word, and gold for "DAMN".

## QC
- Re-transcribed the final audio: every word matches the cut. Captions are timed from the cut's transcript; onsets for "all" and "or" were corrected to the actual speech.
- Overview every 0.5 s, frame strips through every split in/out, the shutter, the client push, the DM entry and the exit. Chunk seams were checked frame by frame.
- Fixes made during the build:
  - Pillow 12 ignores text alpha, so text now fades through a mask.
  - Drawing on an RGBA canvas skipped blending, so the canvas is now RGB.
  - Cards no longer overlap the face while the split opens or closes.
  - The empty frame between clients 01 and 02 is gone.
  - The credential card no longer overlaps the inbox card.
- **Not done:** listening. Sound effects were placed by timestamp only. Fonts are stand-ins (Bebas Neue, JetBrains Mono, Barlow, DM Sans). The dial markers are illustrative.
- Client photos aren't committed (privacy). `render.py` expects them in `imgs/` next to it.
