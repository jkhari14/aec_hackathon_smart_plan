# UI refresh: design

Date: 2026-11-14 · Branch: `rishabh/cityweft-3d` · Follows the project screen (`2026-11-14-project-screen-design.md`)

## Intent

The explorer works but reads as a dark data dashboard. The team wants it to feel like an architect's
drawing table: light paper, black ink, one blue. It should also say less and show more. Strands should
tell one story at a time, scores should read at a glance, and the map controls should sit where people
look for them.

## Goals

1. **Light "paper" look by default:** restyle the light theme to the 4site deck palette and make it the
   default. Dark stays available behind the theme toggle.
2. **Light map:** the basemap follows the theme (OpenFreeMap `positron` in light, `dark` in dark).
3. **Building colours that mean something:** the picked site in accent blue, attached neighbours (the
   party-wall buildings the checklist is about) in charcoal, everything else pale grey. The height ramp
   and its legend go away.
4. **One strand at a time:**
   - No strands drawn by default.
   - Clicking a similar-case card (or its dot on the map) flies the camera out to fit the site and that
     case, highlights both, and draws one strand between them.
   - A "Show all strands" switch draws every strand.
   - Clicking the same card again, or closing the site, clears it.
5. **Similarity as a ring:** a small circular gauge that fills to the score, with the number inside. It
   replaces the bar. Still labelled "similar", never a probability.
6. **Lighter similar-case cards:**
   - Ring plus title and date.
   - One quiet line: address · borough · severity.
   - Up to three ✓ (matches) and two ✗ (differs) as short chips, the rest folded.
   - "What happened" and the reported cause stay behind the existing disclosure.
7. **Controls:**
   - The 2D/3D switch joins the camera controls at the bottom left. Nothing stays in the bottom-right
     corner except the chat button.
   - The layers button in the top bar gets a text label ("Layers · 3"), so it no longer reads as a mystery
     icon.
8. **Layers follow the work type:** when a project with a work type is open and you return to the map,
   the layers relevant to that work type are switched on (see the table below). A manual toggle afterwards
   wins.

## Palette (light theme, from the 4site deck)

| Token | Value | Use |
| --- | --- | --- |
| `--fs-bg` | `#F1F0EC` | paper |
| grid | `#E4E2DC` lines every 24 px, on the page background only | drafting paper |
| `--fs-panel` / `--fs-raised` | `#FAFAF7` / `#FFFFFF` | panels, cards |
| `--fs-text` / `--fs-text-2` / `--fs-muted` | `#141414` / `#3A3A3A` / `#6E6C66` | ink |
| `--fs-line` / `--fs-line-strong` | `#DAD8D1` / `#BDBAB2` | rules |
| `--fs-accent` / `--fs-accent-soft` / `--fs-accent-ink` | `#4A6CF0` / `rgba(74,108,240,.12)` / `#FFFFFF` | the one blue |

- **Fonts (Google Fonts):** "Space Grotesk" for UI and headings, and "Silkscreen" (pixel) only for
  small uppercase eyebrows (`.fs-label`, `.fs-ps__eyebrow`), echoing the deck.
- **Hazard and severity colours** keep their hues, re-checked for contrast on paper.

## Layers by work type

| Work type | Layers switched on |
| --- | --- |
| New construction | construction incidents, structural complaints, watchlist, FEMA flood zones, E-designations |
| Modification to existing structure | structural complaints, unsafe facades, vacate orders, watchlist |
| Demolition | construction incidents, structural complaints, unsafe facades, watchlist |
| No project | catalog defaults, as today |

## Approaches considered

1. **Restyle the existing light theme and make it the default (chosen).** One token set changes and
   every panel follows. Dark remains.
2. A third "paper" theme. More to maintain, and a confusing toggle.

## Non-goals

- No change to similarity scoring or the chat (others own them).
- No real "buildings by similarity" colouring: similar cases are across the city and outside the 3D
  model's ~500 m area.

## Constraints

- AGENTS.md rules hold: sources and dates stay visible; the score is "similar", never a prediction; no
  owner names.
- Touch the similar-case card's look only (Camilo's file, and a teammate is changing scoring), to keep
  merges small.
- Reduced motion: the fly-out jumps instead of animating.
- No new npm dependencies.

## Left to the builder

- Exact fly-out padding and duration; strand styling within the palette.
- Ring size (about 36 px) and stroke.
- Where the "Show all strands" switch lives: the similar tab header, plus the map legend area.
