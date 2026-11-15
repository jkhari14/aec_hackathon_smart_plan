# 4site pitch video: speaker notes

The video ([`4site_pitch.mp4`](4site_pitch.mp4), 4:59, silent, no captions) plays while we talk. Each line
below fits its beat at a calm pace (about 2.5 words a second) with room to breathe. Start each line when its
timecode comes up; if you fall behind, drop the last sentence rather than rushing.

Speakers are a suggestion, following [deck_outline.md](deck_outline.md): one voice for the story, one for the
demo, the structural engineer for "how it works". Swap freely.

**Words to use:** similar cases, patterns compared with similar sites, signals, a prompt to look.
**Never say:** predicts, will fail, safe, would have prevented. Do not name the Nov 11 collapse.

---

## 0:00 Intro (8 s)
*Logo builds, then the title.*
> We're 4site. Build on hindsight, design with foresight.

## 0:08 Team (15 s)
*Eight cards, then the discipline legend.*
> We're eight people across five disciplines: architects, a structural engineer, computational designers, a
> developer, and software and AI engineers. That mix is the point: this problem sits between our disciplines.

## 0:23 Problem (25 s)
**0:23 The wrong building.**
> On an NYC job, the warnings are usually public. But they're filed on the job's record, not on the old
> building next door, and no one links the two.

**0:32 One slice each.**
> Everyone holds one slice: the architect, the engineer, the contractor, DOB. No one sees the whole site.

**0:39 The scale.**
> And it repeats: more than sixteen thousand structural complaints since 2024, nearly fifteen hundred
> incidents, and 1,187 active excavations next to old attached buildings right now.

## 0:48 Who it's for (9 s)
> It's for architects and structural engineers first, and developers and contractors too, from before
> acquisition through construction.

## 0:57 Solution (10 s)
*Dark slide; the four steps light up.*
> 4site is one risk-intelligence map for every site in New York. Pick a site, see its public record,
> compare similar cases, and act on early warnings.

## 1:07 Product demo (98 s)
*Full-screen recording of the real app, sped up and zoomed. The chips match the four steps.*

**1:07** *(title card)*
> Here's the live product, on an active site in Brooklyn.

**1:10 Pick a site.**
> This is the whole city in 3D, with risk layers like unsafe façades and Sandy flooding.

**1:15**
> We search for 861 Park Avenue: a new building with excavation, next to attached neighbors from the 1910s.

**1:22 See the public record.**
> Right away: what stands out, life-safety first, each with its source and date, and why you're seeing it.
> It covers this lot and every lot it touches.

**1:35 Compare similar cases.**
> Similar cases are past NYC sites with the same profile. This one, 211 East 34th Street, partly collapsed
> next to an excavation in 2020, with no injuries. You see what matched, and what happened, as publicly
> reported.

**1:52 Act on it.**
> Then actions by role, each tied to the building code.

**1:58 Shared checklist, by role.**
> Start a project: new construction, masonry, the scope pre-ticked. 4site drafts one shared checklist,
> life-safety first. Open an item and you see who owns it, the code section, and the proof it needs.

**2:11 Early warnings.**
> Back on the map, early warnings: work continued after a stop-work order, and heavy rain and freeze-thaw
> during an open excavation.

**2:21 Ask in plain English.**
> And you can just ask.

**2:27** *(the answer scrolls)*
> The engineer asks what to check before excavation continues. Claude answers from this site's records
> only: the open support-of-excavation job, the attached neighbors, the code sections to follow. Then
> it's pinned to the project, so the whole team sees it.

## 2:45 Inputs, process, outputs (15 s)
*Animated diagram with records flowing through.*
> An address, the project and public records go in. We build a site profile, then run similarity,
> early-warning rules and a grounded Claude. Out come similar cases, warnings, a checklist and answers.

## 3:00 How it works (42 s)
**3:00 Similarity.**
> Similarity is a weighted sum of facts an engineer can check. Against 211 East 34th: masonry wall,
> attached, excavation, the same hazards. That's 56. A fact nobody reported never counts as a difference.

**3:13 Early warnings.**
> Early warnings are sequences in time: a stop-work order, then more work; rain during an open
> excavation. Two of the four rules fire here. They're prompts to look, not findings.

**3:24 The checklist.**
> The checklist turns all of it into work: 12 building-code duties and 9 hazard rules, split by role.
> Each item has an owner, a status, its code section, and the proof the team must supply.

**3:34 The chat.**
> The chat is grounded: every claim cites a record, and there are no verdicts, blame or predictions.

## 3:42 Data sources (10 s)
> It's all public and all dated: DOB filings, complaints and violations, façades, flood, soil, weather, a
> 42-case library, and the building code.

## 3:52 Tech stack (9.5 s)
> React, MapLibre and deck.gl on top, Claude for the chat, Python and FastAPI underneath, and Cityweft for
> the 3D city.

## 4:02 Impact (10.5 s)
> The neighbor's risk shows up on your site, hindsight becomes a checklist, and the whole team works from
> one picture. Right now, 1,187 sites fit this profile.

## 4:12 Limits and next steps (12 s)
> We're clear about the limits: public records only, not engineering advice, never a prediction. Next: a
> DOB objection check before filing, a forensics ledger, daily alerts, and more cities.

## 4:24 How we built it (25 s)
**4:24 The process.**
> We recorded our brainstorms with Wispr Flow, synthesized them with Cursor and Claude, iterated on the
> plan, made concept videos, and took feedback, including from a Thornton Tomasetti forensic expert.

**4:39 The build.**
> BUILD.md became our single source of truth. Each of us ran an agent session from it, and 41 pull requests
> merged in about five hours.

## 4:49 Close (10 s)
*Logo builds again, then the tagline.*
> The warnings were always public. 4site turns them into risk intelligence, before work starts.

---

### Facts behind the lines
- Counts are from NYC Open Data, pulled Nov 14, 2026: 16,581 structural complaints and 1,495 construction
  incidents since 2024. The 1,187 is the watchlist of active earth-work, foundation and SOE permits next to
  attached pre-1940 buildings.
- 211 E 34th St (2020): partial collapse of a vacant building next to an excavation; no injuries reported.
  The similarity of 56 is 18 (wall system) + 10 (attached) + 20 (earth work) + 8 (record hazards).
- The two warnings on 861 Park Ave are from ECB violation 39550399K (2026-02-16) and job B00898115
  (support of excavation, permitted 2024-11-26).
- The demo project's checklist: 21 items (12 from the BC 3304/3309 checklist, 9 from hazard rules); 12 for
  the structural engineer, 6 for the architect, 3 for the contractor; 18 marked life safety.
- The DOB objection check is not built yet; it is shown only as a next step.
- The PRs: 44 opened and 41 merged between 23:58 UTC Nov 14 and 05:16 UTC Nov 15, across four waves.
- Team backgrounds were checked on LinkedIn and company pages on Nov 14, 2026.
