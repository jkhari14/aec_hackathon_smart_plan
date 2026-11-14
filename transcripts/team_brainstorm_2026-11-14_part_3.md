# Team brainstorm transcript, part 3

Third session from the 2026 NYC AEC hackathon, recorded 2026-11-14. Part 1 is [team_brainstorm_2026-11-14.md](team_brainstorm_2026-11-14.md), part 2 is [team_brainstorm_2026-11-14_part_2.md](team_brainstorm_2026-11-14_part_2.md).

## About this transcript

- It is an automatic transcription, kept word for word as provided. Transcription errors are not corrected.
- Speaker labels do not map to one person each, and names are as transcribed and may be misspelled.
- The name of the outside expert interviewed near the end, and the name of his firm, are withheld.

## Transcript

**Speaker 1:** Hey, power factory—

**Speaker 2:** I wonder if I can do a whisper phone so you could just pass the phone around.

**Speaker 1:** Oh, that's a good idea—

**Speaker 2:** I'm saying I'm not—

**Speaker 1:** We do that on the phone.

**Speaker 2:** I mean, I have my phone.

**Speaker 1:** I think we just talked. This has been wonderful.

**Speaker 2:** Yeah, this has been—

**Speaker 1:** All right, go for it.

**Speaker 2:** Let's do it.

**Speaker 3:** We start with the details. Platform fetches zoning, lot area, FAR, yearbuild, landmark flags, and flood zone automatically.

**Speaker 3:** Next, we set the stage: late design before filing, the job type, an alteration, and the work types—excavation, foundation, SOE, and structural. Drawings can be added too.

**Speaker 3:** It pulls DOB complaints, 311 reports, inspection dispositions, and FEMA and USCIS flood data, then keeps only life safety signals like shaking, falling debris, or a building leaning. On the 2.5D map, the site sits next to a pre-war photograph of rubble from a cleared carriage.

**Speaker 3:** Similar cases from across the city appear alongside.

**Speaker 2:** I will not use it, but okay.

**Speaker 3:** In the chat, you can ask—

**Speaker 2:** I mean, I'll need to do that.

**Speaker 3:** —in English, and every answer points to the records behind it. The result is one dashboard, split by discipline, with actions for structural, geotechnical, the architect, and the contractor. Code, data, and AI flag the risks; engineers review them.

**Speaker 1:** Sounds like a gnome pitch.

**Speaker 3:** Everyone on the project, including DOB, works from the same dashboard before work starts.

**Speaker 1:** Dude, that's crazy.

**Speaker 2:** Going from the beginning to the end, it never has the same picture in vision.

**Speaker 1:** Yeah.

**Speaker 2:** That's a thousand—

**Speaker 1:** Yeah, that's good.

**Speaker 2:** This is what doesn't mind, like for, like, in AC space, like, do you think this is useful or—

**Speaker 1:** Yeah, I think so. It's really fun.

**Speaker 2:** I'm sorry, you think that's what we wanted? Is this the proposed, like, workflow? Like, which, at least the middle parts of it, like, are—

**Speaker 1:** I have to look at why she skipped the first two tabs, but—

**Speaker 2:** Sorry?

**Speaker 3:** Could you share—

**Speaker 2:** Yeah, share the video. I'll just share the video on the Slack.

**Speaker 1:** Yeah.

**Speaker 2:** Yes, please.

**Speaker 1:** Maybe we also go around and just each comment on a couple things.

**Speaker 2:** I think the UI needs a lower—

**Speaker 1:** Yeah, yeah, yeah.

**Speaker 2:** Yeah, that can be polished.

**Speaker 1:** But generally, like—

**Speaker 2:** It's dressing up.

**Speaker 1:** Yeah. Like, yeah, let's go around. Like, what do you think from, like, the initial, like, user flow and, like, the types of things that, like, what do you think?

**Speaker 2:** Let's start with the first reactions.

**Speaker 1:** First reactions.

**Speaker 3:** We start with an address. The platform fetches zoning, lot area, FAR, yearbuild, landmark flags, and flood zone automatically.

**Speaker 2:** Okay, coming fast. What would it look for?

**Speaker 1:** As they are?

**Speaker 2:** I know, but like, why is that relevant?

**Speaker 1:** Uh, for how— if you want to build something, or build on top of it, you want to know your FAR, to know how much you can build. If it's an existing two-floor building but your FAR is 5, you're like, oh, maybe I want 5 floors.

**Speaker 2:** What if we, like, by adjacent, like, do we— should that be a parameter?

**Speaker 1:** There could be a parameter on adjacent airports.

**Speaker 2:** Airwright? Like air rights or—

**Speaker 1:** Air rights.

**Speaker 2:** About, like, you know, like—

**Speaker 1:** Yeah, yeah. It's an additional parameter.

**Speaker 2:** Yeah.

**Speaker 1:** I mean, it's the standard, standard, like, zoning. These are just, like, standard things. I mean, like, I think from, like, the high level, like, are there any, like, red flags or, like, major gaps from, like, just the value proposition standpoint and, like, the user flow?

**Speaker 2:** I don't know about the— I mean, the first step is pretty generic, right? Like, the real impact is what historic data it fetches using this input.

**Speaker 1:** Yeah, that's right.

**Speaker 2:** So, so yeah, I don't have any opinion on that. I just want to see how it can make it.

**Speaker 1:** Yeah, sorry, could I just also comment on this first page? Everything on the first page is not very valuable, it's just like a quick check, except for the last sentence.

**Speaker 2:** The adjacent building one?

**Speaker 1:** Yeah.

**Speaker 2:** Okay.

**Speaker 1:** Yeah, in some ways it's like, I don't particularly— I mean, maybe, maybe not. Like, it's not like this needs to necessarily be like a thing that you stop on. It's like, I want to get to the thing.

**Speaker 1:** Like, this should be like in whatever, like the UI is like separate, but like, this should be information that can be like seen.

**Speaker 2:** It's on the loading screen almost, like until you say it.

**Speaker 1:** Yeah.

**Speaker 2:** But like, yeah, just I want to understand quickly, like, what those implications are from the historical data, I think. All right, let's see, go next.

**Speaker 3:** Next, we set the stage: late design before filing, the job type, an alteration, and the work types—excavation, foundation, SOE, and structural. Drawings can be added too.

**Speaker 2:** Can I stop there for—

**Speaker 1:** Yes.

**Speaker 2:** So, so selecting a project stage, select a job type, select work type.

**Speaker 2:** I just feel like this is mostly structural engineering, like, but we are talking about many different aspects. I feel like I don't know why it's like singularly, like, only focusing on structural aspect of it.

**Speaker 1:** Are you talking about work types?

**Speaker 2:** Like input types, I guess. It's like, it seems like it's only structural.

**Speaker 1:** Yeah.

**Speaker 2:** Yeah, I mean, there's facade, there's sprinkler, but what's missing?

**Speaker 1:** Like a fire.

**Speaker 2:** A fire.

**Speaker 1:** A fire.

**Speaker 2:** Or like model, like, like, you know, model data, right? Like, because 2D plans are kind of dead, dead. There's, like, it's just limited to the vectors, but if you have, like, a complement where, like, a connection to brevit also informs it.

**Speaker 1:** Yeah. I mean, I wonder, like, how many, like, I would guess, like, a pretty small percentage of, like, the, like, renovation projects would have, like, their models. But, like, it's a question mark.

**Speaker 2:** I would argue, I would argue, like.

**Speaker 1:** What do you think?

**Speaker 2:** There's a workflow that people are looking more and more nowadays where they use.

**Speaker 1:** Scan to them?

**Speaker 2:** Like, not even scan to them, but clock code and plat code and PDFs, and it models it.

**Speaker 1:** Oh, that's true.

**Speaker 2:** So it's pretty accessible.

**Speaker 1:** That's actually interesting, yeah.

**Speaker 2:** And it's, like, you know, business-wise, like, it seems that it makes more sense than— like, for example, for we're doing a brownstone, right? Like, it seems cheaper to do that than to, like, scan the entire brownstone.

**Speaker 1:** Oh, yeah.

**Speaker 2:** For a NASA where you could just get the drawings from, like, a— from, like, a set.

**Speaker 1:** Yeah. So would this build that model from the inputs, or would you bring that in later?

**Speaker 2:** I would say structures.

**Speaker 1:** Yeah.

**Speaker 2:** It's too delicate to do that. Like, I feel like I would rather trust a BIM model that has a structural, like, stamp on it, right? Like, and that way, that's where the connector kind of makes sense because then it's like— then it reduces the potential hallucinations, I guess.

**Speaker 1:** Yeah.

**Speaker 3:** I have a question on the work type section. I don't fully understand why we need to click boxes in that section. Because if you have excavation as a task, then you will have foundation and wall and everything, because that means you're, like, building from scratch.

**Speaker 2:** Oh, yeah.

**Speaker 3:** That's true.

**Speaker 2:** Yeah. Yeah, right.

**Speaker 1:** That's true. It should intuit, like, what is dependent on it, on other things.

**Speaker 3:** Yeah. And you already selected alteration or new building or demolition.

**Speaker 2:** Yeah, it should automatically assume all that, like, not like we have to click that. Is it, like, is it only doing facade? Is it finishing the sprinkler?

