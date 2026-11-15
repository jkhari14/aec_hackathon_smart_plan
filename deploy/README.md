# Deploy and freeze (PR 19)

The web app is static and goes to GitHub Pages. The API is one container that runs on any host. If the API
is down, the web app reads the demo snapshot, then the fixtures, and always labels what it shows: "Sample
data" for fixtures and stubs, and the saved date for snapshot answers.

## The demo snapshot

```bash
.venv/bin/python -m tools.demo_snapshot --as-of 2026-06-01          # from data/cache/, offline
.venv/bin/python -m tools.demo_snapshot --pull --as-of 2026-06-01   # refresh data/cache/ first (live)
```

This saves every GET answer the app needs for the demo sites into `web/public/snapshot/`, which is
gitignored and rebuilt by every deploy. The sites come from `data/demo_sites.json` (Ethnie) plus every pull
in `data/cache/`. It asks the API in process, so it saves whatever routers have merged; it prints how many
answers are still sample data, and that number should be 0 at the freeze.

## The API

```bash
docker build -f deploy/api.Dockerfile -t foresite-api .
docker run -p 8000:8000 -e FORESITE_WEB_ORIGINS=https://<owner>.github.io foresite-api
```

On the host, set `FORESITE_WEB_ORIGINS` to the web app's origin. `ANTHROPIC_API_KEY` and `SODA_APP_TOKEN`
are optional, and both stay in the host's environment.

## The web app

1. Once: enable Pages for the repo (Settings > Pages > Source: GitHub Actions), and set the repository
   variable `FORESITE_API_BASE` to the API's URL. Without it, the site is static: snapshot and fixtures only.
2. Actions > Deploy web > Run workflow.

## Freeze, Sun 11:00

1. All PRs merged and the end-to-end check passed on `main`.
2. Refresh the caches: run `python -m data_pull.site_brief_pull --demo` and
   `python -m early_warning.watchlist`, then commit `data/cache/`, `data/layers/` and
   `early_warning/weather_cache/` in one PR.
3. Run `tools.demo_snapshot` locally and check that nothing is still sample data.
4. Redeploy the API and run the Deploy web workflow. Rehearse on the deployed URL with the API stopped once,
   so the snapshot fallback is known to work.
5. Tag the frozen commit: `git tag demo-freeze && git push origin demo-freeze`. After that, only fixes.
