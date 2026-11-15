# Live demo runbook (1:45)

**Driver:** Shandon (map). **Narrator:** Jacob. Seeds: [demo_seeds.json](demo_seeds.json). Sites and their sources: [data/demo_sites.json](../data/demo_sites.json).

## Before you go on stage
1. Open the deployed app in a fresh browser window at 1920×1080 with the dark theme on. Close every other tab.
2. Check the hero site loads end to end once (map, panels, chat), then reload so the audience sees the fly-to fresh.
3. Have the offline fallback ready in a second tab: the same app with the API down shows "Sample data" from the fixtures.
4. Re-run the hero site's source links from `data/demo_sites.json` and note today's counts. Say only the numbers the app shows.

## Steps
| # | Time | Do | Say |
|---|---|---|---|
| 1 | 0:00 | The citywide map is on screen. | "This is ForeSite's home: the whole city, every source as a layer." |
| 2 | 0:10 | Open the layer panel and turn one layer on. | "Each layer shows its source, its date and its count." |
| 3 | 0:20 | Search the hero address and press Enter. | "We'll pick a real site with active work next door to older rowhouses." |
| 4 | 0:35 | Let the fly-to finish, then point at the outlined neighbors and the glowing shared wall. | "These are the lots that touch the site. This is the wall they share." |
| 5 | 0:50 | Open the site panel's top signals. | "Here's what neighbors and inspectors already put on the record, with dates." |
| 6 | 1:05 | Zoom out to show the similar-case arcs; hover one. | "Similar cases across the city: what matched, what differed, cause only as reported." |
| 7 | 1:20 | Open actions by discipline; assign one to the structural engineer. | "Each action has an owner and the proof it needs." |
| 8 | 1:35 | Ask the first chat question from the seeds; click a source chip. | "And you can just ask. Every answer points to its record." |

## If something breaks
- **The map or API fails:** switch to the fallback tab and say "this is the same app on saved sample data", then continue from step 4.
- **The chat is slow:** skip step 8 and point at the always-visible limitations panel instead.
- **A record shows a person's or company's name:** don't read it out; move on.