**Speaker 2:** Like, what's the logic? I mean, curator work's logic, I guess, in terms of work type.

**Speaker 2:** Like, what does it mean? It's like the work that's being done.

**Speaker 1:** The work that will be done.

**Speaker 2:** Like the scope of work.

**Speaker 1:** Yeah, the scope of work, basically.

**Speaker 2:** I think by default it's all selected, right? So it's just giving me the option to—

**Speaker 1:** Okay.

**Speaker 2:** Oh, like, unselected.

**Speaker 1:** Yeah.

**Speaker 2:** So now we'll control over what's— but I guess.

**Speaker 1:** I feel like DOB NOW kind of helps, has a structure for that, right, where you go in and you put in details and it'll automatically know what specific work types to go with whatever you start with, right? I have to double-check though. Like, see if I have a DOB NOW account.

**Speaker 1:** Because we could be, like.

**Speaker 2:** Should that be an input as well, DOB NOW, like the PDF?

**Speaker 1:** I have the PDF.

**Speaker 2:** I mean, just for the sake of the tool, like, we are inputting structural drawings. Do you read the structural information? Or do you think we can use another layer of input, like, by taking the DOB form, like the DOB NOW form?

**Speaker 1:** Yeah, I was thinking we could borrow from the form to help structure that part specifically. Because, you know, it's not— DOB NOW is not perfect, but I think they get that part right. But let me double-check though.

**Speaker 2:** I like the brevit connector. How hard do you think it's going to be for the—

**Speaker 1:** Not hard at all.

**Speaker 2:** Like, connect— because there's two types. You could do a bidirectional connection, which I don't think is needed because it's like you're constantly changing ship.

**Speaker 1:** Yeah, you just need a one-time.

**Speaker 2:** So you could just have like a— like a one-direction where you just, like, when you're ready, you click it.

**Speaker 1:** Yeah.

**Speaker 2:** And one thing that—

**Speaker 3:** Sometimes systems shut down.

**Speaker 2:** It already is in places.

**Speaker 3:** Your system is always down.

**Speaker 2:** Is there anything wrong?

**Speaker 1:** Uh, the DOB, you know, government site is always—

**Speaker 2:** Oh, I thought it was full-form.

**Speaker 1:** Oh, no, no, no, no.

**Speaker 2:** Yeah, what were you saying? So, like, in general, I don't know too much about the structural side of BIM, but, like, on top of, like, you know, families have, like, parameters and stuff, like, there are solutions for things like COBI, which is like post-occupancies, like, workflows where, like, you deliver more than just a building and you deliver, like, extra things like, you know, manufacturing and kind of details. So you can essentially develop a tool that, like, well, let's say maybe through Excel or any sort of

**Speaker 2:** input, you can identify what metadata you want to add into that Revit model and that Revit element, and then it will, like, add a parameter in for, I don't know, if, like, I don't know, load points or, like, stuff like that where, like, it's like structural data that you can add on top of what you're doing. And then the model is.

**Speaker 1:** Who's providing the data to the BIMs?

**Speaker 2:** We could, we could add, like, I don't know how it works, but it's like, we can add more data if we need to, through, like, a— like, it doesn't even need to be through the Revit. It could be through, like, Excel. It could be through, like, you know, just, I don't know too much about the structural side, but, like, for example, when you have a BIM, like, what are structural important, like, what is structural relevant data?

**Speaker 2:** Like, point of reflection, like, all that stuff, like.

**Speaker 1:** Yeah, like the sizes, like the flange, thickness, the depth, the width, like.

**Speaker 2:** That is, yeah, that is probably already— I guess what I'm trying to say, like, those parameters, if they're not already part of the metadata of the BIM, we could add those.

**Speaker 1:** When does that matter in our study, though? That's my question.

**Speaker 2:** Because, like, because we're not— we're not going to do an existing building structural framing assessment because that's too much on over, like, over design. We just want to extract the very basic information from existing structural document to determine what type of structural system they have. And that's it.

**Speaker 2:** We're not going to, like, examine if this wood is deteriorating because we cannot know from. I guess maybe then, in that case, like, if you determine, you can, like, if it's an SBO, it's probably not going to have metadata because you haven't modeled it in Revit.

**Speaker 2:** But if you have a document that talks about that in a Revit model, then you could probably mix that data into the data within the Revit model. Like, you know what I mean?

**Speaker 2:** Like, because you could always model anything, but if there's like a document that talks about it.

**Speaker 1:** Yeah, we usually, after we assess an existing building, we create, we, like, write a structural assessment report, and then we're going to identify all the locations that need some care, like, like water damage on the joists, wood joists that's deteriorated. We need to, like, fix that, maybe, like, sister with other new wood joists, or, like, some.

**Speaker 2:** Would you say that's not going to— we don't need that for this?

**Speaker 1:** Yeah, I don't think— yeah, we just want to get the, like, master kind of, like, general information such that we can compare with historical data. We're not—

**Speaker 2:** What would be the— what would be things you would want to get?

**Speaker 1:** Like the type of structural system? That's very easy to, for AI to determine from just looking at a structural drawing. We want to know, like, if it's existing masonry, like, hardy wall construction, wood joists, what's the structural system?

**Speaker 1:** Like, the— we usually identify as, like, a gravity system, a ladder system. I don't know if it's, like, too difficult, but the most basic information, whether it's a steel building or, like, a reinforced concrete building.

**Speaker 2:** Like the structure type?

**Speaker 1:** Yeah, like the type material.

**Speaker 2:** Oh, that's easy.

**Speaker 1:** Yeah.

**Speaker 2:** Like the structure type of that.

**Speaker 1:** Yeah.

**Speaker 2:** So maybe we— maybe we could do with just drawings, like, you know, the metadata from Revit. Like, because that probably is in a schedule somewhere, the drawings, right?

**Speaker 1:** Yeah.

**Speaker 2:** Even better, right? Like, really clear.

**Speaker 1:** Anyways, what next?

**Speaker 2:** Next one?

**Speaker 1:** Yeah?

**Speaker 2:** Oh, is he—

**Speaker 3:** This is where we— this is where we—

**Speaker 4:** Before DOB complaints, 311 reports, inspection dispositions, and FEMA and USC's flood data. Then keeps only life safety signals, like shaking, falling debris, or a building leaning.

**Speaker 2:** Okay. Yeah. So that's like, I guess, separately, you just visualize this public record?

**Speaker 3:** You know you're a target. You should just assume.

**Speaker 2:** So it's going through all the data based on—

**Speaker 1:** Yeah.

**Speaker 2:** We're not only the one site of the record. We are defining what the photos are.

**Speaker 1:** Yeah.

**Speaker 2:** And this is, like, similar buildings or your lot?

**Speaker 1:** Both, right?

**Speaker 3:** Both. Similar conditions.

**Speaker 2:** I guess this would be— this is where it would just essentially show that map type you would, you would, like.

**Speaker 1:** Yeah, it's the next one.

**Speaker 3:** He's trying to take you down.

**Speaker 2:** Anyway.

**Speaker 1:** Guys, I'll be tired of what's going on.

**Speaker 2:** I'm rolling.

**Speaker 3:** Thank you, Jensen. Anything new? Has there been more than three?

**Speaker 2:** Okay.

**Speaker 3:** No, we're good. I mean, it's actually way easier to process.

**Speaker 1:** First, present.

**Speaker 2:** Wait, wait, wait. Thoughts on this slide? Are you fine with this?

**Speaker 3:** Yeah, maybe. I think, like, okay, so DOB complaints. I mean, that's not, like, the main one.

**Speaker 3:** Like, obviously, like, we need to prioritize.

**Speaker 3:** Like, I think it's not capturing, like, all the data sources that we talked about. So that is— it's just not— it's not complete.

**Speaker 2:** I think it's only capturing the ones we talked about. I'm sure there's a lot more.

**Speaker 3:** I mean, in the— I guess, yeah, maybe we— we don't have, like, a synced plan yet, so that's probably why.

**Speaker 1:** Keep only life safety signals. I mean, I think we would want to have, like, life safety signals are, like, sort of sorted, like, and prioritized, but we'd still, like, maybe— we talked about, like, other signals, like, still being included, but filtered, maybe. That's my sense.

**Speaker 1:** Yeah, I think this is probably the most important thing. Like, I'm not sure that, like, it's, like, necessarily, like, as a user flow, like, a step-by-step.

**Speaker 1:** Like, I imagine, like, you're in there, but, like, the map view, like, is the main.

**Speaker 2:** It's your home.

**Speaker 1:** And, like, you're bringing in data sources from there. Like, you could see where, like, what all the data sources are. Like, you could add other ones, potentially, or, like, you know, toggle on or off.

**Speaker 1:** I mean, maybe, but, like, you have a very clear sense of, like, you are in this map view. Like, I'm sort of thinking, like, what we're missing is just, like, a centralized user sort of, like, home base, which is.

**Speaker 2:** In the video you're making, can you make sure that the second tape of making a video is maybe that sort of a look?

**Speaker 1:** Yeah, yeah. Yeah, yeah. Okay.

**Speaker 1:** Anyway, yeah, I think, like, the map is next, but, like, we can look at that too.

