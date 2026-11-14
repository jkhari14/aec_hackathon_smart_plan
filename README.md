# ForeSite (aec_hackathon_smart_plan)

A citywide 3D map of NYC for architects and structural engineers: the public data that matters for a
site, similar-profile cases across the city, and early-warning patterns before work starts.

**Building it:** start with [BUILD.md](BUILD.md). Tell your agent "I'm <your name>" with the kickoff
prompt there; [AGENTS.md](AGENTS.md) tells it how to find your section.

## Planning
- [ForeSite build plan](planning/foresite_build_plan.md): the build goal after the third meeting: a citywide 3D map for architects and structural engineers, with a predictive foresight layer (post-event forensics is a next step)
- Brainstorm transcripts: [part 1](planning/transcripts/team_brainstorm_2026-11-14.md), [part 2](planning/transcripts/team_brainstorm_2026-11-14_part_2.md), [part 3](planning/transcripts/team_brainstorm_2026-11-14_part_3.md)

## Reference docs and modules
- [Data and code notes](docs/data_and_code_notes.md): verified data sources, the Building Code checklist, the 1321 Flatbush demo facts
- [Data sources](docs/api_data_sources.md): more datasets, ownership sources, the Revit/Rhino/Grasshopper path
- [Manual data imports](docs/manual_data_imports.md): the sources a crawler can't use, our verdict on each, and the manual-import path ([manual_imports/](manual_imports/README.md), with DOB's complaint code key as the first import)
- [data_pull](data_pull/README.md): address in, the public record for the site and every touching lot out (cached demo data in `data/cache/`)
- [checklist](checklist/README.md): the Building Code duties toward adjoining property for a site, which apply, and the proof each needs (demo output in `data/checklists/`)
- [jahleel/](jahleel/README.md): one teammate's earlier API and web app (PreFlight), kept as a read-only reference for the ForeSite build
