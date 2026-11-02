# Editor test 02: depiction overlays (test only)

The feedback on test 01 was that overlays shouldn't quote the speech. They should depict it, as a visual example with context and nuance. The captions carry the words.
Same source and range as test 01 (0.00–9.40 s), 720×1280, 30 fps, −14.4 LUFS, true peak −1.4 dBFS. It doesn't approve the style or change final-video settings.

| Time | Speech | Depiction |
|---|---|---|
| 3.20 | "don't trust USA Big Pharma" | A US pharmacy Rx bottle (lot, expiry, dispensed) rises on the left shoulder. Light tock. |
| 4.40 | "but they'll order…" | The bottle is pushed out and the footage drops back. Whoosh. |
| 4.92 | "…all their" | A shipping box from Guangzhou lands hard and squashes, labelled CONTENTS "LAB SUPPLIES", VALUE $15. Heavy thud. |
| 5.60 | "peptides" | Flaps open, three unbranded 10 mg vials rise out. Glass clink. |
| 6.44 | "China's Big Pharma" | Handoff: a Certificate of Analysis slides out of the box and grows into the main frame, light and floaty, with a slight sway as it settles. Paper slide. |
| 7.75 | "without questioning" | A highlighter marks "Tested by: Supplier in-house lab". Marker swipe. |
| 8.20 | | A highlighter marks "Independent lab: —". No sound. |
| 8.66 | "thing" | A "SELF-ISSUED · NOT INDEPENDENTLY VERIFIED" rubber stamp slams onto the Approved signature. Impact and a 2-frame shake. |

All company and lab details are generic placeholders. Nothing real is named.

## Checks
- **Transcript:** the final audio matches 32/32 words, with at most 0.1 s drift.
- **Sound sync:** the tock, thud, clink and stamp were each detected within 1 frame of the visual contact.
- **Defects fixed:**
  - The bottle covered the face; it moved to the left shoulder because the subject leans right.
  - The product line overflowed the certificate.
  - The stamp covered the highlighted nuance; it moved to the signature.
  - The certificate faded in semi-transparent over the box.
- **Not done:** listening. Audio was checked by measurement only. The fonts are stand-ins.