**Speaker 4:** On the 2-and-a-half D map, the site sits next to a free wardrobe.

**Speaker 1:** It's like, I don't need to know that.

**Speaker 4:** And a shared party wall. Similar cases from across the city appear alongside.

**Speaker 3:** This is my favorite. This one, yeah, that's part of that.

**Speaker 2:** Yeah. I would like, like, more—

**Speaker 3:** It could be more—

**Speaker 2:** Yeah, it's just—

**Speaker 1:** It's not detailed enough.

**Speaker 3:** More real, but, like, yeah, I want more of the flip in the structure. I want to move it.

**Speaker 2:** Google photogrammetry type thing. I don't know. That would be nice.

**Speaker 3:** Yeah, not just a block.

**Speaker 2:** Yeah.

**Speaker 1:** It depends. I mean, it's a good question of, like, the level of detail. I don't know if it needs to be, like, super, super detailed, but, like, the information that is, like, relevant needs to be presented in a clear way.

**Speaker 3:** Yeah.

**Speaker 1:** Which, like, right now, I mean, it's not clear, obviously.

**Speaker 3:** Yeah.

**Speaker 2:** I guess that might be easy to do with, like, a case study. Do you guys have any, like, any building or project that you can pull up from your past, or?

**Speaker 1:** I mean, it's— we're talking about the—

**Speaker 2:** A site that has structural, like, collapse, right?

**Speaker 1:** Yeah.

**Speaker 3:** We could pull—

**Speaker 2:** We could pull—

**Speaker 3:** None of the things I built have collapsed. Like, another demo. Like, all the example ones.

**Speaker 3:** I know. I also generated something that we can look at later.

**Speaker 3:** Okay, sure, we can look at— well, do you want to look at all of them and then comment, or after this?

**Speaker 2:** Whatever you guys want.

**Speaker 3:** Okay.

**Speaker 4:** You can ask the agent questions in plain English, and every answer points to the records behind it. The result is one dashboard, split by discipline, with actions for structural, geotechnical, the architect, and the contractor. Code, data, and AI flag the risks.

**Speaker 4:** Engineers review them.

**Speaker 2:** Like, as an idea.

**Speaker 3:** Yeah. That, like, it's the entire team seeing what everyone is concerned about.

**Speaker 2:** Are we actually going to have ask the agent thing? Is that a new feature?

**Speaker 3:** That's a new feature. That chat feature, that's— that's not very unique. Exactly.

**Speaker 2:** It's not unique, but—

**Speaker 3:** It is helpful.

**Speaker 2:** Can you implement something like that for this algorithm? Like, can we implement that? Which one?

**Speaker 2:** Ask the agent.

**Speaker 3:** It's supposed to be a graphical.

**Speaker 1:** Like, LMA.

**Speaker 2:** Okay.

**Speaker 3:** Yeah.

**Speaker 2:** I think you should. You—

**Speaker 1:** You just got to remove our API key after that.

**Speaker 3:** Oh, wait. We wouldn't put— wait, wait, from what?

**Speaker 2:** Are you— are we putting our own API key or something for the agent? Or how is it like working?

**Speaker 3:** Oh, yeah, yeah, yeah. I see what you're saying. Yeah, like, as a test with, like, a sandbox, like sandbox or solutions.

**Speaker 2:** Yeah, I think the chat layer is necessary.

**Speaker 3:** Yeah. Is that the end of the video?

**Speaker 4:** Everyone on the project, including DOB, works from the same dashboard before work starts.

**Speaker 3:** It feels like a call-out, including DOB. Because you guys typically don't—

**Speaker 2:** We are the worst on the team.

**Speaker 3:** Exactly. Okay, let me share a video. So my— my vibe code generated a teaser video and a page.

**Speaker 2:** Oh, really?

**Speaker 3:** Yeah. Should I make an AI video? Can you guys ask?

**Speaker 2:** Yeah, perfect.

**Speaker 3:** So, hold on. First, this is a video.

**Speaker 2:** Oh, yours doesn't have audio, or?

**Speaker 3:** No, it doesn't have audio.

**Speaker 2:** Can you— can you give us, like, a little—

**Speaker 3:** Ooh, I like that. I like the darker interface. Really?

**Speaker 3:** I was—

**Speaker 2:** Or just a— just, like—

**Speaker 3:** Classic flaw.

**Speaker 2:** Yeah. It's just a generator.

**Speaker 3:** Yeah. That's what I don't like about— Okay. And then the website.

**Speaker 2:** Oh, it's done. Yay.

**Speaker 3:** Yeah. It's, like, broken down by faces, and then you have a project.

**Speaker 2:** I like the zoom-in feature.

**Speaker 3:** Um, site intelligence.

**Speaker 2:** Whoa.

**Speaker 3:** Oh, no. I zoomed out too much. I lost the site.

**Speaker 3:** Can I click onto these ones? Yes.

**Speaker 3:** Nearby risks. Sites.

**Speaker 3:** Hold on. Not very functional.

**Speaker 2:** This is—

**Speaker 3:** This is not really useful.

**Speaker 2:** That's cool.

**Speaker 3:** Why this is relevant to my project.

**Speaker 2:** Not really.

**Speaker 3:** During analysis. Very back to back. Risk register.

**Speaker 3:** It also kind of assigns a person.

**Speaker 2:** Yes.

**Speaker 3:** You could change it to another person. Yeah. Project coordination.

**Speaker 3:** And lastly, it does have a chat box.

**Speaker 2:** That's pretty neat.

**Speaker 3:** Everything needs a chat box.

**Speaker 2:** Yeah.

**Speaker 3:** And I have the link in the Slack group, so you guys can play around.

**Speaker 2:** Okay. Oh, for the website?

**Speaker 3:** Yeah.

**Speaker 2:** Oh, wow. You published it?

**Speaker 3:** No, it's a preview link.

**Speaker 2:** Good stuff. How long is your video taking, man?

**Speaker 3:** Maybe—

**Speaker 2:** So anyways, pulling in stuff. Oh, wait. Oh, loveable.

**Speaker 3:** Can you see it, or do you need permission?

**Speaker 2:** Well, I'm seeing. If I need to log in, please.

**Speaker 3:** All right, let's try this. So this doesn't include— it downloaded.

**Speaker 2:** Weekly ends— third weekly ends tomorrow, right? Like, we can just, like—

**Speaker 1:** You know, just resets by the time you're back.

**Speaker 3:** All right.

**Speaker 2:** Oh, no.

**Speaker 3:** We're online.

**Speaker 2:** He does want to keep this. Oh, it resets now at 7:00 PM.

**Speaker 1:** Or, like, the file will upload as to models.

**Speaker 2:** I guess weekly at 7:00 PM.

**Speaker 1:** Can you check this one?

**Speaker 2:** Yep.

**Speaker 1:** Wait, do you want to wait for—

**Speaker 2:** Oh, did you do that?

**Speaker 1:** Oh. Oh.

**Speaker 2:** Okay.

**Speaker 1:** It— it— it—

**Speaker 3:** That's me. I'm through. We're going to watch this video.

**Speaker 1:** One more slide or something.

**Speaker 3:** Sorry?

**Speaker 2:** Oh, there's something else.

**Speaker 3:** Oh, I got to go over there.

**Speaker 2:** Oh, I have two bags. I have this— no, no, no. All that came inside of this bag.

**Speaker 1:** Where did you get that one from?

**Speaker 2:** AU. Oh, okay.

**Speaker 3:** Print flight. Project risk intelligence for New York City. One shared view of a site, its neighbors, and what each party needs to check.

**Speaker 3:** On November 11, 1321 Flatbush Avenue collapsed into the excavation next door. The cause is under investigation, and we don't assign responsibility.

**Speaker 2:** That's a dark background.

**Speaker 3:** The dark background.

**Speaker 3:** Starts with an address and a project title. Pre-flight pulls the site, every touch and lock, and their DOB, complaint, and 31 record.

**Speaker 1:** Pause real quick.

**Speaker 3:** The site is red, its neighbors angry.

**Speaker 3:** The neighbor's file is mostly housing violations. Those don't predict structural risk, so we show them without scoring them.

**Speaker 3:** Replay the site's record as of June 1. Demolition, excavation, and foundation violence, and a March violation because protection for adjacent properties wasn't installed.

**Speaker 3:** In April, a violation for working through a stop-work order. Public more than 6 months before the collapse, but on the site's record, not the neighbor's.

**Speaker 3:** Move the date to November 11. Nothing after that day leaks in.

**Speaker 3:** The checklist is organized by party, from the building code duties toward adjoining property. Does each duty apply, what proof exists, and what's missing.

**Speaker 3:** Proof is never inferred. Open gaps are in red.

**Speaker 3:** Protecting the neighbor's foundations applies here, and no proof is on the record.

**Speaker 3:** The adjoining-only view turns each proof into a question the neighbor can ask.

**Speaker 3:** Similar cases across the city, shown here as samples, quoted as publicly recorded.

**Speaker 3:** Next, and not built yet. Three project stages, more life safety layers, plan and read-it-up work, and an agent to ask what to check.

**Speaker 3:** Everyone saw one piece. Pre-flight shows the whole picture and who owns each check.

