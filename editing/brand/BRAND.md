# @coach.agz — Brand Style Guide (for Reels, overlays and carousels)

## Identity
- **Name:** Coach AGZ (written **COACH AGZ** in headers and logo lockups)
- **Instagram handle:** **@coach.agz** (lowercase, with the dot). Use exactly this on every watermark, header and end card.
- **Logo:** `logo/coach-agz-logo-round.jpg`. A layered "A" triangle in cracked, textured antique gold over black paper texture, with faint ember-red flecks and "COACH AGZ®" below.
  - Logo palette (sampled): highlight `#C0B090`, mid gold `#A09070`, shadow bronze `#706040`, background `#050505`.
  - It's a raster image with a baked-in background. Ask for a transparent PNG or SVG before animating the mark on its own.

Source: carousel and overlay examples in `reference/`. Hex values were sampled from those files. Font names are best visual matches and haven't been confirmed. Replace them with the real font files if they differ.

## Voice on screen
Blunt, clinical, coach-to-athlete. Short declarative lines with full stops ("SAME BODY. TWO STANDARDS."). One idea per frame, then one supporting sentence. The content is health and data-driven ("bloodwork is the roadmap"). Show numbers, ranges and trends. Avoid hype graphics.

Fixed disclaimer: **FOR RESEARCH & EDUCATIONAL PURPOSES ONLY** (small, tracked caps, muted).

## Two looks

### A. Carousel / "Audit" look (navy + gold)
Use it for full-screen graphic scenes, title cards, schedules and stats.

| Token | Hex | Use |
|---|---|---|
| `bg` | `#0E1117` | Base background (near-black navy) |
| `bg-glow` | `#1D1D1E` | Soft warm glow in the top-right corner (radial, very subtle) |
| `panel` | `#181A22` / `#191C23` | Cards, tables, comparison columns |
| `panel-border` | ~`#3A3630` (1px, low contrast warm) | Box outlines |
| `gold` | `#C9A96E` | Brand accent, kicker labels, key numbers, "positive emphasis" word |
| `cream` | `#F4F1EA` | Headlines, primary text |
| `muted` | ~`#B8B8BC` body / ~`#7C7C82` labels | Body copy, captions, footer |
| `red` | `#E7472A` | Warning / "never" / the problem word |
| `green` | `#5BB77A` | Good / "checked" / daily-OK status |

Layout anatomy (1080×1350 carousel; reuse proportions for 1080×1920 Reels):
- **Gold vertical rule** about 4px wide on the left edge. This is the signature brand element.
- **Header:** "A" logo badge, then **COACH AGZ** in gold condensed caps, with `@coach.agz` in mono below. Page counter `01 / 10` in mono at the top right.
- **Kicker:** a short gold line `——` followed by wide-tracked gold caps (e.g. "THE MIRROR TEST").
- **Headline:** heavy condensed caps in cream. One or two words are recoloured gold (positive or key) or red (danger).
- **Sub-line:** sentence-case sans in muted grey, with the key phrase in **bold cream**.
- **Tag pill:** a solid gold block with dark mono caps (`NON-NEGOTIABLE 01`).
- **Bullets:** small gold diamonds ◆ with a **bold lead-in**, an em-dash and a muted explanation.
- **Big stat:** an oversized gold or red number (500+, 73%), with a tracked caps label or a red vertical rule beside it.
- **Chips:** dark red fill, thin red border, light red condensed caps.
- **Footer:** the disclaimer on the left, and `SWIPE →` in gold or a progress-dash row on the right.

### B. Reel overlay look (charcoal + crimson)
Use it for floating explainer cards over talking-head footage.

| Token | Hex | Use |
|---|---|---|
| `card` | `#0C0C0E` at ~92% opacity | Card fill; footage shows faintly through it |
| `card-inner` | `#1D1D21` | Inner boxes |
| `crimson-bar` | `#C8102E` | Left edge bar on every card, and pill fills |
| `crimson` | `#E0243F` | Kicker text, accent words, numbers, arrows |
| `chip-fill` | `#280C12` | Chip background with a crimson border |
| `cream` | `#F4F1EC` | Headlines |
| `muted` | `#CFCAC4` | Sub-lines |
| Spectrum | blue `#4FA3E0`, green `#3CCB6A`, amber `#F0A030` | Low / dialed-in / high scales only |

Card anatomy: large rounded corners (about 24px at 960 wide), a crimson bar on the left, a centred or left-aligned crimson tracked kicker, cream condensed headline, muted sub-line and an `@COACH.AGZ` watermark at bottom right. Diagrams use white 3px outlines, rounded boxes, crimson numbered dots and arrows.

## Fonts on file
No font files have been supplied yet. Put the real files in `fonts/`. Until then, draft mockups use free stand-ins (Bebas Neue, DM Sans, JetBrains Mono, Barlow Condensed) and label them as stand-ins.

## Type
| Role | Style | Likely font |
|---|---|---|
| Headlines, numbers | Heavy condensed caps, tight leading (~0.95) | Bebas Neue |
| Overlay text, labels, table rows | Semi-bold condensed | Barlow Condensed |
| Body / sub-lines | Clean geometric sans, sentence case | DM Sans |
| Counters, handles, tags, status words | Monospace caps, tracked | JetBrains Mono / IBM Plex Mono |
| Kickers | Condensed caps, letter-spacing ~0.25em | Barlow Condensed / Bebas |

## Colour rules
- Gold means brand and "the thing to do". Red means danger, "never" and the problem. Green means only "OK / checked".
- Use at most one accent colour per line, and usually two accent words per frame.
- Keep backgrounds flat and dark with a subtle glow. Don't use generic gradients. The only multi-colour gradient allowed is a data spectrum.

## Translating to motion (applies with QUALITY_STANDARD.md)
- **Gold left rule** works as a persistent anchor; it can grow to become a divider or the edge of a new panel (handoff).
- **Kicker line** `——` draws on first, then the label types or tracks in. The headline lands after it.
- **Accent words** recolour on the spoken word. Don't pre-colour them.
- **Big stats** count up and land with weight. The label follows with a short delay (overlap).
- **Comparison columns:** the top border draws on, then rows tick in time with speech (✓ softly, ✕ firmer).
- **Tag pills** are heavy blocks that slide in and settle. Mono text appears after them.
- **Overlay cards** are light glass that rises with slight blur and settles. The crimson bar leads by a few frames.
- **Spectrum marker** slides along the bar and settles on the spoken state; the matching box outline lights up.
- **Disclaimer and handle** stay static; they never animate.
