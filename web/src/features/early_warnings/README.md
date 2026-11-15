Early-warnings panel. Owner: Jacob (PR 7).

`<WarningsPanel bbl="3052110074" asOf="2026-06-01" onEvidence={flyToRecord} />` reads
`/api/sites/{bbl}/warnings` and `/warnings/checks` (fixtures when the API is down). Pass `onEvidence` to
make the record chips fly the map; without it they open the record on NYC Open Data.

Preview it over the map with `npm run dev`, then
<http://localhost:5173/src/features/early_warnings/preview.html?bbl=3052110074&as_of=2026-06-01>.