**Speaker 3:** I like pieces of each one.

**Speaker 2:** I would say it's a dark—

**Speaker 1:** It's a dark—

**Speaker 2:** I think November 11 would go away from the pre-flight name.

**Speaker 3:** Yeah.

**Speaker 2:** Because, like, not, like—

**Speaker 3:** Oh.

**Speaker 2:** Yeah, yeah.

**Speaker 1:** Let me be honest. I found that boring.

**Speaker 3:** It was— it was very, like—

**Speaker 2:** Yeah.

**Speaker 1:** Oh, yeah.

**Speaker 2:** Very—

**Speaker 1:** It's just a one-passed over.

**Speaker 3:** It was not, like, yeah, a pitch. It's more of, like, yeah, just— I guess it's sort of showing, like, this example. I didn't even prompt it to do that, but it's, like, showing that project and, like, kind of, like, what the considerations were, like, were not.

**Speaker 3:** Yeah. Did like, the map view with the subtext on the side.

**Speaker 2:** Mm-hmm.

**Speaker 3:** Me too.

**Speaker 2:** It's interesting. Yeah. I mean, it mispronounced rivet to rivet.

**Speaker 3:** Rivet.

**Speaker 2:** Rivet.

**Speaker 1:** Oh.

**Speaker 3:** Rivet. My brain was processing. It took a minute to generate.

**Speaker 3:** Everyone's using their correspondent. I want to see, like, I actually never generated a video with AI before.

**Speaker 2:** Oh, yeah? Not really.

**Speaker 3:** It was the first video.

**Speaker 2:** They're really good.

**Speaker 3:** Okay.

**Speaker 2:** So how are we, like, moving forward from here?

**Speaker 1:** Third transcript, right?

**Speaker 3:** I think, yeah.

**Speaker 1:** Yeah, third transcript.

**Speaker 3:** Let's watch all the videos first.

**Speaker 2:** Yeah, yeah.

**Speaker 1:** Okay.

**Speaker 2:** You're making one of these.

**Speaker 3:** Yeah, it's just— this is on the way.

**Speaker 2:** Make the videos.

**Speaker 3:** Yeah.

**Speaker 2:** Yeah.

**Speaker 3:** Sorry. I feel like the end result, we could present a very short pitch deck and a demo video.

**Speaker 2:** Mm-hmm.

**Speaker 3:** Once we get the website, we could have a video be made from what the site actually looks like.

**Speaker 1:** Yeah, we should show, like, a live demo.

**Speaker 2:** Yeah.

**Speaker 1:** We should have, like, the product.

**Speaker 2:** Okay.

**Speaker 1:** But is the workflow— is this the, like, workflow we had in mind, or?

**Speaker 3:** It's all forming right now.

**Speaker 2:** Yeah.

**Speaker 3:** It's forming. It's coming together.

**Speaker 2:** I mean, I think, like, it seems like, yeah, sort of, like, there's, like, a view of any particular property, and then, like, there's all the, like, data that's associated with, like, past examples that are similar.

**Speaker 2:** And in some ways, like, I wonder, like, do you want to be able to see more of, like, the map and the similarities, like, visually, or is it more about, like, the information that's, like, sourced?

**Speaker 2:** Like, I found that one to be, like, there's, like, way too much stuff.

**Speaker 3:** Yeah.

**Speaker 2:** Like, you can get too— like, imagine, like, you can get overwhelmed.

**Speaker 3:** Yeah.

**Speaker 2:** So it's like, how do you surface the right information at the right time?

**Speaker 1:** I think— I think the chat layer is very important. You know, you have a huge payload of data that the chat is looking at, and based on what you're saying to it, it can go back between what you're saying, going back between the payload, and you can get— you can arrive at a place that makes sense for you in the workflow, right? I think having the interface be mostly chat and then having a payload of data that you can search through yourself would be, I think, a

**Speaker 1:** good way to get the best of both, essentially.

**Speaker 2:** And interact with the data in natural language.

**Speaker 1:** Yeah. And I think the visual component is doable as well. I mean, I didn't want to emphasize kind of what you were talking about in terms of hooking up, like, Revit integrations, because I also did want to think about, like, visual analysis of what a user provides.

**Speaker 1:** If we could simulate that as well. I think, in general, an interface where someone can look up an address, go to it, click on it, ask questions about it, get answers, save that in project context, continue that process, look at things, receive analysis, put that in project context, it can kind of help them.

**Speaker 1:** I think that form of an interface can help a lot of different people at any stage of the process. Does that make sense?

**Speaker 2:** Yeah.

**Speaker 3:** Yeah.

**Speaker 2:** Makes sense. Yeah.

**Speaker 1:** So, like, I guess I would picture something like a map that you can interact with and start the process from there. A map in a chat.

**Speaker 2:** Yeah.

**Speaker 1:** Info, you can toggle it, look through it as necessary.

**Speaker 2:** Okay.

**Speaker 3:** I hear you.

**Speaker 2:** I mean, that's a good feature.

**Speaker 3:** You're breaking the souvenirs.

**Speaker 2:** Yeah, it's fine. It's back in the middle.

**Speaker 3:** It's almost like a treaty.

**Speaker 2:** Is it thinking?

**Speaker 3:** It's still running. It's getting there. 8 minutes. Is this a generated website?

**Speaker 1:** No, this is not. This is the reference.

**Speaker 3:** Oh, okay. Can't tell. Can't tell what's real, what's fake.

**Speaker 1:** No, no, yeah.

**Speaker 3:** The amount of time it's taking.

**Speaker 2:** Yeah.

**Speaker 3:** Videos take long.

**Speaker 2:** Dang.

**Speaker 1:** They take longer, man.

**Speaker 2:** I think you have a good sense. Like, we'll watch that. But yeah, I mean, like, this has been really, like, insightful.

**Speaker 2:** What's the main gap? It's really, like, just making sure the data sources, like, that we pull in are, like, useful.

**Speaker 1:** Yeah.

**Speaker 2:** And then, like, how that information is represented.

**Speaker 1:** We can also filter the data sources so that maybe processing takes much shorter amount of time.

**Speaker 2:** Yeah.

**Speaker 3:** Agreed.

**Speaker 3:** Because I think, like, yeah.

**Speaker 2:** What does the DOB do in this? Just review it and approve it?

**Speaker 3:** I think they don't do anything in our process.

**Speaker 2:** Just, like, give us the information.

**Speaker 3:** Yeah.

**Speaker 2:** Oh, so we just use their data, but they don't.

**Speaker 3:** Yeah.

**Speaker 2:** So we don't bring them in until the feed.

**Speaker 3:** No. The whole point is that they don't do enough, so we need to.

**Speaker 2:** They just tell you no when you come back.

**Speaker 1:** Do they not do enough because their infrastructure is terrible? Like, are we offering them a solution as well?

**Speaker 3:** No. You have no solution.

**Speaker 1:** Well.

**Speaker 3:** We're not helping.

**Speaker 2:** It's like, they take long.

**Speaker 1:** Meaning, we're improving the whole permitting thing, not the.

**Speaker 3:** We're improving it so they don't have to say no at the office.

**Speaker 2:** Yeah.

**Speaker 3:** We're helping other people because they are difficult.

**Speaker 1:** I think, like, when we talked about the DOB earlier, we talked about how the software is really bad, and the support from the actual, like, city is basically nonexistent. Our way of mitigating that is by having this face both the person that's pushing the filing and the person that's reviewing the filing. They're both on the same platform.

**Speaker 1:** I believe that's the approach.

**Speaker 2:** So the DOB is?

**Speaker 1:** So yeah, we from, like, what we discussed earlier, they would be able to go on the platform and review a plan that's intelligent, right? But it seems like we kind of did shave that off. So I'm just explaining why we were talking about DOB and why not now.

**Speaker 1:** But.

**Speaker 3:** Great.

**Speaker 2:** Is he ready?

**Speaker 3:** 10 minutes later.

**Speaker 2:** The good thing is, oh, he has the timestamp.

**Speaker 3:** Me too, me too. All right. Hopefully it has audio.

**Speaker 2:** We'll watch that one.

**Speaker 3:** We'll see. Yeah, my screen is also broken.

**Speaker 3:** And there's no audio.

**Speaker 2:** That's fine. We'll look at it. We'll look at it.

**Speaker 2:** Pull it up here.

**Speaker 3:** Oh yeah.

**Speaker 2:** Yeah.

**Speaker 2:** Pre-flight? Pre-flight's the name?

**Speaker 2:** We're all going to Dublin right now.

**Speaker 1:** Because it was from the transcript.

**Speaker 2:** Don't show it. Don't show November 11.

**Speaker 3:** Is there a voice?

**Speaker 2:** No.

**Speaker 1:** I can't really see any of the words.

**Speaker 3:** Yeah.

**Speaker 2:** I can just say it's wrong.

**Speaker 1:** I like the UI so far.

**Speaker 2:** Yeah.

**Speaker 3:** I said think about the user experience.

**Speaker 1:** Case might.

**Speaker 1:** No, no, I'm playing.

**Speaker 3:** Girl, I need any.

**Speaker 2:** Are you able to share this link and we can do it?

**Speaker 3:** I'm going to download the.

