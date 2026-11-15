App shell. Owner: Camilo (PR 1, 10).

- `App.tsx`: full-bleed map with floating columns. Left: top bar and layers. Right: site panel with the
  chat dock under it. Bottom left: "What ForeSite doesn't know" and the data status line.
- `slots.tsx`: the panel frames other PRs fill. `LayerSlot` (Shandon, PR 5), `SiteSlot` (Camilo, PR 10),
  `ChatSlot` (Jahleel, PR 9). Replace the body, keep the `Panel` frame and its props.
- `CommandBar.tsx`: `/` or Cmd/Ctrl-K. Address search through `api.search`, plus app commands.
- `shortcuts.ts`: `/` and Cmd/Ctrl-K search, `L` layers, `C` chat, `T` theme, `?` help, `Esc` closes the
  top panel. Single keys never fire while typing in a field.
- `url_state.ts`: shareable URLs. `?site=<bbl>&layers=1&chat=1`. Picking a site pushes history; panel
  toggles replace it.
- `preferences.ts`: dark or light theme (saved per browser when storage allows) and reduced motion.
