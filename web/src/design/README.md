Design tokens and primitives. Owner: Camilo (PR 1).

Import everything from this folder, never from its files: `import { Panel, Card, SourceLabel } from "../../design";`

- `tokens.css`: color (dark first, light under `[data-theme="light"]`), hazard and severity colors, type,
  8-point spacing, radii, motion. Text colors meet WCAG AA on panels in both themes; `--fs-faint` is for
  decoration only. The PR 0 Tailwind names (`bg-panel`, `text-muted`...) point at these tokens.
- `components.tsx`: `Panel`, `Card`, `Chip`, `HazardChip`, `SourceLabel`, `Badge`, `SampleBadge`,
  `SeverityMark`, `SeverityBadge`, `Count`, `Skeleton`, `SkeletonCard`, `EmptyState`, `ErrorState`,
  `Button`, `Toggle`, `Tabs`, `Kbd`, `formatDate`.
- `hazards.ts`: hazard labels, RGB arrays for deck.gl (`HAZARD_RGB.dark`), severity marks for the map,
  and `bySignalPriority` (life safety first).
- `icons.tsx`: the inline icon set.

Rules the components already follow, so screens get them for free:
- Color is never the only cue: severity is size plus rings, source kinds differ by border style, pressed
  chips show a check.
- A failed query is `<Count status="error">` ("Couldn't load"), an unknown count is "count unknown", a
  capped one is "at least N". None of them render as 0.
- Every fact can carry a `<SourceLabel kind="record|ai|user" name url date>`; a missing date reads
  "date unknown".
- Motion uses `--fs-fast/base/slow` (150 to 300 ms), which drop to 0 under reduced motion.