**Speaker 2:** Yeah, I think, like, what sort of, like, stands out is, like, there's a couple instances where, like, like, there's a good amount of information, but, like, it's sort of, like, it's sequential, and I wonder if that's the right approach. Like, is it sequential or not, like, as a user flow?

**Speaker 1:** But that's the thing, right? Will it always be sequential? Like, I don't.

**Speaker 2:** Yeah.

**Speaker 1:** It has to be sequential, but then, like, you never know when the next part of the sequence might come, right? Because the other diagrams that you upload, you never know. You're just, I imagine, like, you don't have the structured diagrams yet.

**Speaker 1:** So you're just inputting the address and checking the lot out. That's it.

**Speaker 1:** And then this whole part comes, like, later on, maybe, like, after 2, 3 weeks.

**Speaker 2:** Yeah.

**Speaker 1:** So, I mean, we'll have to mention that, I guess, or something of that sort is what I'm thinking, but I'm not sure.

**Speaker 2:** The plans are not optional. Like, for example, you have to give it.

**Speaker 3:** In my demo, it's optional.

**Speaker 2:** Okay.

**Speaker 1:** Okay.

**Speaker 2:** And it could be, like, kind of, like, the way that.

**Speaker 1:** It's the best.

**Speaker 2:** But AEC has the help. Like, it's not sequential. It's sequential in the video because, like, it's you explaining it, but, like, you can always go back and add more stuff.

**Speaker 1:** Yeah.

**Speaker 2:** There's new studies for it or something.

**Speaker 1:** Do I watch the series? Let's watch it, guys. I will turn on CD myself.

**Speaker 3:** I haven't even slept.

**Speaker 2:** Look at your face.

**Speaker 3:** It's scary.

**Speaker 3:** I'm not very clear. Oh, go.

**Speaker 3:** I like it. I like the sound.

**Speaker 1:** Oh, that's it.

**Speaker 3:** Oh, that's funny. This is an advertisement.

**Speaker 1:** That was, like, too much, too much.

**Speaker 2:** It's easier.

**Speaker 1:** Yeah, yeah.

**Speaker 2:** This is a product launch video, but not, like, a demo video. This is a product launch video.

**Speaker 3:** But that's actually, like, nice.

**Speaker 2:** This is a product launch video.

**Speaker 3:** The graphics, yeah. The graphics is nice. I like the dots popping up.

**Speaker 1:** I think the dots is a little overwhelming, though. Like, I don't understand why, like, why there's so many dots. Oh, shit.

**Speaker 3:** It looks like this neighborhood is about to collapse.

**Speaker 2:** Yeah.

**Speaker 3:** Okay, so.

**Speaker 2:** Any other thoughts?

**Speaker 3:** My AI suggested a project name. It's called Foresight. It's like foresight, but the site is S-I-T.

**Speaker 2:** Ooh, that's pretty good.

**Speaker 3:** Foresight.

**Speaker 2:** Yeah.

**Speaker 1:** That's lovely.

**Speaker 3:** I thought that was a good one.

**Speaker 2:** Should we go with that?

**Speaker 1:** Yeah.

**Speaker 2:** Yeah.

**Speaker 1:** That's a great name.

**Speaker 2:** Should we just start building now?

**Speaker 3:** Yeah, we should. Yeah.

**Speaker 2:** Sometime.

**Speaker 3:** Yeah.

**Speaker 2:** Yeah.

**Speaker 3:** Are we waiting for any more demos?

**Speaker 2:** Is there anything else you want to, like, cover in this recording?

**Speaker 1:** I think we should just, like, start building it and then, like, come in and then, like, improve it.

**Speaker 3:** But it's so peaceful. Like, last year, team, they started fighting around this time. And one guy stormed out of the room.

**Speaker 2:** Maybe until it's 9 o'clock. Then maybe.

**Speaker 3:** And then we had to break out into groups and talk to them individually.

**Speaker 1:** How do we want to delegate who builds what part of this?

**Speaker 2:** Yeah, like, how do we execute this is what I'm not familiar with.

**Speaker 3:** I think, okay, so I missed out the first part. How long are we presenting for?

**Speaker 2:** In the pitch?

**Speaker 3:** Yeah.

**Speaker 2:** Should we check?

**Speaker 3:** Two or three minutes.

**Speaker 1:** Oh, we are with two, three minutes.

**Speaker 3:** Is it that short?

**Speaker 2:** I think it's not.

**Speaker 3:** It's not more than five minutes.

**Speaker 1:** I'm surprised we get that much.

**Speaker 3:** I think we have audio now.

**Speaker 2:** It's not more than five minutes.

**Speaker 3:** You got a new version?

**Speaker 1:** Five minutes. You only have five minutes for introduction, presentation, live demonstration.

**Speaker 3:** This is pre-flight.

**Speaker 2:** Oh.

**Speaker 3:** Oh.

**Speaker 1:** Oh.

**Speaker 2:** I know.

**Speaker 2:** He's on Favor 5.2 extra.

**Speaker 3:** I'm on medium. Oh, okay.

**Speaker 2:** This is the reason.

**Speaker 3:** This is a shared brief for the whole project team before anyone digs. Start with an address. Add the job type, the work, and where the project stands.

**Speaker 3:** Pre-flight pulls the public record for the site and for every lot that touches it.

**Speaker 3:** Here is the site in context. Each touching lot shows its age, its size, and its dated records.

**Speaker 3:** Select a neighbor to see what is known about it and what is not.

**Speaker 2:** I like that.

**Speaker 3:** Signals are combinations in the record that call for questions. Here, there are three. Housing violations next door are shown, but not scored.

**Speaker 3:** And what the record leaves out is named. The checklist turns signals into duties under the building code.

**Speaker 3:** Each duty has an owner, a status, and the proof it needs. Answer a question, and the rows update.

**Speaker 3:** Open a row to close its gap. Request the proof, receive it, and assign a reviewer.

**Speaker 3:** Provided is never treated as checked.

**Speaker 3:** The case library holds past failures. Each one adds questions to future checklists.

**Speaker 3:** A cause is stated only when an investigation has stated one.

**Speaker 3:** One brief carries through every stage, from acquisition to construction. The stage before excavation is built first, with more hazard layers to follow.

**Speaker 3:** Everyone shares the same brief, and each party sees what is theirs to answer. Export it for meetings, for data, or for design tools.

**Speaker 3:** Public facts, named gaps. No cause claimed and no one blamed.

**Speaker 3:** That is pre-flight.

**Speaker 2:** That's good, though. That's super interesting. Can you read it from a DOB person, like, someone from forensics?

**Speaker 1:** Yeah.

**Speaker 2:** Maybe you could explain their idea, take their feedback on it, and then. Is there anyone here?

**Speaker 1:** I'm a stuck person.

**Speaker 2:** I can read yours.

**Speaker 3:** I have a question. I love that demo. I think it missed out the floor plan part of the function.

**Speaker 2:** It's from the transcripts, mostly, so.

**Speaker 3:** Yeah.

**Speaker 2:** Do we want to do, like, integration to the software for that part?

**Speaker 1:** I think so.

**Speaker 2:** We don't go to like, what's the alternative?

**Speaker 2:** Yeah, that's a good question. Yeah, I think at the stages of, like, if there's, like, data, like, structural data from, like, how to use it.

**Speaker 2:** We could definitely build and just, like, a structural sample model for Snowden Tower, so it could add just to show that it could add info to the dashboard. It doesn't have to be, like, relevant, I guess.

**Speaker 1:** Yeah.

**Speaker 2:** So that's good. Yeah, so, okay, so you had the question of, like, the delegation, right?

**Speaker 1:** Yeah.

**Speaker 3:** Yeah, can we start with deliverables? So we said five minutes presentation. That includes pitch and demo.

**Speaker 2:** We better make sure our tech staff is, like, actually clear.

**Speaker 3:** For any reason, please do not open the windows, okay? Did someone try? Someone tried and we cannot close it.

**Speaker 3:** And it is also dangerous. Someone can fall.

**Speaker 3:** I'm just, yeah, they've told me that I should tell anybody. Someone needed some air.

**Speaker 3:** They're like, oh, suffocated.

**Speaker 2:** So live demos go a long way in these things. So that would be me. And then, like, you sort of pitch the problem.

**Speaker 2:** And then, like, I think doing, like, a video, short video, like, pitch to, like, summarize it.

**Speaker 1:** Like a storyboard type thing?

**Speaker 2:** Yeah, like, something like, in some ways, like, we could talk about it. Like, I think when we would like to have, like, you know, maybe a short, we could do a couple of ways. Like, you could do, like, two minutes first, sort of high-level pitch plus video plus demo.

**Speaker 2:** Or you could do, like, one of us, like, sort of talks about something over a video or, like, demo. Like, there's a short amount of time, so you have to convey the idea.

**Speaker 3:** I have a suggestion. Based on what you just said, we can do a short elevator pitch with a few slides, one minute, and then a video demo, one minute, and then a live demo, maybe one to two minutes. And then we can wrap it up with different personas saying what we can take out of this situation.

**Speaker 2:** Yeah. I mean, could we also, like, just have, like, if we do a video, like, we could just talk over that?

