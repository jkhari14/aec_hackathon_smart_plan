# model_input (Rishabh)

A building's structural system, from the Revit reader or a drawing, saved for the project and its site.
Once saved, the site profile (`structural_model`), similar cases (the "construction" match) and the
pattern score use it.

- `revit.py`: reads the Revit reader's `structural_model.json` (bare or wrapped in
  `{"structural_model": ...}`) into the `StructuralModel` contract. Served by
  `POST /api/projects/{id}/model`.
- `drawing.py`: sends a PDF to Claude (`claude-opus-5-5`, structured JSON output) and classifies the
  structural system. Served by `POST /api/projects/{id}/model/drawing` with the PDF as the body
  (`Content-Type: application/pdf`). Needs `pip install anthropic` and `ANTHROPIC_API_KEY` in the
  environment; without them the route answers 503 "Couldn't read the drawing". An AI-read drawing is
  a suggestion for the engineer to confirm, so its confidence is capped at 0.7.
- `store.py`: the latest model per project and per site, in memory until Jahleel's project store
  (PR 4) persists it.

```bash
curl -X POST localhost:8000/api/projects/proj-sample/model/drawing \
  -H 'Content-Type: application/pdf' --data-binary @S-101.pdf
```
