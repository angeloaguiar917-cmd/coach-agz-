# Editor test 03: clinical evidence look (test only)

Feedback on test 02: the direction was right, but avoid cartoonish overlays and keep it aggressive and clinical.
Same source and range (0.00–9.40 s), 720×1280, 30 fps, −14.3 LUFS, true peak −1.4 dBFS. It doesn't approve the style or change final-video settings.

## Visual language
- **Evidence panel:** a frosted dark panel with corner brackets, a mono header (blinking red rec dot, stage name, "EVIDENCE 0X") and a thin cream border.
- **Documents:** desaturated paper scans with grain.
- **Flags:** red detection brackets around the exact value, with a solid red mono tag beside it.
- **Motion:** expo snaps and focus pulls. No bounce, squash or overshoot.
- **Sound:** clinical. Sub hit, scan sweeps, digital ticks, one impact.

## Timeline

| Time | Speech | On screen |
|---|---|---|
| 3.20 | "USA Big Pharma" | Reference tag on the shoulder, "REF · US PHARMACY", with ticked rows: lot-tracked, pharmacist-dispensed, regulated mfg, recall system. Tick sound. |
| 4.36 | "but they'll order" | The tag snaps out and the footage pushes back. Whoosh. |
| 4.80 | | The evidence panel lands (focus pull) as "PARCEL SCAN" of a shipping label. Sub hit. |
| 5.30 | | "DECLARED LAB SUPPLIES" is flagged MISDECLARED. Tick. |
| 5.62 | "peptides" | Scan wipe to X-RAY: three vials, "3 × VIAL · NO PHARMACY LABEL", then "CONTENTS UNVERIFIED". Scan sweep. |
| 6.44 | "China's Big Pharma" | Scan wipe to DOCUMENT REVIEW: the Certificate of Analysis. The panel frame persists; this is the handoff. Scan sweep. |
| 7.75 | | "Tested by: In-house" is flagged SAME SELLER. Tick. |
| 8.20 | | "Independent lab: —" is flagged NONE. Tick. |
| 8.66 | "thing" | A red verdict bar slams across the signature: "SELF-ISSUED · NOT INDEPENDENTLY VERIFIED". Impact and a 2-frame shake. |

## Checks
- **Transcript:** 32/32 words, at most 0.08 s drift.
- **Sound sync:** the panel hit, flag tick and verdict impact were each detected within 1 frame of the visual.
- **Defects fixed:**
  - Flag tags overlapped neighbouring rows; they now sit beside a box tightened to its value.
  - Small X-ray callouts were enlarged.
  - The verdict bar spilled past the panel.
  - Text overflowed the reference tag.
- **Not done:** listening. The fonts are stand-ins. All document details are generic placeholders.