**Speaker 3:** We can try, but unless the video talks.

**Speaker 1:** It did a little stop.

**Speaker 3:** EPRI?

**Speaker 1:** Yeah.

**Speaker 2:** Oh, really?

**Speaker 1:** Integrated project risk intelligence.

**Speaker 3:** Integrated project risk intelligence. One place where a project team sees the life safety risks for a site before work starts.

**Speaker 3:** It starts with the basics. The owner enters the site address, the job type, and the work types.

**Speaker 3:** The address unlocks the public record for that site. The map shows the site and its neighbors.

**Speaker 3:** Here, the building next door shares a wall with the site, and its foundation type is unknown. Across the city, four past cases matched as profile.

**Speaker 3:** Each past case is presented as public fact, without blame. The team sees what happened, who tripped slide there, and where each one stands today.

**Speaker 3:** Risks are grouped by discipline, and every item ends with an action. The shared wall next to the excavation is the highest risk.

**Speaker 3:** The first step is to survey the neighbor's foundation. Later, the structural model arrives.

**Speaker 3:** One button can read that reads it. Columns, framing, foundations, and bearing walls join the same project, and the risk level updates.

**Speaker 3:** Earlier findings stay attached. This is a test run.

**Speaker 3:** The reading reader is built and was tested on a sample model. The site data, past cases, and risks shown here are illustrated.

**Speaker 3:** The next step is to connect the public data.

**Speaker 2:** Oh, stop.

**Speaker 1:** Yeah.

**Speaker 2:** Okay.

**Speaker 1:** I would say the structural.

**Speaker 2:** Did this book capture this? Like, it probably did. I mean.

**Speaker 1:** This book will capture that.

**Speaker 2:** I'll turn off to the close the window.

**Speaker 1:** Like, listen to all the videos and make a video.

**Speaker 1:** Yeah, the transcript, I think, is getting most of it. It might be a little confused if we talked over the video, but.

**Speaker 3:** Yeah.

**Speaker 2:** So, like, I guess we need, like, right, like, there's getting data sources, like, and making sure we have, like, the right longs. That's, like, a task. There's, like, sort of pulling it into kind of, like, the stack, like, whatever we want to do as, like, a basis of, like, maybe perhaps, like, the map.

**Speaker 2:** And then we rely on, like, sort of the mapping engine side of things. That might be two and maybe one.

**Speaker 2:** And then there's, like, the verification layer, like, making sure it's, like, actually, like, doing some sort of output that would, like, be accurate and to whatever the end user is.

**Speaker 3:** Verification.

**Speaker 2:** Verification. And then it could be also interacting with, if we have, like, forensics advisor, like, showing them some, like, iterations. And then there's also, like, the machine learning part, maybe.

**Speaker 2:** Like, I don't know if we want to even, like, start up. Like, we could see what data we have access to and, like, could we even, like, use that data as, like, a basis for, like, the foresight training.

**Speaker 2:** Like, I don't know, maybe. That could be, like, one other work.

**Speaker 2:** There could be, like, sort of whatever thing too.

**Speaker 1:** It created a ribbon connection. So you could see that.

**Speaker 1:** I need to save it as.

**Speaker 2:** Do we miss anything?

**Speaker 1:** I think you touched on what I was going to bring up, like, mapping of filing back to interpreting what is wrong with it.

**Speaker 2:** Yeah.

**Speaker 1:** All right.

**Speaker 2:** Yeah, it's interesting. Like, yeah, it's a new, it's, I mean, Alex, when he brought up the meta, like, mapping of happenings. Like, it's like, the sort of contribution model, like, I mean, we could just do stuff through GitHub.

**Speaker 1:** Oh, [name withheld]?

**Speaker 4:** How's it going?

**Speaker 2:** You work with the forensics team, right?

**Speaker 4:** Sometimes I work with them, but it's not my day-to-day.

**Speaker 2:** Can we talk something while you work with it?

**Speaker 4:** Sure.

**Speaker 2:** Guys, possibly.

**Speaker 4:** Should we show it?

**Speaker 2:** Do you want to ask him?

**Speaker 4:** Yeah. We have this tool, so we choose a lot and we enter the address and then enter the building type. And it pulls all the historic data of, like, similar construction type, like, similar condition and the risks it entailed.

**Speaker 4:** So I don't know. I feel like it's just easier to show the demo video and then kind of elaborate on it.

**Speaker 1:** What do you have the demo of?

**Speaker 2:** I see you standing near the podium. You have the demo?

**Speaker 1:** Which one is it? Which one is your show? We have, like, seven minutes.

**Speaker 2:** Okay.

**Speaker 4:** Maybe should I take this one?

**Speaker 2:** We could do a couple of them. We could say, like, I'll show you this one.

**Speaker 3:** Integrated project risk intelligence. One place where a project team sees the life safety risks for a site before work starts.

**Speaker 3:** It starts with the basics. The owner enters the site address, the job type, and the work types.

**Speaker 3:** The address unlocks the public record for that site.

**Speaker 3:** The map shows the site and its neighbors. Here, the building next door shares a wall with the site, and its foundation type is unknown.

**Speaker 3:** Across the city, four past cases match this profile.

**Speaker 3:** Each past case is presented as public fact, without blame. The team sees what happened on projects like theirs, and where each one stands today.

**Speaker 3:** Risks are grouped by discipline, and every item ends with an action. The shared wall next to the excavation is the highest risk.

**Speaker 3:** The first step is to survey the neighbor's foundation.

**Speaker 3:** Later, the structural model arrives. One button and reiterates it.

**Speaker 3:** The risk level of framing, foundations, and bearing walls join the same project, and the risk level updates. Earlier findings stay attached.

**Speaker 3:** This is a test run. The reading reader is built and was tested on a sample model.

**Speaker 3:** The site data, past cases, and risks shown here are illustrative. The next step is to connect the public data.

**Speaker 2:** Before we comment, let's watch this one. It has, like, a batch.

**Speaker 2:** Two people have a bridge next door. The cause is under investigation, and we don't have time for it.

**Speaker 2:** The neighbor's file is mostly house delegations. Those don't fit the construction list, so we show them what that was going on.

**Speaker 2:** We play the site's record as a June 1st demolition, excavation, and foundation filing, and a March violation because protection for adjacent properties wasn't installed. In April, a violation for working through a stock report.

**Speaker 2:** How about more than six months before the collapse? But on the site's record, not the neighbor's.

**Speaker 2:** Move the date to November 1st. Nothing after that day leaks into it.

**Speaker 2:** The checklist is organized by project, like building code changes that control the property. Does each duty imply what proof exists?

**Speaker 2:** Proof is not a screen. Nothing checks out.

**Speaker 2:** Protecting the neighbor's foundation. No proof is good enough.

**Speaker 2:** The adjoining owner isn't going to change proof into a question of doing or not.

**Speaker 2:** Similar cases across the city, shown here as cities, quoted as publicly recorded.

**Speaker 2:** Next, cannot build yet. Three projects to adjust to what life safety layers plan and data output, and an agent tasked with the check.

**Speaker 2:** So, like, the problem, like, right, like, can we have, like, different instances of, like, on a range from, like, catastrophic accidents to, like, maybe not as bad.

**Speaker 2:** Things that, like, we want to flag early stuff, like structural, like, civil and geotechnical, flooding, environmental, fire safety, hazardous material. So, like, these are things, like, we want to sort of, like, come up with a way for these things to be, like, tracked and then, like, pulling historical data so that, like, when you go to a new site, whether you're doing, like, construction or demo, like, you have a sense of, like, things that, like, you need to consider and make sure, like, are properly coordinated based on,

**Speaker 2:** like, similar profiles of projects. And then bringing, like, sort of, like, one source of truth for that for all the parties involved. So that's kind of, so, like, I guess the questions are, like, from your perspective or collaborating with folks who are, like, going to be doing this type of work and, like, are there things that would be really important to sort of, like, how would you imagine, like, sort of people interacting with this type of system?

**Speaker 1:** Yeah.

**Speaker 2:** And maybe we're recording right now.

**Speaker 1:** Well, it's not the basics of.

**Speaker 4:** Useful, you know, in the non-forensics context, right, like, when you get a case started. And there's some interesting stuff there from the forensics side.

**Speaker 4:** Do you want me to talk about the forensic perspective?

**Speaker 2:** Yeah, sure. Like, whatever comes to your mind that's, like, potentially.

**Speaker 4:** That's just where you kind of framed it from the beginning.

**Speaker 1:** Yeah. We understand that forensics is very complex. There might be multiple factors that contribute to the collapse.

**Speaker 1:** So we just want to, like, kind of sort of interpret the collapse and the reasons that you, like, identified in the report and you get similar cases in the future. And you can take the discussion kind of as, like, whether it's coordination, it's not sounds fairly based on the design, or whether it's the condition on nonstructural values.

**Speaker 4:** We've got the basic, like, we do a forensics job. That we want to make the person really amazing at. You think of big, big jobs or big news stories that are called.

**Speaker 4:** The process is like what you do.

**Speaker 4:** We look at these past documents and all the documentation available, and we basically piece together the story. And that's what was the code, what was built, who reviewed it, when was it reviewed, I know what did it change, who built it, was it reviewed after it was built.

**Speaker 4:** We basically, you're basically just putting together the story of both how the structure ended up the way it was, and then the story of what actually happened in the event.

**Speaker 4:** Because you need to know this whole backstory, but, like, you also need to know exactly what happened. So that you could piece together, you know, the what, the why is the core of it.

**Speaker 4:** And I think what I'm seeing here, you don't have a whole lot that tells you what happened. You have some nice context about why something might have happened.

**Speaker 4:** And then if you're starting a new project, it is cool to know what's gone, like, where people stumbled in the past to be a little extra careful about. I think what's hard is, like, as professionals, we're required to know everything we're supposed to do.

**Speaker 4:** That's different codes, different stamps, discipline boundaries, reporting.

**Speaker 4:** If this is supposed to augment that, you got to kind of walk the, it either needs to know everything that we're supposed to know or be really good at separating what it is doing.

**Speaker 2:** Is there, like, a place where all that is documented, like, everything that we're supposed to know?

**Speaker 4:** No, and forensics is almost always like a, you were always assembling the information. Often, like, a lawyer will hire you and give you just, like, thousands of pages of documents, and you have to reconstruct the story from that, like, huge dump. And you do some independent research.

**Speaker 4:** Sometimes the lawyer doesn't have a whole lot, and you do what you guys are doing. You go look at the public records, you check against, like, the USGS soil studies, you see, like, oh, did the engineer design it, like, knowing the soils were like this, or did they assume the soils were different and, like, that was the failure problem?

**Speaker 4:** I don't know. So the biggest risk, I think this is cool, but the biggest risk is, like, if you have this tool that's kind of, like, guiding you and helping you be aware of stuff, it's really important to know its limitations so you're not like, oh, the tool said, like, I checked these boxes, like, the reason those projects failed we have covered.

**Speaker 4:** Doesn't mean you're good, you know?

**Speaker 2:** That makes sense.

**Speaker 4:** That's the thing that comes to mind. But it's helpful, and, like, having an agent in forensics is super valuable because we are looking at these huge tranches of material. Like, we have to move through a lot of material.

**Speaker 4:** You do all this research, different public records. Even across the city, the information is across many departments.

**Speaker 4:** So tools that help structure that for you and organize it and draw connections would be really helpful. And maybe that's, like, a way that, maybe it has a few tools, like, search this database, search that database, and pull stuff in.

**Speaker 4:** But if it lets you as a user help to codify the link and, like, why those two are related and important, that could help be your project index in a way, or, like, help you. Because at the end of the day, we also, you basically write a report, and then maybe you go and testify in court as expert witness.

**Speaker 4:** Is generally the role on the forensic side.

**Speaker 4:** So if this helps you basically just collate what's important about all these documents and then tell the story, that would be really cool.

**Speaker 2:** That's interesting.

**Speaker 5:** Hi. Quick question. I was just listening to what you talked about.

**Speaker 5:** Do you think it would make this tool more helpful? Because earlier in the process, we talked about uploading floor plans, uploading existing design documentation that we have.

**Speaker 5:** Do you think it would be helpful to kind of, like, amplify that feature and use the data that we pulled to comment on the design features that we currently hold?

**Speaker 4:** Yeah, potentially. Often what, so usually something goes wrong, and you go to site, and you document that, and then you go look at any historic documentation, like old photos, and then you look at the drawings, and you kind of stitch them together. And you need to know what was built or what was supposed to be built.

**Speaker 4:** And then you're checking, it's like, okay, that's what the architect said. Maybe the architect did it all right.

**Speaker 4:** Was it the contractor, or was it just the owner didn't maintain it correctly? You're trying to tell this whole story.

**Speaker 4:** The design, whether the design was correct or not in the first place is, like, something you check against. So you need the drawings for that.

**Speaker 4:** If you, again, like, what's hard about this is so much information, you're doing all this research, and you have to stitch it together. So the drawing alone isn't, like, the thing.

**Speaker 4:** It's can you tie it to the evidence? Can you link it back to these other moments in time?

**Speaker 4:** And determine, like, what actually matters. Maybe the drawing really doesn't matter because all the material facts have to do with, like, owner maintenance in the last six months.

**Speaker 4:** Or this construction job next door and a big rainstorm, and it was just, like, a rainy February. And it's like, oh, they didn't do the shoring, and they were cited for it, and it was okay for a while, and it went unseen, but it was so wet this last month or the last three days that the soil changed, or even if we had a freeze thaw cycle for the first time, and that is what helped release, you know, the soil.

**Speaker 4:** And that's, like, so weather data. Whenever I work on these, I'm always doing, like, weather and landscape stuff.

**Speaker 4:** I'm looking at the weather, I'm looking at the soil, I'm looking at the designs and the design calculations and the permits and what was signed off on the permit. And then often we look, like, was maintenance done?

**Speaker 4:** Because there's what you design for performance, but if something fails after 30 years, it's usually just because the weather patterns have changed or the year was weird or nobody ever, like, maintained the system. So those are, like, other, like, the weather is very interesting and often very material to these stories.

**Speaker 2:** When you. Super insightful. Like, when you were saying, like, you'll sometimes get, like, these huge document packages from lawyers.

**Speaker 2:** Like, where do they get those from?

**Speaker 4:** They get them from public record, or they get them from owners or.

**Speaker 2:** Okay.

**Speaker 4:** You know, sometimes they, sometimes it's they're already in a case, and they get it through discovery. Like, they basically subpoena people to produce the documents.

**Speaker 2:** Yeah.

**Speaker 4:** It's always different, you know? And it changes who your client is. Sometimes you're working for an insurer, sometimes you're working for an owner, sometimes you're working for a lawyer.

**Speaker 4:** It's like, you can kind of come in from a lot of different angles, and you often, it's like, maybe you give stuff, but you can't just take what you're giving as the baseline. You almost always have to do your own checking to make sure there's not more data out there.

**Speaker 2:** So from, well, I actually had two questions, but I forgot the first one.

**Speaker 2:** But the second one is, like, if you are, this is more, I guess, on the side of, like, after, right? It's less of, like, the foresight and predictive, like, aspect, and it's more like, we are investigating what happened, trying to get all the data.

**Speaker 4:** Predictive is cool. Predictive is, like, if you're, like, basically just pulling these records every day and identifying suddenly that, like, wait a minute, this violation happened, and then that wasn't recorded, and then, like, nothing's come in in three weeks. Like, shouldn't that have been addressed and been noted by now?

**Speaker 4:** Like, this is a, this suddenly has become a more high-risk spot. That's a very interesting angle.

**Speaker 2:** Exactly.

**Speaker 4:** We're actually recording a quick session here. The six times these three sequences of events occurred in the past, you know, resulted in a bigger incident, you know, at step four. That's all, that would all be, like, cool predictive stuff.

**Speaker 3:** I had a question. Like, for this system which you've seen, like, we're building, who do you think will it be its primary user, and what do you think it'll use it for? Like, getting it right.

**Speaker 4:** I don't know, man. You got to name it. I think I'm not going to join your team, but I think you have some interesting pieces here, and you can have a lot of different users, but it's, you should pick one or two and try to really tease it out.

**Speaker 4:** Otherwise, it'll be a little bit too incomplete.

**Speaker 3:** Okay.

**Speaker 4:** I think the predictive thing is fun. I think just, like, knowing what's gone wrong in the past, like, knowing the horror stories. I mean, one, that's great when you're young in your career.

**Speaker 4:** You don't know what you don't know. And, like, usually, you need to have a whole career to see the lessons learned and know all the ways people, like, make honest mistakes or nefarious ones.

**Speaker 4:** Like, getting kind of, like, a profile of things to look out for, which, sorry, there's, like, an educational thing there that's kind of, like, useful. On the forensic side, I really think, like, needing something that helps you index all these documents and tag what matters about the relationships and the sequence of events.

**Speaker 4:** That's, like, the really hard meat of the forensic work. So there's something here that helps you do the research, codify the relationships.

**Speaker 4:** What I saw in those videos, at least, was that they were telling a little bit of the story for you. So it has some capacity to do that reporting.

**Speaker 4:** And so that's, I wouldn't trust the system to do it all, but help me maintain the ledger and help suggest maybe relationships. That's useful.

**Speaker 2:** Is are most of the documents that you would get, like, you would need to, like, sort of synthesize everything, like, public record? Like, could we tell a story with things that we could find?

**Speaker 4:** Not always. I mean, often you're looking at, like, drawings and stuff that aren't necessarily in the public record.

**Speaker 2:** Right. But we could have, like, a starting point. And, oh, so the first question was.

**Speaker 4:** A lot of the data is, you know, the DOB stuff, the historic weather, the soil, you know, how the zoning changed, what was the building code when it was built, all that stuff, you know, is definitely always part of the story.

**Speaker 2:** And the other question was, are you able to share an example of a project that you worked on?

**Speaker 4:** They're always, I mean, they're almost always illegal, you know, a legal proceeding, and it's confidential. It's like, we're extensions of the lawyers.

**Speaker 2:** No kidding. Yeah.

**Speaker 4:** So, but it's easy for me to give you, like, you know, typical things, you know, something collapses, you know.

**Speaker 4:** We had, and they're in the news too, you know, this stuff's always in the news. If you just search, like, the DOB records, you get New York City examples very easily.

**Speaker 4:** For me, I've worked on a lot of things where stuff starts flooding or water's going where it's not happening. We do construction.

**Speaker 4:** Construction losses are a big one. If a storm happens while stuff's under construction, it's, everyone's like, well, who's at fault?

**Speaker 4:** Like, did the crews actually, like, put all the protective measures in place? Or were they kind of mean and lazy because it's like, they just want to build it.

**Speaker 4:** They don't want to, like, protect. And then half of slope washes out or, you know, stuff gets blown over in a storm.

**Speaker 4:** And, like, so those, that's, you can just imagine. It's easy to imagine.

**Speaker 2:** Yeah. Cool.

**Speaker 4:** It's cool. The video's fun. The video's fun.

**Speaker 4:** I can see that there's something.

**Speaker 2:** Appreciate it. Yeah. Do you mind if we use your, this recording to inform our, like, we recorded this.

**Speaker 4:** Oh, you should have mentioned that. Don't replay it for people, but if you want to.

**Speaker 2:** No, we're not going to replay this. We just want to, we've just been recording the transcript.

**Speaker 4:** I didn't share anything damning.

**Speaker 2:** Using the transcript to help the product. No, it's not, we're not going to use your, like, actual work, but just, like, we're getting the feedback on the product into here. Should I just close that?

**Speaker 2:** I wanted to make sure.

**Speaker 4:** Glad you asked.

**Speaker 3:** Gotcha. Yeah. Thank you so much.

**Speaker 2:** Appreciate it. Cool. Thanks, [name withheld].

**Speaker 4:** Sorry, I was, like, grabbing trash in my pocket.

**Speaker 2:** Cool. All right. So maybe we stop this one, or do we keep it going?

**Speaker 2:** Stop it. Let's get this.

**Speaker 2:** Bring this in.

**Speaker 3:** Yeah.

**Speaker 2:** I think we'll kick off the meeting.

**Speaker 3:** Let's hear everyone's thoughts on it. Should we record this? I think we should focus on one user.

**Speaker 3:** Like, we should do, like, a transcript of our thoughts.

**Speaker 2:** Should we just keep it in this?

**Speaker 3:** I think, I think we should end it. I think this is a long one.

**Speaker 4:** I just want to signal to it so it focuses on what he said. This last stretch of information is important.

**Speaker 2:** Okay. Yeah, this was, this was a, the previous, like, interview that was just recorded was with a structural engineer and forensics sort of advisor expert that, you know, was helpful for us to get feedback.

**Speaker 3:** I think you brought up a great point, and there's also something that I still question about, is that there's no way that the list we created is an exhaustive list for what they should do to prevent the collapse. Like, it's not exhaustive. It's just, like, recommendation based on historic data.

**Speaker 3:** Because, as he said, the structural engineer, they are supposed to know what they're doing, and they're supposed to produce the drawing that's done, and they're responsible for anything that they misdesign. But we're just, like, so I'm just thinking, how useful is it for a structural engineer, like, in a global perspective, if I just take on a job that I have a quick search and have this, like, presented, like, graphical information right in front of me, it's very good.

**Speaker 3:** But, like, on the other hand, like, I have to know this anyway, just, like, if it's just, like, structured. But if it's, like, coordination, maybe it's more valuable, like, there could be coordination with, like, some other parties that I should make sure it's done, even if it's not fully measured, something like that.

**Speaker 2:** I mean, I think, yeah, like, he brought up some good points about, like, the aspect of the prediction. Like, we can get, like, whatever data sources we can and focus on, like, these are, this is a guideline. It's not, like, we're saying we're replacing, right?

**Speaker 3:** Just a reference.

**Speaker 2:** It's a reference point. And then there is the forensics angle, which is quite interesting, like, from the perspective of, like, after something happens, bringing in all the information. And that's a real problem of, like, these huge, you know, bodies of, like, files and, you know, documents that people have to source through and, like, find the relevant information to come up with.

**Speaker 2:** So, like, AI could actually help there. I also think there's sort of, like, I mean, we're talking to sort of, like, [firm name withheld] is one of the best engineering firms in the world.

**Speaker 2:** So, like, they know their stuff.

**Speaker 3:** It is.

**Speaker 2:** Like, a lot of, I mean, and not to say that, like, other engineers don't, but, like, on any given, like, very small project in New York, like residential construction, you're not getting [firm name withheld] engineers. So, like, folk, like, it's, you know, objectively, like, not as high level of, like, engineering and, like, construction competence, I think, all the time. So it's like.

**Speaker 3:** They don't have the resources to, like, get.

**Speaker 2:** They don't have the resources, like.

**Speaker 3:** For lawyers and stuff.

**Speaker 2:** Yeah. Like, the stuff that they're doing here is, like, on the highest end of, like, what you could possibly do. So, like, for any other given job, right, like, you have folks who, like, yeah, they have their licenses, but, like.

**Speaker 3:** But the construction in Brooklyn.

**Speaker 2:** Yeah.

**Speaker 3:** The structural engineers who have licenses.

**Speaker 2:** Yeah. Exactly. So, like, this is sort of, like, it's not, like, the main users are not, like, the best engineers in the world.

**Speaker 2:** Like, probably. It's, like, the folks who are, like, you know, they're just doing, like, and the same thing with, like, DOB.

**Speaker 2:** Like, the examiners, like, often are licensed professionals, right? I think some of them have to be, maybe, right?

**Speaker 2:** Like, so, but are they the best architects in the world? Like, obviously not.

**Speaker 2:** So, like.

**Speaker 3:** They pay those more.

**Speaker 2:** Yeah. So anyway, like, just to put things in perspective, like, I think, like, there's this spectrum of, like, user competence, and, like, we're probably on the sort of side of things where it's like, this would be helpful because, like, they don't have, like, shit, it's like, the resources that, like, some of the biggest engineering firms.

**Speaker 3:** So we help the public defense attorneys of engineering.

**Speaker 2:** Yeah. I mean.

**Speaker 3:** So parsing through, like, legal data, like, legal documents, yeah, like you said. I don't know how to sell this point because the structure, like I said, the structural engineers don't want to use this product because by using it, people are going to think they're incompetent.

**Speaker 2:** Yeah.

**Speaker 3:** It's counterintuitive a bit. So yeah, so I don't know. I think we need to refine the audience.

**Speaker 2:** Is it structural engineers?

**Speaker 3:** They're opening this platform for everybody. Like, they're just, they influence everybody.

**Speaker 2:** Yeah, it shouldn't be. Yeah, it shouldn't be.

**Speaker 3:** I think what we should do is, like, target the user. Like, figure out who's going to use the system. Okay, map the whole system around them, around that person, what they will need.

**Speaker 3:** Like, our centerpiece for the system is obviously going to be the 3D map. Like, everyone loves that.

**Speaker 3:** All of us love it. So that has to be the central piece of the system.

**Speaker 3:** And then we decide what to include, like, in the system. It's what I'm trying to say.

**Speaker 3:** The 3D map is a given. Are there users from different parties?

**Speaker 3:** Yeah, that's what he said, right? No, I meant, like, is it only going to be the structural engineer, or is it only going to be the owner?

**Speaker 3:** So that's how we define who is going to use the system. If once we define who uses the system and how they use it.

**Speaker 2:** Yeah.

**Speaker 3:** Maybe there's, yeah. Does that mean that only that person will use it? Like, is it only for a structural engineer?

**Speaker 3:** Only for a structural engineer?

**Speaker 2:** I'm guessing we'll have to restrict the scope because right now it's too broad. Right now, I mean, even he couldn't say what the school will use this product. And that's kind of, like, we need to find a user for this.

**Speaker 2:** So. I mean, in some ways, like, it's like a catch-22 because, like, what you're saying is correct, but, like, at the same time, like, the whole failure mode was, like, it wasn't, like, one person.

**Speaker 3:** One person, yeah.

**Speaker 2:** It's like, the solution is contingent on the collaborative aspect of it.

**Speaker 3:** So I guess it has to focus on the developer or the architect who can bring all the parties together.

**Speaker 2:** Get it. Yeah. I mean, right, like, who is the sort of coordinator?

**Speaker 2:** Like, it's usually the architect.

**Speaker 3:** Yeah, it's usually the architect.

**Speaker 2:** Or, I mean, it could be the developer, but largely not. Like, they're, I mean, unless they're, like, very much involved in the construction process, but, like, like.

**Speaker 3:** Maybe the future is integrated project management, right? Like, because in that situation.

**Speaker 2:** Could be, right? Yeah. So, but, like, who is, like, sort of typically coordinating trades?

**Speaker 2:** Architects, right?

**Speaker 3:** Yeah, the architect or the professional engineer.

**Speaker 2:** Could be the PE.

**Speaker 3:** Like, those are the people they distinguish most often as applicant of records.

**Speaker 2:** Yeah.

**Speaker 2:** So, like, from, yeah, like, who.

**Speaker 3:** Yeah, I think let's end the transcript.

**Speaker 2:** We can end it.

**Speaker 3:** Yeah. Let's work within ourselves and then, like.
