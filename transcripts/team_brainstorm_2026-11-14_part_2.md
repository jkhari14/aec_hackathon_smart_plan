# Team brainstorm transcript, part 2

Second problem-framing session from the 2026 NYC AEC hackathon, recorded 2026-11-14. Part 1 is [team_brainstorm_2026-11-14.md](team_brainstorm_2026-11-14.md).

## About this transcript

- It is an automatic transcription, kept word for word as provided. Transcription errors are not corrected.
- **Speaker labels do not map to one person each.** "Speaker 1" introduces themself as Hongyu early on, and the in-meeting demo is also under "Speaker 1"; "Speaker 3" introduces themself as Luis, and later answers as Jacob. The names said near the end (Jacob, Shandon, Ethny, and three more) are as transcribed and may be misspelled.

## Transcript

**Speaker 1:** Okay, we're starting.  
**Speaker 2:** Luis, you want to start us off?  
**Speaker 3:** I was about to— I mean, we're trying to say our feelings about where we currently at.  
**Speaker 4:** Yeah.  
**Speaker 2:** And things that, like, are on your mind. Like, from the plans, you know, like, what are you thinking, questions you want to answer as a group. If you say your name and say.  
**Speaker 3:** My name is Luis. Um, I guess from where we're at so far, I know we took a look at the school addresses that had some issues. I guess my question would be, like, demo-wise, we're going to expect whatever social we're going to give to also be able to differentiate when an address is also okay.  
**Speaker 3:** For example, like, that's my, like, my question is, like, are we going to be able to, like, have that as a focus as well? Like, both cases, basically.  
**Speaker 3:** And another thing I was thinking about is that with the current cases, like, the status is kind of unresolved. Like, my question is going to be, like, how can we automate, like, because the information I've gotten so far from the two sites have been from various sites.  
**Speaker 3:** We could do various sites. How can we automate this in a way that's, like, efficient when, like, buildings are older and versus when buildings are newer, I guess?  
**Speaker 2:** Do we want to pause on any of this, or do we want to just go?  
**Speaker 3:** That was something to go on. Another thing that I saw was that with the buildings, like, I know we said, like, there's a checklist we want to do based on, like, historical data, but from what I've seen a little bit, like, the buildings we were looking at, yeah, they did have a lot of, like, violations, but a lot of times they didn't even end up connecting to the main failure. So that's another thing I was wondering.  
**Speaker 3:** If we're going to be scoring past violations as, like, a— like an indicator, like, how would that work when the final we're seeing, like, the final, like, issue wasn't even something that was, like, being reported on and it's, like, another issue? Like, where is that correlation going to be?  
**Speaker 2:** What's an example of like that?  
**Speaker 3:** Um, the example being, like, for the Flatbush one, it had, like you said, 90 open violations, but it was all housing-related. It wasn't, like, structural-related. And I think I mentioned this before, that that makes sense because the residents are not going to report something structural.  
**Speaker 3:** And I was thinking, how are we going to know there's something structural to look at unless somebody makes the decision to, like, go and see if something is structurally sound? So.  
**Speaker 2:** The violations don't necessarily mean that it will lead to some structural issue. Like, some buildings could just have violations of their own.  
**Speaker 3:** Yeah, they just have violations. It doesn't mean it's structural.  
**Speaker 4:** That too.  
**Speaker 2:** Unless it's reported stuff.  
**Speaker 4:** Yeah. Yeah, unless you send somebody physically there.  
**Speaker 3:** Exactly. I'm saying unless you send somebody physically, like, you're not going to, like, just know every building there's some structural issue unless somebody's like, "Okay, wait, maybe look at this house."  
**Speaker 1:** So I think the approach we might want to take is scrutinizing what's not recorded. Right.  
**Speaker 4:** But even that, with what's recorded in DOB, are we not able to find historic structural issues related? Out of the— but.  
**Speaker 1:** Like, all the structural failure, like, if it's many years ago, there has to be an open, like, forensic report to identify the reasons. And even if not— even if it's not a full collapse, it's, like, just, like, partial collapse or, like, specific issues, then I think there are open-source information that we can find. The key is to look, like, pinpoint which specific input we want to use from past, like, cases and how to pair that with new project, like, information.  
**Speaker 1:** So I think first we should identify what type of failure we want to focus on. So we already foc— we already mentioned about full or partial collapse, but there are other safety issues that could have, like, DOB rejection or anything like— I'm not an expert on this, but I'm thinking, like, fire hazard.  
**Speaker 1:** There are, like, bars that caught fire and maybe the door is not designed properly to— to imagine, like, a situation where people have to escape, that they have enough room to get out. So, yeah, so that can be another one.  
**Speaker 1:** So yeah, that's the first step, is to identify what type of, like, failure we want to identify. And the second question would be what specific inputs we want to correlate it with.  
**Speaker 1:** And the input can be, like, zoning district, like, lot area.  
**Speaker 4:** That's just address.  
**Speaker 1:** Yeah, address and, like, FAR ratio allowed, year built, landmark and historic flags. And if possible, geotechnical and structural information. And yeah, just to identify the inputs we want.  
**Speaker 1:** And secondly, it's the approach, how we get the data. We have different— we already identified different sources, data sources that we can use.  
**Speaker 1:** I guess we can just, like, research more on how we get those historic data. And the last question would be about the output.  
**Speaker 1:** So we have all the inputs, we have the data sets, we do, like, data processing, and what the output, like, what the product will look like. Right?  
**Speaker 1:** We were talking about a website where we'd checklist for different parties, like, to make sure they coordinate things properly, but, like, to just to make it more specific. So, yeah, and I forgot to mention, my name is Hongyu.  
**Speaker 1:** So, yeah, that's my main suggestion and questions.  
**Speaker 2:** I think for, like, we should go back to Luis and then back to you after. Like, for each one, like, we should actually make the decision.  
**Speaker 3:** Yeah.  
**Speaker 2:** So that we capture all that as recall. So, like, do you mind just recapping your, like, questions?  
**Speaker 3:** Yeah, I'm just—  
**Speaker 2:** Like, if you were going to, like, talk about anything.  
**Speaker 3:** If we're looking at, like, sites, with, like, okay, there's a various amount of complaints, but if the complaints are more so about the building and not, like, structural, and if we're going to use that to, like, sort of degrade, like, if it's not even structural. Like.  
**Speaker 2:** Yeah.  
**Speaker 4:** Can we filter that out? If it's not related to the core issue?  
**Speaker 3:** I mean, we could, but I'm just saying all 98 were not structural.  
**Speaker 2:** Yeah.  
**Speaker 3:** For the one that collapsed.  
**Speaker 4:** Because those were violations.  
**Speaker 3:** Yeah, they were violations. I'm not seeing the structural part.  
**Speaker 2:** The issue was the site, not the building. The building is fine, the site is what they stuck with.  
**Speaker 3:** Yeah.  
**Speaker 2:** So that does connect to the point about, like, other types of things, like a fire. Like, so maybe we can decide as a group, like, do we want to focus on, like, safety primarily, or do we want to include, like, a few categories? Like, maybe it's life safety, maybe it's, like, it could be accessibility, it could be, like, a couple other areas.  
**Speaker 2:** I mean, there's a lot of potential objections. Like, we could do all of them, or we could sort of decide, like, on a subset.  
**Speaker 3:** What if we did, like, a— like a, like you said, a renter's focus? Like, I feel like if we did, like, a— from the perspective of somebody who lives there with the types of, like, objections. Like, I think the fire safety was something that's good.  
**Speaker 3:** Or even with winter coming, like, heating, stuff like that, that gets reported, that's another thing I think would be good. Maybe something where more people are likely to be reporting on it versus somebody who would have to come in and be, like, an inspector looking for something specific.  
**Speaker 1:** So you want to go where there's more data.  
**Speaker 3:** Like, more data and just, like, you know, like, you know, people are reporting their doors doesn't work, stuff like that. The heat isn't on. Like, stuff like those types of violations instead of saying, okay, the structural, like, the lot, I'm saying.  
**Speaker 2:** Interesting, yeah. I think if there are, like, so many violations and complaints, we should still flag it. We're not saying, like, there is something wrong with the building, but we should still be able to flag it and give it, like, a red flag almost or something.  
**Speaker 2:** Like, so people know. Like, not just, like, ignore it is what I'm saying.  
**Speaker 3:** Yeah.  
**Speaker 4:** I think that changes the objectives slightly from an architect-builder focus to a renter focus too. I think those are two separate problems.  
**Speaker 1:** Oh, what if we—  
**Speaker 3:** My question is just more so about where the data is going to be coming from, structurally-wise.  
**Speaker 2:** Oh, what if we, in the idea of building risk intelligence, we expand the spectrum of, like, it's not about the renter, it's not about the owner, it's not about the owner, it's like a platform that allows you to take feedback from the renters but also takes information from the builders but also takes information from, like, the DOBs. That's like, it's like every day everybody comes to the table. Like, there's existing workflows for buildings which are followed.  
**Speaker 3:** Yeah.  
**Speaker 2:** Those advocacy things where, like, even after the building is done, you create data sets for the people that look into it. Like, maintenance documents. So it's like the same idea of, like, you take the information of the buildings past the construction, and then you open the input of data from the, from the, like, the perceivers, which the.  
**Speaker 2:** I mean, I think it's a question of, like, the user, and I think, like, going, like, more specific will help us rather than going broad. And I think, like, the things that we're talking about affect tenants and people who occupy buildings, but they're not, like, the users, I think, like, unless we want them to be.  
**Speaker 2:** But, like, I think it seems like what the original sort of, like, seed of the idea was, like, to make sure that, like, all parties involved in construction are, like, doing the right thing, essentially. And then that, like, that goes to, like, protecting life.  
**Speaker 2:** So, like, I mean, one approach would be to just focus on, like, if you had a spectrum of severity of issues, like, the sort of, like, upper portion where it's, like, the things that could affect life safety first, like, that's sort of the primary objective. Other things, like, maybe could be flagged, but they're sort of, like, secondary.  
**Speaker 2:** That could be, like, a next step. It's like the core problem that we sort of identified earlier.  
**Speaker 2:** Like, these things happen, like, again, it's not, like, every time it's like a collapse or something. Even if it's like a structural failure, like, people had to evacuate the building, that could have been bad, it wasn't horrible, but, like, those are the sort of types of things that, like, maybe there's enough precedent for us to, like, focus in on.  
**Speaker 2:** And then, like, we could also phase it too, like, in the pitches, like, usually you have, like, the MSI steps. Like, we could sort of say, like, this could be expanded to, like, different users and, like, different types of objectives.  
**Speaker 2:** Like, it might be, like, useful, like, for this. I think they do, like, typically also judge on, like, how, like, tightly it's sort of, like, gotten, like, the broad problem to something that would be, like.  
**Speaker 4:** Specifically solvable.  
**Speaker 2:** Yeah, solve. So, like, that would be my sort of, like, maybe suggestion would be to, like, focus on, like, the next step.  
**Speaker 3:** I agree.  
**Speaker 1:** Yeah, I agree.  
**Speaker 3:** The question is, like, who do we want to focus on for now as a key user?  
**Speaker 4:** Yeah.  
**Speaker 2:** So I was showing everyone the Jobs Blitz, the nonprofit website, and that specifically actually focused towards the tenants and renters that you spoke about before. So I don't think we should do that again, because I feel like it would just be redoing the same thing again. And I do agree with what Jacob said, that we initially started the seed idea with, like, you know, engineers, architects, designers, like, for those people.  
**Speaker 2:** And I honestly think, like, even if it's broad with all these different.  
**Speaker 4:** It's hard.  
**Speaker 2:** It's fine, I think. I don't know.  
**Speaker 3:** I think it's a good idea. I just feel like there's, like, because there's a whole, like, workflow. I feel like there's some key pieces missing that, like, adds to the story.  
**Speaker 3:** And we're missing some data to the next, like, kind of, like, like, like, the drawings, like, the initial plans and the drawings. Like, that would be something very important, but it's like, where can we find that, like, on, like, a large scale?  
**Speaker 2:** I think that's why it's important to integrate the specs with architecture and the queue and integrate it with, like, the build, like, the designers. All that data, when you model it, just the simple metadata of the actions that you take for some point of it, it informs that. So it's like, it goes from, like, you know, when you're building the building or whatever, the concentration, like, foundation, to then that all gets kind of preloaded into the data.  
**Speaker 2:** And I guess that's a point after, I guess, once you— but I guess in that way it only rewards multiple projects, like, throughout time for, like, data. And then that's kind of when it builds.  
**Speaker 4:** Like, the ones where you see this in somebody else's drawing and you're actually looking at it. Too excited.  
**Speaker 2:** So users, like, oh, actually, you had another one before, like, maybe we can do that one.  
**Speaker 3:** I thought you said the— I mean, I said I was down for the— mine was just a renter, like, but the fire violations, like, because I was thinking, okay, violations that are, like, more, like, visual and closer to, like, the people living in the building maybe might be easier to represent on a larger scale. So that's why I brought it up. But I do like the architecture and planner side.  
**Speaker 3:** It's just that I feel that not everyone's plans were clear and as available as the renter's violations, basically.  
**Speaker 2:** So the city of New York has construction-related incidents, like, a full data set for that one.  
**Speaker 2:** But that only has specific categories that they're logging in for that thing.  
**Speaker 4:** And very vague.  
**Speaker 2:** And very vague.  
**Speaker 1:** Yeah, city of New York as well.  
**Speaker 3:** So, like, how vague? Like, what's like the general? I downloaded Excel from that.  
**Speaker 2:** And it only goes back until 2024. So it's a little bad.  
**Speaker 2:** Are we, are we, I guess, we're only using that data to check or agree on a checklist to prevent future cases, right? Like, we're not trying to solve the ones that are separate.  
**Speaker 2:** We're just seeing the pattern.  
**Speaker 4:** I believe so.  
**Speaker 2:** Yeah. And that data is mostly about people's safety, like, people falling down and stuff. It's not about, like, building in any way.  
**Speaker 3:** So that's actually a good one as well, like, worker safety. Like, that's a life safety issue.  
**Speaker 2:** Yep. From the construction, wait, any structure engineering background?  
**Speaker 4:** Yeah.  
**Speaker 2:** From the structure engineering, is there a structure engineering only, like, like, permit workflows?  
**Speaker 4:** Data.  
**Speaker 2:** Like, essentially, is there a place where only structure engineering is required?  
**Speaker 4:** I don't think so.  
**Speaker 2:** So your questions were around, like, the severity. Like, I think it seemed like we're maybe converging on, like, including the catastrophic damage, including the fire, safety, life safety issues, like, geotechnical issues that affect those types of structural. Like, are there any other sort of, like, things in the spectrum of, like, maybe the top, like, four to out of things that would be, like, considered, like, severe?  
**Speaker 4:** I think flooding, maybe.  
**Speaker 2:** Flooding? That's a good one. Yeah, flooding.  
**Speaker 4:** Yeah, because I know I have friends whose apartment got flooded. Maybe it's not that severe, like, but it can be very bad.  
**Speaker 2:** Yeah. No, that's a really good one.  
**Speaker 3:** Flooding is a good— say it again. I think flooding is a good one.  
**Speaker 2:** Yeah, resiliency.  
**Speaker 3:** We can use the elevation of, like, rooms. I think that's a good one.  
**Speaker 2:** Yeah, culture is a good one. And you said, I mean, I think, like, the meeting including extreme weather conditions, like you mentioned, like, in winter and summer, I think would be, like, relevant.  
**Speaker 4:** Is that environmental? Weather and flooding?  
**Speaker 2:** Yeah. Yeah, yeah. Any other ones?  
**Speaker 4:** Maybe soil contamination.  
**Speaker 2:** Oh, yeah.  
**Speaker 4:** I'm not sure if New York City.  
**Speaker 2:** Brownfield, like.  
**Speaker 4:** Brownfield, yeah. If it's not resolved, it can intoxicate the future tenants who live there. And also, I know the, the, there's, do you guys know about the building built on top of the highway in Brooklyn or?  
**Speaker 3:** B3?  
**Speaker 4:** Yeah.  
**Speaker 3:** Yeah, yeah, that's right.  
**Speaker 4:** Yeah, like, the, it's also, like, like, the, the exhaust just go up and then.  
**Speaker 2:** People have higher levels of.  
**Speaker 4:** Yeah. But I think that category is harder to.  
**Speaker 2:** That's a hard one.  
**Speaker 4:** Yeah.  
**Speaker 2:** Proximity to, like, sort of, I don't know if there's a name for that. Detrimental, like, environmental.  
**Speaker 4:** Environmental.  
**Speaker 4:** Question. Are these all just pre-existing in the GIS data that we can't find?  
**Speaker 2:** Yeah.  
**Speaker 4:** Yeah, flooding is from FEMA.  
**Speaker 3:** Wetland.  
**Speaker 4:** There's, like, US GIS.  
**Speaker 3:** Yeah.  
**Speaker 4:** So, so those are more available data that's a little bit easier.  
**Speaker 2:** I think, like, this is great. Like, I think the vision, like, we're sort of focusing on, like, the thing, like, data availability, like, will be a gap no matter what. Like, there will be gaps, but I think, like, I mean, since we're not necessarily, like, saying, like, this is going to be open so that right now, like, we can probably be, like, like, there's, there's, like, a lower risk of, like, data gaps being detrimental.  
**Speaker 2:** Like, later on, I think we can, like, solve that. But it's good to sort of.  
**Speaker 4:** So there's no specific data set for buildings that are flooded, but there is a data set for complaints. I think that you've spoken about that. But the complaints have specific codes assigned to them.  
**Speaker 4:** So, for example, if a building is shaking, that's assigned building code 30. So we could filter specific codes based on what could be associated with building accidents, for example.  
**Speaker 4:** And then that has, like, a decent amount of data to be honest, that we could use for.  
**Speaker 2:** Okay.  
**Speaker 2:** Do we answer all your questions yet or not yet?  
**Speaker 4:** Just, yeah, the, the main, like, identifying the problem is, like, resolved. And, and the data sets, we have, like, spoken about it a little bit. The other question is just narrowing the inputs and outputs we want, like, what.  
**Speaker 2:** That's right. Which I think has to do with the users, right? So, like, in some cases.  
**Speaker 4:** Yeah.  
**Speaker 2:** Okay.  
**Speaker 2:** Cool. Does anyone have any thoughts on any of this?  
**Speaker 2:** Or, like, maybe this is, like, just kind of just narrow down to users.  
**Speaker 4:** We wanted to.  
**Speaker 2:** The primary demo user.  
**Speaker 4:** We wanted to extend it to the whole, like, the way of, like, the, like, the primary architects, contractor developers, and developers, like, startups, I guess.  
**Speaker 2:** Yeah. I mean, it's, like, a question sort of of, like, who, and then, like, who is doing what, right? So, like, architects are engineers, like, certainly filings, like, contractors.  
**Speaker 2:** Are we, like, targeting them before, like, mobilizing them to do, like, later work? Like, adjacent owners or tenants, like, those users?  
**Speaker 2:** Or, like, then there's also the DOB exam and inspectors. So, like, it could be all of those, sort of, drives and outcomes.  
**Speaker 4:** Theoretically, all of them. But it depends on at which point of the development we want our project to kick in and be most effective.  
**Speaker 2:** Yeah. I mean, literally, the suggestion is, like, the project team before excavation. That is the primary objective.  
**Speaker 4:** Project team before excavation, so after CD set. That's pretty late.  
**Speaker 2:** There's a team that would be focusing on the project. There's a team that would be focusing on the building. I mean, it's an open question.  
**Speaker 2:** Like, at what point in time do we, do we, do people need to be able to get information from this to make decisions?  
**Speaker 1:** So I just want to say, um, it's starting to get a little loud. You guys might want to speak up a little louder.  
**Speaker 4:** Oh, okay.  
**Speaker 1:** It might get corrupted loud.  
**Speaker 2:** Okay. Anyway, so that was.  
**Speaker 4:** That's an open question to where we think our product is most effective in the process, right? So let's summarize a couple of points. First is when a developer is looking at a building, the decision to acquire, acquisition stage, before architect, before anybody has signed a contract to work on it.  
**Speaker 4:** Or it could be the early design stage when an architect is signed and maybe, maybe not an engineer is in. Or it can be in the heavily involved design stage where they're, the architect's working together with an engineer and they're actively designing and drafting before they file permit.  
**Speaker 4:** And I don't think this needs to, and then after you file permit, this is kind of, like, redundant, right? We don't need this anymore.  
**Speaker 4:** But you could also have the renter kick in after permit filing.  
**Speaker 2:** Is it different here with the permits? Like, I can't remember if you do, like, a DDS model.  
**Speaker 4:** No, just one. After the 100% CD set.  
**Speaker 2:** Yeah, that's a really good point.  
**Speaker 4:** So, like, pre-purchase, early design, late design stage. I guess three options.  
**Speaker 2:** And then there's also, like, like, when you're going to the site and going to excavate, like, you, like, you have to sort of be still, like, yeah, in certain construction, you have to be sure that, like, everything is sort of right up until that point.  
**Speaker 4:** I see.  
**Speaker 2:** That it carries through.  
**Speaker 1:** From my understanding, like, proactiveness is very important in this space. So my, my immediate thoughts, and again, I'm not, like, an expert on your workflow or your workflow, but my thought is at every stage, interaction with this is helpful. Like, you should do that at every stage.  
**Speaker 1:** But if you're thinking about isolating its usage to a particular stage, what are you trying, what trade-off are you trying to take advantage of?  
**Speaker 4:** I agree every single stage. And I think for the purpose of the MVP, we target one stage for this hackathon.  
**Speaker 1:** Gotcha.  
**Speaker 4:** But I think, ideally, every stage. But the problem is that it has different target audience per stage because.  
**Speaker 2:** Because pre-acquisition is developer and then, and then it changes to architect.  
**Speaker 1:** Right.  
**Speaker 2:** Or what if we thought about, like, integrated project management situations where everybody's involved in.  
**Speaker 4:** Oh, yeah. That's an ideal situation.  
**Speaker 2:** I mean, we could also, like, like, sort of as an MVP, so to speak, like, show all of them to, like, all the phases and, like, where we would intervene at all of them. Like, as, and then, like, we could go deeper on those, of course. But, like, if we, and, and maybe we could even go deeper on one.  
**Speaker 2:** But, like, we do want to show the connectivity, right, and the ability to be proactive at the stages. So, like, I think showing that would be quite, like, impactful.  
**Speaker 4:** I—  
**Speaker 1:** No, I was just saying, I think that's a good way to have that trade-off. Because it seems like you're concerned that it will be hard to do that for an MVP, right?  
**Speaker 4:** But now I'm thinking maybe not that hard.  
**Speaker 1:** But that's why I'm thinking, like, we could, at worst, be relatively shallow in some areas, but deep enough, and then if you want to really show depth in one particular spot, you can do that.  
**Speaker 4:** Yeah. And I'm thinking, let's say, according to the three stages that we just talked about, early pre-development stage, you will have historic floor plan and a location address. Early design stage, you will have schematic design drawing, maybe sketches, like, very preliminary plan.  
**Speaker 4:** And then later design stage, you will have some sort of a CD set. So the input would be different according to the three stages.  
**Speaker 4:** But they can all be floor plans plus address.  
**Speaker 2:** So we say, like, like, is this a new build or, like, you know, renovate, is this, you know, ground up or, like, you know, renovation?  
**Speaker 4:** Or renovation.  
**Speaker 2:** Or, like, and even then, like, type of construction, like, I suppose, if we, if we kind of focus on, like, for example, IPD, like, or IPD.  
**Speaker 4:** IPD.  
**Speaker 2:** And already in, in, like, every, most of the parties are in, in the practice.  
**Speaker 4:** I agree with IPD, assuming IPD as an approach.  
**Speaker 2:** Because I think IPD in general is pretty experimental, so it could be, like, arguing how to bring the DOB into the IPD, like, workflow. And then that connects the whole building.  
**Speaker 4:** Yeah. And we're kind of doing what's bringing DOB into the IPD workflow, just without a DOB person.  
**Speaker 2:** Yeah. Like, maybe, so, like, yeah, bringing it into IPD workflow.  
**Speaker 3:** Address, like, job type, work type, like, construction type also could be part of that.  
**Speaker 4:** What is the full name for IPD again? Interdisciplinary.  
**Speaker 2:** I think it's Integrated Project Delivery.  
**Speaker 4:** Integrated Project Delivery, which is the idea that developers should have an architect, engineer, environmental consultant, everyone at the start, get-go of the project, and everybody has involvement throughout, which doesn't happen in real life. It's recommended by AIA, but it never happens in real life.  
**Speaker 2:** And I think it's, like, newer, right?  
**Speaker 4:** It's new. It's, it's recommended. You're supposed to aim for that.  
**Speaker 2:** I think that was helpful. Also, like, thinking, like, let's say you said for the earliest case where someone is trying to go into acquire a land, won't he already have a checklist? Like, won't he be just repeating the, won't he just mirror his old checklist?  
**Speaker 2:** Like, because when he plans to acquire a land, I think he would have also put some thought into why he's acquiring that land.  
**Speaker 4:** 100%.  
**Speaker 2:** So, so if he put a checklist there, aren't we just mirroring that?  
**Speaker 4:** I don't think we're just giving them a checklist. I think they're inputting the address and whatever preliminary floor plans they have in hand. And then we can give them more intelligent layer based on their special case.  
**Speaker 4:** Because typically, a checklist is just making sure there's no tax overdue, making sure the, to hire something, something, making sure there's report. Like, it's, it's not a visual checklist.  
**Speaker 4:** It's usually a word checklist.  
**Speaker 2:** Gotcha. Okay.  
**Speaker 4:** Yeah.  
**Speaker 2:** Did you guys have anything else?  
**Speaker 3:** Do you think it's great, like, for the product to be more referenced, like, post-build, like, maybe after, like, a building that's been built for 20 years? Like, I know how it makes more sense when it comes to things like checklist evaluation and that nature. But like you said, if something is being written, obviously, because we have our own standards and we're being evaluated by them, but obviously, if we have a second check after another one's already built, like, now we see, is it still up to  
**Speaker 3:** standard?  
**Speaker 4:** And I think that's very applicable for New York City and, like, right now in the world, because, because we overbuilt in the past 50 years. And you're not going to torn everything down. So there's, I think, going to the future, there's going to be a big market on, like, purchasing old buildings and, like, strategically developing old buildings.  
**Speaker 2:** But I think we kind of, it seems like, all agree that, like, this thing as a vision will touch many stages of the project. So I think in some ways, like, we should just build it, like, almost like that, like, kind of addressing each stakeholder's needs and, like, what the sort of, like, required coordination and, like, data is going to be useful at those various stages. Like, we can map that out in the product and then, like, we can see how far we get.  
**Speaker 2:** Like, we'll probably not solve it all, but it seems like we, we need to capture that as, like, the vision of it. Because, like, everyone's involved and there's, like, many stages.  
**Speaker 3:** Which is the problem.  
**Speaker 2:** Yeah. That, that's really, like, the, the sort of underlying needs.  
**Speaker 3:** Yeah.  
**Speaker 2:** Cool. Okay. So do you have some other things from your notes?  
**Speaker 4:** Hold on. I got distracted. Like, question.  
**Speaker 4:** My main question is about input into our software, into our platform. I don't know if it's too early to talk about it, but I want to make sure we're aligned on what we're inputting.  
**Speaker 4:** Address is a given, and floor plans is what we talked about. Is there anything else, or is there any disagreements on this input and output?  
**Speaker 2:** I think it, it might not be like a single party or, like, like, when you say address, like, that's like the initial input? Because I, I feel like the input comes from all the different parties that are using it consistently. Like, like, it's not only the address, but, like, for example, the architects and the engineers are involved.  
**Speaker 2:** Like, some of their, some information modeling is part of it and also the input that it's not even, it's like automatic in a way that it doesn't, like, you don't have to actually type or submit anything. It just kind of reads the native thing that.  
**Speaker 4:** Could you clarify what the.  
**Speaker 2:** Like, like, like, when you say input, like, are we just putting the address and then it spits out the report? Or is it like, is the input, is the input a one-time thing or is the input like a, like a back-and-forth thing between different stages or different.  
**Speaker 4:** That's what, that's my question to the table.  
**Speaker 3:** Is it coming from their information? Like, you know, it's not just like the same visual examiner or the type of thing that's being done, stuff like that.  
**Speaker 3:** Would that be included under the.  
**Speaker 2:** Are we, are we still capturing her over there?  
**Speaker 1:** We are.  
**Speaker 4:** Okay. Let's just all talk louder. That's my question.  
**Speaker 3:** Could, like, um, sort of like a, a connector to, like, what we have already, like, one of the DOB websites. Like, you can put the address, we can get all that information. So that's something we don't have to worry too much about.  
**Speaker 3:** The address can be enough. We can automate that.  
**Speaker 4:** Yeah. That's my question. So you're suggesting once we have the address, we don't need to input.  
**Speaker 3:** What do you use, basically?  
**Speaker 2:** Like, what do we need to, like, are we thinking about, like, for example, are we thinking about new projects or existing projects that, like.  
**Speaker 3:** New developments.  
**Speaker 4:** Right now we're thinking about existing buildings. So it could be whatever.  
**Speaker 3:** Within new, yeah, within new construction.  
**Speaker 2:** I think I would also be good for the new.  
**Speaker 3:** I think it could be that combination. So, like, what are you guys talking about?  
**Speaker 2:** Depends on the.  
**Speaker 1:** Yeah. I just agree with the idea of, like, address is not like a real input, but we use the address to fetch all the other inputs we want, such as the, yeah, yeah, such as the zoning, like the flood, like classification.  
**Speaker 4:** Oh, maybe I didn't clarify my question. Sorry. By input, I mean, what does the user need to input?  
**Speaker 4:** Not ours.  
**Speaker 2:** Yeah.  
**Speaker 4:** Address is usually needed.  
**Speaker 2:** Yeah.  
**Speaker 1:** So yeah, sure.  
**Speaker 4:** Yeah. But then later on in the design stage, they will have floor plans and they can upload, like, a design package.  
**Speaker 2:** Exactly.  
**Speaker 4:** So is that the only input we require from the user?  
**Speaker 2:** But just to put it, like, put it into the solution. So I think I, I have a sense of it. Like, from, so there's, so we, where you're, we stepped away.  
**Speaker 2:** We sort of agreed, like, this problem spans multiple stakeholders and, like, multiple phases of the project. So we're sort of going to, like, design it to address those needs.  
**Speaker 2:** Um, and then, like, so the question about inputs, I think it'll be based on, there's, like, some high-level inputs of, like, if, so what's the goal, right? Like, it's to, if you're a practitioner and you're trying to understand, like, at various stages of the project, like, based on the given site and, like, design and things like that.  
**Speaker 2:** Are going to be the, like, risks, right, to mitigate and, like, the potential, like, hazard or issues based on, like, past, like, lessons. So, like, you, you are, like, putting in your address because that's where you're designing.  
**Speaker 2:** I think, like, the job type, like, I have sort of, like, is it new construction, is it an alteration, a demo? Like, these are all things that, like, will pull in useful information from past projects.  
**Speaker 2:** And, like, the work types, right, like excavation, foundation, SOE, structural, facade, sprinkler, like, like, all those things touch, like, the relevant, like, codes, previous, like, data that, that we'll be able to pull in. And then, like, that might be earlier on.  
**Speaker 2:** And then, like, later on, like, when you have, like, preliminary floor plans, like, you might put that in and then there might be some other issues that you have.  
**Speaker 1:** I, I think all of those things are important to be, like, ingested into this. All of them are being considered, like, at every stage that they come up, essentially. So you, we need to be able to look at plans, um, look at, you know, previous job data, uh, and, and natural language as well.  
**Speaker 1:** Like, someone just can speak and tell the, or the agent or the front-facing, uh, model what they need, what they don't know, what they want to know, and they can formulate from there. I think that's an important way to approach it.  
**Speaker 2:** And maybe, like, there would be even a big model, like, you know, for, like, later down the line.  
**Speaker 3:** Because, like, markets and energy.  
**Speaker 2:** Yeah.  
**Speaker 3:** Because, like, if you're going to be doing, like, some sort of, like, you may or may not, like, depending on the building and the type of construction, like, you may not have a model. Like, you may just have, like, in.  
**Speaker 1:** Just a CAD sometimes.  
**Speaker 2:** There's also as-built, like, and scan-built.  
**Speaker 3:** There's as-built. So it, it really depends on, like, there's some of those, like, initial inputs that then tell you as a user what you, like, additional information you have. But it, it kind of all relates to, like, what are you trying to accomplish at any given time.  
**Speaker 3:** And it's like you're trying to just list all the risks and the compliance and, like, all those things. And so it's like, you're not going to have the same inputs, like, at any given point, but you still need kind of high-level stuff, like, yeah, address, job type.  
**Speaker 2:** Like, the creative, like, creating the project input, right? Like, the first, the starting thing that.  
**Speaker 3:** If anything that, like, is just baseline, what will tell you, like, hey, um, okay, so let's say, like, the Brooklyn project, right? If I'm doing a very similar project, I want to know, like, how to not have that happen. So I'm putting in my address, job type, like, all of these, like, whatever we need as, like, the stakeholders to, like, basically say, like, I'm giving you the information about the project, like, starting off, and then I need to know whether my new address or project will have,  
**Speaker 3:** like, is there going to be an issue with, like, the, the, the party wall? Like, is the party wall going to be, like, if there's going to be excavation, like, what do I need to do?  
**Speaker 4:** Yeah.  
**Speaker 2:** That's a good point. That's a good point. Like, the services based on, like, it's not analyzing existing buildings.  
**Speaker 2:** It's analyzing the adjacency of the new build and maybe the likelihood of, like, like, a, like, a store.  
**Speaker 3:** Giving you all historical data of buildings in the profile that, that we sort of decided on with, like, um, like, issues that have come up from, like, medium severity to high severity, pulling all of that in from past projects and then telling you for your new projects, which could be new construction, it could be renovation or something else, like, what you need to consider, right, based on that historical information.  
**Speaker 2:** And the, the little side of the debate, like, we're talking about renters, renters having feedback loop where they can assign, like, the, uh, like, the complaints. That only happens when you complete the building, right? Like, I guess those complaints would only happen so then your building would have the availability of upcoming, like, so, so then when this building is done, this building speaks back to that dataset.  
**Speaker 2:** Like, we make sure that our building creates that dataset.  
**Speaker 3:** Yeah.  
**Speaker 4:** Yeah, like, for, for renters.  
**Speaker 2:** Yeah, because, like, for example, like, what kind of renter, like, if this is an entity state, like, renters. Renter, like, it might help for the next for, like, getting the data, the data from the next building, like, or creating the.  
**Speaker 3:** I mean, is there, like, a, is there a, like, a use case where, like, renters would be helping in, like, life-safety issues?  
**Speaker 4:** Yes. I think so. In the news article for the Brooklyn one, the renters have reported feeling mild shaking in the leading months.  
**Speaker 2:** Oh, like, real-time?  
**Speaker 4:** During the construction of the neighboring site. But they didn't report it anywhere because there's no, there's no platform to report it.  
**Speaker 2:** Would you have to ask the developer.  
**Speaker 3:** There is.  
**Speaker 2:** They could have filed a complaint and then it would have been a, like, pretty much out of control.  
**Speaker 4:** Maybe it wasn't strong enough. I didn't read into it, but it was just like a news article that said the renters have experienced shaking.  
**Speaker 2:** Do you think as a, like, let's say Villamir Road, the Piñuelo Tower, like, as a developer, would you want to give your tenants a portal to tell you that and, like, document that and, like, make that, like, a dataset? Like, as, as a developer, right?  
**Speaker 4:** As an established developer, typically apartments have that. My current apartment has an internal portal. But that building was 100 years old, owned by an individual that only has four apartments.  
**Speaker 4:** So no. They.  
**Speaker 2:** I guess a good question. Would those type of owners adopt this product? Like, is this a product for, like, some of the, the, the big companies, like the Genser, like, the, like, uh, like the Genser, the KPS, the Ascent, or is it, like, every?  
**Speaker 4:** It's for the owner of the building because architects are being.  
**Speaker 2:** But I'm wondering about what that, what that owner would ever actually purchase it, right?  
**Speaker 2:** Oh, is it, oh, oh, you're not a service? Or, like, who's the owner of the building?  
**Speaker 1:** I mean, this could be a long shot, but I'm, you know, I'm, I haven't lived in the city that long, but regardless of who, uh, is in charge of the building, uh, 311, I believe, usually gets contacted if there's issues that could be like that.  
**Speaker 4:** Yeah. You can.  
**Speaker 1:** Do you think it'd be possible to leverage any data they might possibly have?  
**Speaker 4:** Oh, I don't know.  
**Speaker 2:** Do you think the data is coming from 311 calls?  
**Speaker 1:** Yeah.  
**Speaker 2:** That's how it is.  
**Speaker 1:** Ah.  
**Speaker 2:** Because that's what's logging everything.  
**Speaker 1:** That you saw something like that?  
**Speaker 2:** I think I, I remember reading it somewhere, but.  
**Speaker 1:** Got you. Okay.  
**Speaker 3:** What do you guys think over there? Like, is this rental piece, like, should it be in scope because it has, like, a relationship to potential life-safety, like, mitigation, or should it be out of scope? Like, what's, what's your take?  
**Speaker 1:** I think, I think we should take it carefully, right? If it's just a complaint that has nothing to do with, like, architectural structural problem, or if it's a complaint, um, like, even, even the engineer and architect follow the standard of care, like, do everything great, there could be issues that's unpreventable even by close collaboration, such as, like, some tenants will complain about the concrete cracking. But cracking could be mitigated by concrete is a material that's not, like, as regular as steel.  
**Speaker 1:** So sometimes it's not preventable. So I, I think if we are going to take the renters' complaint, we need to parse out the noise and just focus on the ones that has real, like, safety, like, implications, such as fire, like, structural collapse or, like, chemicals.  
**Speaker 3:** I mean, I, yeah, I wonder, wonder, like, if this, I mean, is there a way to do that? And, like.  
**Speaker 1:** Yeah, there's.  
**Speaker 3:** Does this become then where, like, you move 311 and, like, you're, like, not doing renters?  
**Speaker 1:** Um, yeah.  
**Speaker 3:** I mean, it, it feels like it's sort of maybe challenging, like, in a way of, like, how would you actually, like, how would that be? Because it's sort of, like, it's data points, perhaps, but, like, I mean, in some ways, maybe it's, like, some of the other ones are also unrealized. I don't know.  
**Speaker 4:** Is there, like, standards that exist in, like, for there to be a complaint to be made? Like, is that, like, standard versus, you know, like, no renters, you can complain about anything, but, like, say from a structural point, like, okay, this building is leaning three inches. That's out of the acceptable range.  
**Speaker 4:** So this, you know, now you can put a complaint about this. Like, is there, like, some standards that exist to, like, normalize it?  
**Speaker 1:** Uh, I mean, if it's a building, so leaning is definitely a very big red flag.  
**Speaker 4:** How do you know? Like, how bad do we know it is? Like, on an objective scale to be able to compare it to other buildings that also lean?  
**Speaker 4:** Maybe for one building, the same type of leaning is, like, less detrimental.  
**Speaker 2:** So the, I found this, I don't know what it's, like, exactly what it is, but I complied by address and there's a code and it's called disposition. And I'm, and I think it's, like, it's, it's a, it's a legend, like, but then there's one particular file for you that's, like, red. And it's, it's essentially, like, it's red and it says the building is leaning.  
**Speaker 2:** So, like, L3 might be the code that we can use for structural, like, like, red. Like, it's literally red.  
**Speaker 4:** Just the building is leaning?  
**Speaker 2:** It's, like, it says there's a mixed-use property and the building is leaning towards northeast.  
**Speaker 4:** I guess, it might actually ask some questions, like, what do we qualify as a lean?  
**Speaker 1:** Oh, there's a criteria. We call it, we, so we the amount of leaning and divide by the height of the building.  
**Speaker 4:** Okay.  
**Speaker 1:** That's something quantifiable. But, but, yeah, I, I don't have a specific number in my mind of how much leaning is too much leaning.  
**Speaker 4:** As long as it exists.  
**Speaker 2:** So I checked on the 311 calls, by the way. Uh, that's how most of the DOB complaints actually start. So, yeah.  
**Speaker 2:** So that's New York City's phone number for non-emergency problems. Uh, so basically, if the neighbor sees a crash, they call 311, 311's number for the DOB, and that becomes a DOB problem.  
**Speaker 2:** There's a separate dataset for that also.  
**Speaker 3:** Is that public access?  
**Speaker 2:** It is, yeah. It's plain English descriptions, by the way.  
**Speaker 3:** I mean, honestly, like, why don't we just pull that stuff in and, like, because if, like, we could, we could technically solve, like, if, if we have a checklist, right, and, like, let's say there's, like, geotechnical reports or the structural, like, you know, submissions, things like that, if they're already, like, like, flagging, like, oh, these are some potential issues, plus we have, like, a tenant complaining about, like, the building shaking, then that's, like, ding, ding, ding, like, like, let's stop work. It could be an additional data  
**Speaker 3:** point, whether we can solve it, like, we could figure that out later. But it seems like in this case, like, clearly there was people who actually experienced something, but they had no way of communicating it. So that's, that's pretty bad.  
**Speaker 2:** The 311 data set is actually really good because the reports are, like, building is shaking, vibrating, structural instability, debris is falling, adjacent buildings are not protected. Like, that all fits within.  
**Speaker 3:** Yeah, yeah, yeah.  
**Speaker 1:** Yeah, this is very structure-related, yes.  
**Speaker 3:** I think that's it.  
**Speaker 2:** There's a, there's a complaint code, like, code, and it's, and it's categorized, and some of them are specifically for, like, stop or quarters or different, like, violations and stuff. So maybe parsing those specific codes.  
**Speaker 3:** Say that one again?  
**Speaker 2:** So, like, there's a thing called, like, uh.  
**Speaker 3:** Just check this.  
**Speaker 2:** So from the just, what is it called? Just, uh.  
**Speaker 3:** Just NYC?  
**Speaker 2:** Like, the one that you were talking about, uh, JustFix.  
**Speaker 1:** Yeah.  
**Speaker 2:** They have a DOB building profile, and within that building profile, they have, like, a NYC department complaint by address. And so they have all of those addresses, but then there's dispositions, which are, like, categorizing those, those, like, what those mean. And so some of them are, like, violation focus or stop order focus.  
**Speaker 2:** So, like.  
**Speaker 3:** Okay.  
**Speaker 2:** Parsing that database through these codes might give us, like.  
**Speaker 3:** That's interesting.  
**Speaker 2:** Like, everyone.  
**Speaker 3:** I'll put the codes that in there. Cool. All right.  
**Speaker 3:** Um, so I think we can do, you, we missed you, Steve. Do you want to do your questions and thoughts?  
**Speaker 3:** No? Why don't we, let's try to wrap up the full group at, like, by 3:30 this week.  
**Speaker 3:** We could, like, sync this up this last session, uh, and then we can get down to it.  
**Speaker 1:** Um, yeah, I think everybody raised good points. Um, my only, uh, thing, have we covered, uh, the general structure of how this will be delivered to people? Because I, I've had, I have, like, a prerequisite that I think might be useful that I want to show you guys.  
**Speaker 1:** Um, but that could come next.  
**Speaker 3:** What's the prerequisite?  
**Speaker 1:** Like, um, like, this is a kind of a. Let me see if the demo's still up. But, uh, it's, it's based on something I've worked on before, but someone would come in and they would type in an address they're concerned about, or they'd have a query.  
**Speaker 1:** You would, you could, like, or you could click on a.  
**Speaker 3:** That's if you want to clock talking for the day for this thing.  
**Speaker 2:** Preflight, wait, did you already do this? My  
**Speaker 3:** friend came up with Preflight name too.  
**Speaker 1:** Mine also came up with Preflight. Yeah, that's crazy.  
**Speaker 4:** I screenshot it up. It says this name was mentioned in our conversation.  
**Speaker 3:** Oh, really?  
**Speaker 4:** I asked you that.  
**Speaker 3:** So I think that's.  
**Speaker 4:** You didn't mention it? Okay.  
**Speaker 3:** Yeah, I was wondering what the Preflight is, though.  
**Speaker 4:** Yeah, I saw it.  
**Speaker 3:** Why did you note this?  
**Speaker 1:** Yeah, so this, this is, uh, like, a, a simpler version of something I've been working on. And, uh, it fits the format of this. You search an address, you can look at it.  
**Speaker 1:** Ideally, you would be able to click on a building and it could maybe pull up.  
**Speaker 3:** Give you the.  
**Speaker 1:** Yeah, like, more details on what's going on in it. It could integrate with, uh, some other, uh, tools that are specific to that area. And then you can ask, okay, what is going on with this building?  
**Speaker 1:** And you can search through different, like, complaints and.  
**Speaker 3:** Okay.  
**Speaker 1:** Don't tell anyone you've done this.  
**Speaker 4:** This isn't even a product.  
**Speaker 1:** This is pretty, like.  
**Speaker 3:** It's awesome.  
**Speaker 1:** Good. Yeah, yeah.  
**Speaker 3:** So what, uh, yeah, like, what, what is sort of, like, in here that, um, we would want to, like, just learn from, you think?  
**Speaker 1:** Um, well, yeah, this, this is just the, uh.  
**Speaker 2:** I mean, this is, like, the.  
**Speaker 4:** This is a checklist.  
**Speaker 2:** Like, you just, you can just build on this one.  
**Speaker 4:** Yeah, I was saying you could build on it.  
**Speaker 1:** But.  
**Speaker 4:** It's up to you.  
**Speaker 3:** Is this open source?  
**Speaker 1:** Um, no, this, this is not what, this is similar, but it's not that.  
**Speaker 2:** If it's not open source, we cannot use it, right? Like.  
**Speaker 1:** Like.  
**Speaker 3:** Probably not.  
**Speaker 2:** But we can just do something similar and on the.  
**Speaker 3:** Yeah, no, this is great to see.  
**Speaker 2:** Replicate what we have.  
**Speaker 3:** This is awesome.  
**Speaker 2:** Did you do this?  
**Speaker 1:** Yeah, I mean, well, yeah. This, this is, this is what I did. Like, I, I, I made sure not to take what I did before and just put it in here.  
**Speaker 3:** Yeah, yeah, yeah.  
**Speaker 1:** But once you do something like this before, it's easy to just kind of.  
**Speaker 2:** Mm.  
**Speaker 1:** Make another version of it.  
**Speaker 3:** Wait, so this, I'm sorry, I misunderstood. Is this previous work or what you just did?  
**Speaker 1:** I just did this.  
**Speaker 3:** Oh.  
**Speaker 1:** Just as we were speaking.  
**Speaker 3:** So based on your experience, like, and our, like, transcript.  
**Speaker 1:** Oh, doing something like that.  
**Speaker 3:** Like, you just.  
**Speaker 1:** Based on your transcript. Right.  
**Speaker 3:** Oh, oh.  
**Speaker 4:** Oh, and the transcript?  
**Speaker 1:** Yeah.  
**Speaker 4:** Come on.  
**Speaker 3:** So it acts mind-blowing.  
**Speaker 4:** That's why, that's why it looks, yeah, it looks cool, man. Like, there's a, um, okay, let me see what she did later.  
**Speaker 3:** Yeah, commit this to the.  
**Speaker 1:** Backups.  
**Speaker 3:** Yeah.  
**Speaker 4:** Who uses latest transcripts?  
**Speaker 2:** I thought you came before the hackathon with.  
**Speaker 3:** That's what I thought.  
**Speaker 1:** No, no, no. I didn't.  
**Speaker 3:** Is this visible?  
**Speaker 1:** I, I don't want to be doing that.  
**Speaker 2:** No, no, no. So this is good, good.  
**Speaker 4:** This is crazy.  
**Speaker 1:** Yeah.  
**Speaker 3:** Nice. Um, okay, cool. So from here, like, all right, so what is it showing?  
**Speaker 3:** Like, yeah, what.  
**Speaker 1:** Yeah. Like, what is the site showing and, like, what does the information could you, like, explain that? But a general idea, because this is, this, this is not a real, like, uh, fully functioning thing.  
**Speaker 3:** Yeah.  
**Speaker 1:** But basically, the idea is, depending on how you want to approach it, if you want to search up a site or a lot that you're, uh, wanting to do work on, you can look at it, you can click on it, and it'll, you can ask a front-facing agent details about that lot. Like, what do I, depending on what you ask, it'll pull up relevant information. So it'll know which database to answer your query.  
**Speaker 4:** Okay.  
**Speaker 1:** Um, and then, I mean, I have never even made this yet. I was honestly hoping maybe somebody here could do this, but I would also want something where you can click on the actual building on the map and look at, uh, details that maybe you uploaded for it as you've gotten further along in the project. You can ask further questions, assess, um, how the building is laid out and what issues there could be from there.  
**Speaker 1:** Um, so it's supposed to be, like, kind of like a, an interface that allows you to approach, um, potential issues and, and debug in a lot of different ways.  
**Speaker 3:** Nice.  
**Speaker 4:** Like the map view component.  
**Speaker 3:** Yeah, map, map is great.  
**Speaker 1:** Can you change the address? Try some other address? Or maybe it's, like, hard-coded.  
**Speaker 1:** This, some of this might be hard-coded, but, uh.  
**Speaker 3:** Okay, fine.  
**Speaker 1:** So these probably.  
**Speaker 4:** You can pull that.  
**Speaker 3:** Yeah.  
**Speaker 1:** But you can scale pretty quickly.  
**Speaker 3:** Nice, nice, nice, nice.  
**Speaker 2:** But this is only for existing ones, right? This is not for, like, new buildings. This is only for existing ones.  
**Speaker 1:** It's for, it's for existing buildings, but I, I would like to be able to, because if a building doesn't exist, you would want to, um, look at a lot, right?  
**Speaker 3:** Yeah.  
**Speaker 4:** Yeah, most of, there's not a lot of lots. Most of the new construction was buying existing buildings.  
**Speaker 3:** Yeah.  
**Speaker 4:** And they do new ones.  
**Speaker 3:** Yeah.  
**Speaker 4:** So it's like, new lots almost don't exist anymore.  
**Speaker 3:** Yeah. Nice. All right.  
**Speaker 3:** So we have, like, good, good start. Um, let's keep going around.  
**Speaker 3:** Um, or did you have any other questions?  
**Speaker 1:** No, I just wanted to see if this, uh, interface made sense to, to you guys, especially you and.  
**Speaker 4:** Like, generally, like.  
**Speaker 3:** See, zoom out and then zoom in.  
**Speaker 2:** So now if you put this on the GitHub and if we are all cloning, I'm guessing you're cloning.  
**Speaker 3:** Yeah.  
**Speaker 2:** If we redo the next prompt, now it'll have the context of this thing also that you're building. So.  
**Speaker 4:** Yeah, I'll take the transcript and this code so far.  
**Speaker 3:** For sure. I mean, this one you could do a branch or you could push to the, either way.  
**Speaker 1:** I believe it's up there already. You can, like, if you hook up your models, it can look at it and.  
**Speaker 4:** You can push already? Okay.  
**Speaker 3:** It's in the repo?  
**Speaker 1:** I believe, I believe it's already in there.  
**Speaker 3:** All right.  
**Speaker 4:** This is so powerful. I'm so amazed at technology.  
**Speaker 3:** I know.  
**Speaker 4:** Now I see why we're fighting for your code.  
**Speaker 3:** No, my job.  
**Speaker 4:** That's why.  
**Speaker 3:** It's my job.  
**Speaker 2:** Camila, and then, and then.  
**Speaker 1:** That's what they are.  
**Speaker 4:** I mean, it's expensive to have that.  
**Speaker 3:** All right, cool.  
**Speaker 4:** I know.  
**Speaker 3:** Cheaper slightly.  
**Speaker 4:** Yeah.  
**Speaker 3:** We've covered the user, the scope.  
**Speaker 4:** We covered the in the core.  
**Speaker 3:** The core claim. Okay, so here's a question. So the core claim of the framing of the collapse, um, so I think just, like, agreeing on the framing, like, we just are going to present, like, what's public knowledge.  
**Speaker 4:** Yeah.  
**Speaker 3:** And then if things are, like, under investigation, like, we're saying, like, that's under investigation. Um, and, like, no, no blame, like, no, like, not saying, like, this would have prevented that or this, like, just for the sensitivity of, like, the project. Like, that's sort of from the framing perspective.  
**Speaker 4:** I think so.  
**Speaker 3:** Um, so we're sort of talking about, like, whatever information is available, like, we're sort of just presenting it in a neutral way, um, for public information. Does that make sense?  
**Speaker 1:** Yeah.  
**Speaker 4:** I think we can start from there.  
**Speaker 3:** Yeah. Um, so, yeah, the differentiation, I think that'll come more later, but just, like, yeah, the, how we differentiate from other existing solutions. Um, I think it's, yeah, like, kind of, like, we have a coordinated checklist.  
**Speaker 3:** We're combining a lot of these different aspects that haven't been combined before in terms of the datasets. And then, like, the precedent library of, like, previous examples, I think that definitely sets us apart.  
**Speaker 3:** Um, what else? Okay.  
**Speaker 3:** Um, oh, yeah, so the checklist, is it, like, sort of mostly rule-based from, like, on, like, your experience? Like, I think you're, like, the expert on this stuff.  
**Speaker 3:** Like, so I think, like, you're, like, the question is sort of, like, are most of the sort of checklist items rule-based, or, like, do you have some LLM-generated or a hybrid? And then, like, do you have the final say, like, kind of on that?  
**Speaker 3:** Because I think you sort of have that expertise.  
**Speaker 2:** What do you mean by rule-based? Because it's, when the building. Fairly reasonably, it's very complex.  
**Speaker 2:** It's a combination of complex things.  
**Speaker 3:** Okay.  
**Speaker 2:** So it's not, like, just one, one rule. They didn't follow this rule and then it failed.  
**Speaker 3:** Okay.  
**Speaker 2:** So, so yeah, I think it could be more than that.  
**Speaker 3:** So, like, hybrid?  
**Speaker 2:** Yeah.  
**Speaker 3:** Between, like, what we get from the code and, like, the documents and the data, plus, like, LLM, like, interpretation?  
**Speaker 2:** Yeah.  
**Speaker 3:** Plus your, like, kind of, you know, sort of, like, expertise?  
**Speaker 2:** Yeah. On, on the structural geotechnical perspective, yes.  
**Speaker 3:** Yeah.  
**Speaker 2:** Like, um, other, like, chemical plotting is, like, anyone can do.  
**Speaker 3:** Okay. Um, all right. Yeah, sure.  
**Speaker 3:** I mean, that sounds good. Um, so maps, like, I think, yeah, like, 2.5D seemed to be, like, probably a good approach rather than doing, like, full 3D.  
**Speaker 3:** Like, I think kind of, like, sort of what we were seeing there.  
**Speaker 2:** Okay.  
**Speaker 3:** Does that make sense?  
**Speaker 2:** You could do the 3D from Revit, like, from the.  
**Speaker 4:** From the structure.  
**Speaker 2:** Architectures, like.  
**Speaker 3:** Yeah. I'm sorry, I'm just talking about the map, like, the sort of map view, like, having it be, like, sort of somewhat three-dimensional and not, like, super, super, like, busy detail.  
**Speaker 2:** Do we collaborate with Citywatch on this one or not?  
**Speaker 3:** Uh, maybe, yeah. They're an API.  
**Speaker 2:** Do they have an API?  
**Speaker 3:** Um, yeah. I mean, we could use, like, MapLibre. Also, like, I mean, if they have something, we could.  
**Speaker 2:** Well, this thing looks like in the general category. Sometimes it's nice to, like, have.  
**Speaker 3:** Yeah. We should, we should check with them. We should check with them.  
**Speaker 4:** We're so close.  
**Speaker 3:** Yeah.  
**Speaker 2:** Where's the show?  
**Speaker 3:** Um, so do we show, let's see, do we show any, like, permit holders or contractors' records?  
**Speaker 3:** Like, some of that might be useful, but, like, it could also name companies. So, like, I'm not sure if we need that.  
**Speaker 4:** Sorry, I don't understand.  
**Speaker 3:** So, like, like, we're talking about, like, the permits and, like, the records from contractors, like, as data source, right?  
**Speaker 4:** Oh, as past jobs.  
**Speaker 3:** Yeah, past information. Like, what, like, that might have, like, you know, PII in it. So.  
**Speaker 2:** Yeah, I don't think that's fully necessary.  
**Speaker 4:** Yeah.  
**Speaker 2:** As far as, like, making sure that people, different parties coordinate to make sure the building doesn't collapse. We're not, like, putting a blame game on who are the parties who caused.  
**Speaker 3:** Yeah, that's right.  
**Speaker 4:** I think a lot of these are good additions that we can mention as, like, future features.  
**Speaker 3:** That's not, like, necessary.  
**Speaker 4:** Like, renters' complaints, like these ones.  
**Speaker 3:** Yeah, got it.  
**Speaker 4:** VIP premium feature.  
**Speaker 3:** Yeah. And then I think that's pretty much it. Like, the stack would be pretty straightforward, like, next to the first level.  
**Speaker 3:** Um, I guess the only other one was, like, the demo, like, sort of, um, like addresses.  
**Speaker 3:** Like, there's several projects that we could show as, like, examples. Like, the Brooklyn one.  
**Speaker 3:** Uh, I mean, we don't have to decide right now, but, like, there's, like, 34th Street, there's a Central Park. Like, we could maybe at some point later go through the list and decide which ones we want to talk about.  
**Speaker 4:** Yeah.  
**Speaker 2:** That sounds like good options.  
**Speaker 3:** Yeah.  
**Speaker 4:** Yeah.  
**Speaker 3:** Yeah, from, from previous examples. Like, you know, like, Liberty Ave in Queens, the Jason Wall Collapse during underpinning. Uh, like, there's some good, like, precedent examples.  
**Speaker 4:** I think from a ruthless marketing perspective, the Brooklyn one would catch most people's residence if you present it.  
**Speaker 3:** Yeah.  
**Speaker 4:** Which will be cruel.  
**Speaker 3:** Well, yeah.  
**Speaker 4:** But most people would resonate strongly.  
**Speaker 3:** I mean, this isn't about, like, marketing. It's just, like, we're trying to solve this problem.  
**Speaker 4:** Yeah.  
**Speaker 3:** Like, it's like a.  
**Speaker 4:** Yeah, yeah, yeah.  
**Speaker 3:** It's like.  
**Speaker 4:** Yeah, yeah. We're comfortable we can start with that, but we can discuss later. Because it also has a lot of recent news articles.  
**Speaker 3:** Yeah. I mean, you pitched that and, like, that sort of hit, you know, stretch of course.  
**Speaker 4:** Yeah, because everybody thought about it very recently.  
**Speaker 2:** It's very fresh, yeah.  
**Speaker 4:** Yeah, it's so fresh.  
**Speaker 3:** Okay. All right, cool. Let's, let's keep going.  
**Speaker 3:** Anything else?  
**Speaker 2:** I think I've kind of, like, sprinkled my thoughts throughout this conversation, to be honest.  
**Speaker 4:** That looks so good. The, the notes.  
**Speaker 2:** Oh, the. But I did have one question. So the, uh, what we're showing basically is going to be our site's history, but also our neighbor's history at the same time.  
**Speaker 4:** Relevant history.  
**Speaker 2:** Relevant history.  
**Speaker 4:** If the neighbor is two miles away, the nearest neighbor, then maybe not necessary.  
**Speaker 2:** And that history is going to be the violations themselves?  
**Speaker 4:** Mm-hmm.  
**Speaker 2:** Okay.  
**Speaker 4:** I think so.  
**Speaker 2:** Okay.  
**Speaker 3:** I mean, if an adjacent building is, like, right, like, if there's construction or if there's, like, history of, and again, like, we talked about, like, flooding or other things that could be interesting, like, sort of to flag early. Soil conditions, contamination, like, it, it starts to become, I imagine, right, like, a contextual map of, like, even a neighborhood where, like, these things can be surfaced. Um, starting with, like, adjacent buildings.  
**Speaker 2:** Could we show something like, like, this is a project that has a specific failure? We can show, like, other parts, New York City, failures that kind of, like, match.  
**Speaker 3:** Exactly.  
**Speaker 2:** The project that's, okay, okay. So we can show something like that.  
**Speaker 4:** Yeah, similar types of risks.  
**Speaker 2:** Yeah, yeah, yeah.  
**Speaker 3:** And, like, you could see that on a map too. Like, that's kind of, like, the nice part about it, right?  
**Speaker 4:** Yeah.  
**Speaker 3:** You click on a site and then you get the history and you get, like, the patterns across the city of, like, similarities. And that's where, like.  
**Speaker 4:** Sorry, yeah. The pure proximity to those activities.  
**Speaker 3:** Exactly.  
**Speaker 2:** Yeah, okay. Just a little quick. Just for, can you say, can you all say your names so it identifies the voice?  
**Speaker 3:** Jacob, what's up?  
**Speaker 2:** I'm Shandon.  
**Speaker 4:** Ethny.  
**Speaker 1:** Jhuil.  
**Speaker 2:** Liz.  
**Speaker 1:** Hershey.  
**Speaker 2:** All right, whisper. We just said our names again, so figure it out. Also, um, are we going to have a checklist for each of the stakeholders?  
**Speaker 2:** Like, like a submission checklist. Like, structural, geotech, contractor.  
**Speaker 1:** But, like, I don't think everybody will submit structural stuff. Like, I think every party.  
**Speaker 2:** No, like, how it affects, like, each person in the description.  
**Speaker 3:** Yeah.  
**Speaker 2:** They're going to have, like.  
**Speaker 3:** Checklist for each stakeholder.  
**Speaker 2:** Something like that?  
**Speaker 4:** Is this about.  
**Speaker 1:** But, like, it's about what structural checklist can develop.  
**Speaker 2:** How would you impact that person?  
**Speaker 4:** I think this is a question about output. And the, whatever output we have, whether it's a report or a web-based result, it can be divided into different sections. So it could be, like, structurally focused issues, environmentally focused issues.  
**Speaker 4:** Is that what you're asking?  
**Speaker 2:** Yeah. Are we separating data like that in any way? Or that's, I'm just going.  
**Speaker 3:** Yeah, discipline. I mean.  
**Speaker 1:** I think for digestion, maybe, like, just, like, if you're, like, if you're a user, if you're into ruthless, you're, like, literally.  
**Speaker 2:** It just makes it easier for, like, the specific user to, like, skim through the data without having to go through a whole language check.  
**Speaker 3:** Yeah, makes sense.  
**Speaker 2:** Anyways, that's fine.  
**Speaker 3:** That makes a lot of sense. Yeah. UX, UX, like, surface the information for the right person at the right time.  
**Speaker 2:** Yeah, more information can be applicable to different parties because, in the end, it's according to the market.  
**Speaker 3:** Yeah. Anything is, like, if you're on the teams, you get, like, access, right? But then, like, you can filter down and drill down to, like, the relevant assistant.  
**Speaker 3:** And you're actionable. Like, I think, like, it should tell you, like, what to do or, like, suggest what to do, right?  
**Speaker 3:** Like, as, like, if there's, like, an emergency thing, like, this is what you should act on. This is, like, a real big issue.  
**Speaker 3:** Like, the underpinning stuff is, like, this. So it should, like, kind of help you, right?  
**Speaker 3:** It surfaces the issue and then it guides you towards the resolution of the issue.  
**Speaker 4:** Yeah.  
**Speaker 1:** Yeah, I think for me, and I think we've kind of all contributed as we go. But I think that definitely, like, the idea of either, A, specifying like, because of the time that we have, like, case studies being identified, maybe a situation where it's like an IPD plus DOB plus renters, right? Like, maybe, uh, for the presentation or for our deliverables, like, finding one specific use case so we can, like, dive into that and not read too vague.  
**Speaker 1:** The idea also that it's like, okay, like, if, for example, if we're doing, like, you brought up a great point, like, there's not really a lot of empty lots, but through this process, like, it kind of closes the loop one, let's say, this is our, our, our scope. And, and at the end of the spectrum, when the renters feed the loop, let's say in the future if somebody was going to do this building, this data is already logged from, from, like, let's say scope one.  
**Speaker 1:** And if they're going to demolish scope two, then the users fill the, the rest of the loop into that, like, scope one. And so, like, if you continue to use this process, it will create more and more data for, like, neighborhoods.  
**Speaker 3:** Yeah.  
**Speaker 1:** And it learns from, from, yeah, like, other projects and structure. Previous scope instructs new scope.  
**Speaker 3:** Yeah, as long as the data, like, if, like, whatever data is public, it can start to pull from it. Like, obviously, like, it's not, like, in full proprietary information, but, like.  
**Speaker 2:** In a very kind of mixture of names, but it's like an idea of, like, integrated project risk intelligence.  
**Speaker 3:** Ooh, that's nice.  
**Speaker 4:** Wait, what's the?  
**Speaker 2:** Like, integrated project risk.  
**Speaker 4:** If we.  
**Speaker 3:** I think, you know, as, um.  
**Speaker 4:** It sounds cute. It's not very memorable.  
**Speaker 2:** I go, like, RGIS, I think. Or E3, it's like.  
**Speaker 3:** Ezri.  
**Speaker 2:** Yeah, yeah.  
**Speaker 3:** Nice. Cool. Um, all right.  
**Speaker 3:** Last but not least.  
**Speaker 2:** Oh, so I had one doubt. Like, how, like, could you explain how the product would, like, finally work? Like, so I, let's say I am the user.  
**Speaker 2:** So then, like, what do I, like, let's say I'm a user and I'm like, okay, this is the land I select. Or, like, this is a building I select.  
**Speaker 2:** What, how is the workflow going? Like, how will it go?  
**Speaker 2:** What would I want?  
**Speaker 3:** Um, I guess that's the input part, right? Like.  
**Speaker 2:** Okay.  
**Speaker 3:** If we say this is like an integrated project delivery, we have different parties, right? Um, maybe the owner can initiate because the owner is at the very beginning of the project phase, like, putting in the address, which link to different other, like, information about flooding, like, contamination, anything. And then the, like, the other parties can come in to, like, upload their plan and then kind of the system recognizes the system, uh, the structural system, like, and then parse that information.  
**Speaker 3:** And then, so, so, so the, so yeah, so it basically is still the address, the, the drawings as input. Um, and the output would be identifying all the potential, like, risk, um, of this project, um, from past sources.  
**Speaker 2:** Okay. So, like, I just open the website and I just put in, like, my address. But I won't have the structural plans, right?  
**Speaker 2:** Or, like.  
**Speaker 1:** Sorry. You could, like, it could be output is a dashboard, but then input could be a combination of, like, you know, hard inputted things like name, address, and stuff. So then for that side of the structure and architecture and MEP, whatever, it could be a plug-in or it could be something that's gathering information through Revit.  
**Speaker 1:** And not necessarily maybe, like, real-time, but, like, kind of like in, kind of like in, uh, when you do, like, e-transfer, like, you just submit that building. Like, add SD or CD and then it, like, removes the, the, uh, the metadata with the 3D model.  
**Speaker 1:** So it's like, it's not extra work to get that data. It's already in there.  
**Speaker 1:** And, and that's when you get the, like, the assets, I guess.  
**Speaker 2:** Yeah.  
**Speaker 1:** But the product is a dashboard. So, like, it extracts from different, like, it's a linear process, but it's like everybody kind of shoots at the same cloud, I guess, or, like, dashboard. And that's maybe what holds and instructs, like, your map or your, like, set.  
**Speaker 3:** And, and, like, people can pull, like, at various points. Like, you won't have the structural plans right away. But eventually you will.  
**Speaker 3:** And then, like, the, the challenge is that, like, those come in and then they're not at, like, they may or may not currently be cross-referenced with the other information that was relevant earlier. Like, you have, like, when you just go to the bare bone site, like, you have the soil, right?  
**Speaker 3:** And then you have, like, the surroundings and you have, like, basically the site conditions. And then, like, but that stuff, like, may not necessarily carry through later unless you have a unified place for it.  
**Speaker 3:** So then, like, when the structural plans come in and the geotechnical report, like, maybe was from earlier, like, that still needs to carry through so that, like, when you go to the site and you're doing, like, this renovation, like, all that data is there and it can be like, "Hey, guys, like, uh, the structural plans came in, like, and we're missing some shoring. And plus, there were all these, like, violations, plus the soil is, like, not great because of the, you know, boring logs data."  
**Speaker 3:** And, like, so, like, this project now, like, we identified some risks earlier and now that we have, like, more data from, like, structural and other folks, like, it's even riskier. So, like, keep an eye out for this project because, like, when you're going on site to construct, like, this is a high-risk project now because of all these factors.  
**Speaker 3:** And there could be, like, ways for, like, machine learning to, like, figure out, like, like, what's the highest risk and, like, lowest risk and severity levels. I mean, that could be more, like, deterministic.  
**Speaker 3:** It could involve machine learning based on, like, past data and the past projects. But, like, I think the end goal is that, like, people can have enough information that carries through from early stage or to later stage of the project so that when, like, something like this, like, literally they're on site and, like, someone isn't like, "Oh, we had no idea.  
**Speaker 3:** Like, we're just excavating here and there's a wall." No, actually, shit, like, this wall is going to collapse tomorrow if we don't fucking, like, you know, because we know from the whole project now and, and all this data and previous examples.  
**Speaker 4:** It would be very convincing if we can demonstrate, let's say, this case, if we can find floor plans of the proposed design of the adjacent lot and showcase, like, maybe highlighting that neighboring wall. I think it would be, it would be strong to demonstrate how our platform can call out this specific danger for this specific incidence. And it's just a thought.  
**Speaker 2:** Yeah, that would be a perfect demonstration.  
**Speaker 3:** Yeah. I think it could be good. Yeah, I mean, I think the, the one thing just on the sensitivity note that we were talking about before.  
**Speaker 3:** Like, sort of saying, like, it could have been prevented if. Like, I think that's, we don't want to sort of, like, say necessarily definitively, like, if something would have happened, it would have been prevented.  
**Speaker 3:** Like, I think we sort of present it neutrally. Like, we show this as a example.  
**Speaker 3:** Like, we, we present the facts and we present the potential, but we don't say, I think, like, it should have been done a different way.  
**Speaker 4:** Yeah.  
**Speaker 3:** Like, it could have been, like, because I think that sort of gets into sort of the things that we're just, we don't necessarily have all the information.  
**Speaker 2:** There's, there's a lot of people, I guess, uh, volunteering for help. TT has a specific forensic department.  
**Speaker 3:** We should talk to them.  
**Speaker 2:** We could talk to them about that.  
**Speaker 3:** We should talk to them.  
**Speaker 2:** Yeah. Um, was that your only one or did you have anything else?  
**Speaker 4:** I was like, could we do it, like, with an example? Is there, like, a proper use of Wispr? Like, could we, like, take an example and.  
**Speaker 3:** We have to, yeah, we should show it end to end. Like, it's sort of like, it's an end to end project, sort of like, uh, life safety, I mean, more things, but just for safety discussion. Like, life safety risk, like, mitigate or management sort of, like, workflow.  
**Speaker 3:** I think, Haungyu, you're like our test user, actually, I think. Like, you would use this, right, probably?  
**Speaker 2:** Yeah.  
**Speaker 3:** So, like, you're, I mean, many of us would, but.  
**Speaker 4:** Many of us would, yeah.  
**Speaker 3:** I think you have a really good sense of your background of, like, what a good, like, outcome would, would look like. I mean, you do too. I think most of you guys in this row do.  
**Speaker 3:** Um, but just from the perspective of the structural engineer, um, I think you have a really good, like, you would be a, a user, real estate development user, architecture. So I think we have a good group to kind of, like, test exactly what you're saying.  
**Speaker 3:** Like, as a workflow, an example. Like, we should find a, like, a lot.  
**Speaker 3:** What would be cool, I mean, what would be interesting is, like, when we get the, all of the sort of previous examples, um, we can ask it to, like, um, suggest a demo site based on a similar profile of the sites from the historical data, maybe. And then test that workflow.  
**Speaker 2:** I'm looking for open source, like Revit models of structures in New York to see if we find.  
**Speaker 3:** Oh, nice.  
**Speaker 3:** I do love Revit right here.  
**Speaker 2:** I really like.  
**Speaker 3:** But, um, okay, so I think, um, the only other last thing I think on my mind was just, like, the, the roasting thing. Like, personally, I think it's not quite, like, right for this, but, like, is that okay?  
**Speaker 2:** I wrote, I wrote a, a note that's like, only, I think it's too sensitive of a subject. Like, if we're going to be presenting the perfect thing.  
**Speaker 3:** Oh, you know.  
**Speaker 2:** We should do the roasting.  
**Speaker 1:** We can mention that specifically in the Revit part of it, there is an assistant clippy, clippy light that assists you through humor.  
**Speaker 4:** I love it separately though.  
**Speaker 2:** Yeah, it's like a, a potential, you can, you can turn it on and off.  
**Speaker 3:** I know. I mean, we can, we can debate it now, but I think we do need to come to a consensus about, like, what we're presenting and, like, whether humor is involved. Like, personally, I think we shouldn't.  
**Speaker 2:** Yeah.  
**Speaker 4:** As people, I think we have humor, but, like, the more we get into this case, the more inappropriate.  
**Speaker 1:** But I guess that means we're focusing on potential, like, collapses, like, our prevention targets.  
**Speaker 3:** Like, dangerous risks, like, yes. I mean, like.  
**Speaker 1:** Like, not stop work orders, like, collapses.  
**Speaker 4:** I wouldn't say we focus on catastrophic events. I think we, yeah, we focus on all kinds of building projects.  
**Speaker 1:** I guess in that term, it's only, uh, delicate when it is a collapse. It's not a collapse. Humor could be included.  
**Speaker 1:** Not, not that I'm arguing to keep it, not that I'm arguing to keep it, but it's like, but the idea of, like, it's only, it's too much if it's, like, you know, collapse related, I guess.  
**Speaker 3:** So, so I think the list from before was, um, structural failure, uh, which includes catastrophic failure.  
**Speaker 2:** Like full or partial collapse.  
**Speaker 3:** Uh, partial or full collapse. Uh, there's flooding, um, fire, safety, contamination on site.  
**Speaker 2:** Extreme weather.  
**Speaker 3:** Extreme weather conditions. Um, so stop work order, like, that's, that's like an output. I mean, in the sense of, like, if you're doing something wrong, obviously, like, you can get a stop work order.  
**Speaker 3:** It's not, like, the thing that causes it. But, like, we're dealing with all those.  
**Speaker 3:** There may be other ones that surface that are, like, sub ones, um, that, like, aren't as severe. Uh, like, I mean, there's also the work, worker, uh, construction worker safety was one.  
**Speaker 2:** Connection worker safety feels like another layer because they're in the cloud or.  
**Speaker 3:** But anyway, like, I think, like, Camila, like, I think even if we sort of went to things like just general code compliance, I think we just have to decide, like, we just have to just definitively say, like, we're not, it's, it's like, we're not including that or we are including. If we are including that, like, we basically can't do anything where people die.  
**Speaker 2:** Oh, I thought we'd get rid of the whole roasting thing.  
**Speaker 3:** All right.  
**Speaker 2:** Yeah. It's like, kind of strange if, like, say I used the roasting and then you reply to me, "Guess what? Your tenant is going to get cancer because this, this lot is contaminated."  
**Speaker 2:** It's just, maybe a little bit.  
**Speaker 3:** A little bit too much.  
**Speaker 4:** Yeah, I love that.  
**Speaker 2:** Yeah, not, not for this.  
**Speaker 3:** We should do that idea separately.  
**Speaker 2:** Yeah, yeah.  
**Speaker 3:** It's a good idea.  
**Speaker 2:** I'm going to do a story.  
**Speaker 3:** My guy here.  
**Speaker 2:** All right.  
**Speaker 4:** Sorry, you had another question?  
**Speaker 3:** Yeah, like, can we go through, like, a perfect, like, not a perfect, like, a hypothetical example? Let's say I log in and I press, like, the Chrysler lot or the Chrysler building. What am I expecting when I click that building?  
**Speaker 3:** Like, how we did that, we clicked that building. Now what am I expecting?  
**Speaker 4:** Yeah, let's talk through those. I don't think we have it fully fleshed out yet.  
**Speaker 3:** Should we do a new call or, like, keep it?  
**Speaker 4:** Yeah, yeah. Oh, really? Okay.  
**Speaker 2:** We're not doing, like, system building assessment. Like, what's, what's the Chrysler building example about?  
**Speaker 3:** Like, oh, let's say I want to renovate, like.  
**Speaker 2:** Oh, renovate.  
**Speaker 3:** Not, I won't say renovate, but as you said, like, there are no new lots available, right? So, so imagine we are going to remodel the Chrysler building.  
**Speaker 4:** Yeah, you're a billionaire.  
**Speaker 3:** So there's plenty of, there's plenty of ground up construction happening, like, all over the city, new lots, and there's plenty of renovations. So, like, we could walk through, like, a good example of that.  
**Speaker 2:** I will say, like, your example, um, I know you're just giving the price of building, but alterations, from what I understand, are, like, the majority of cases people are considering, especially here in New York City. Like, you were saying alterations are, like, the main thing that's happening. Am I right?  
**Speaker 4:** Or demolition. Let's focus on alteration for the purpose of this demo.  
**Speaker 2:** I agree with that.  
**Speaker 3:** For, like, just the walkthrough right now, for him.  
**Speaker 2:** Yeah, just right now.  
**Speaker 3:** It's like, I'm just using Chrysler as a random example.  
**Speaker 2:** It's a good, it's a good, like, let's use whatever, like, makes sense to, like, make the point of, like, what's the workflow.  
**Speaker 3:** Yeah.  
**Speaker 4:** Yeah.  
**Speaker 3:** Like, I'm a billionaire or I'm an owner or something.  
**Speaker 4:** Nice.  
**Speaker 3:** Going with the extreme one. And then I choose to remodel the Chrysler. I just select that.  
**Speaker 3:** So then what is the next step that's supposed to happen?  
**Speaker 4:** Yeah. From what I know, we have a platform. So you go open your computer or phone and you type in our website address.  
**Speaker 4:** You go to our platform.  
**Speaker 2:** You submit the project, like, set up the project with, like, address and.  
**Speaker 3:** And you, like, but, like, setting up the address is basically choosing the Chrysler building. When you choose it on the map, it's basically setting the address.  
**Speaker 4:** Yeah.  
**Speaker 3:** So we, like, let's use, like, a more realistic example. Like, what would be one that, like, you would, like, sort of propose as, like, an example?  
**Speaker 2:** Take a walkthrough together.  
**Speaker 4:** That's like the easiest. Let's do a regular building.  
**Speaker 3:** I think it's like pretty, yeah, like.  
**Speaker 4:** Yeah, like a.  
**Speaker 2:** Let's just pick one, like, let's just pick one.  
**Speaker 4:** Yeah.  
**Speaker 2:** Yeah, like, a four-story apartment that had, that's pre-war building, like, has a, like, rubble foundation, tarry walls, and the building collapsed while they installed and underpinning. And, and then, so if we search a project that has the sim, that has similar profile, like, similar time where, when it's constructed, um, and maybe we have, like, slower information, like, I don't know, but that's very specific.  
**Speaker 1:** Wait, are you saying that our project is the one that collapsed or?  
**Speaker 2:** Yeah, just as an example.  
**Speaker 4:** As a model.  
**Speaker 3:** Right, right. No, different, different. Like, that's a historical example.  
**Speaker 2:** Yeah.  
**Speaker 3:** So what I'm understanding is, like, okay, you have a townhouse in Brooklyn, and you're going to, like, there's, there's, like, a lot, and you're, there's a building adjacent and it's a tarry wall.  
**Speaker 1:** Like this.  
**Speaker 3:** No, like this. Like, you're, you're, you're starting on the, on the building that's.  
**Speaker 4:** You're working on the lot.  
**Speaker 3:** Yeah, yeah. You're going to build something, there's an adjacent building there. So there's, like, so I'm, like, putting in the address for the new building, like, the, the lot.  
**Speaker 3:** And I want to know, where else in the city was there a similar condition with, like, the soil, like, the, the adjacency, like, the, the sort of, like, materiality, the construction type of adjacent buildings so that, like, when I'm building this, I, like, understand that, like, there's specific things from a risk profile and, like, from a life safety kind of standpoint, things that we need to go off and check and make sure.  
**Speaker 2:** Right. Yeah.  
**Speaker 3:** So, like, the next time they're doing a building, like the, the first one, like, someone should be able to basically put in that. And if it's like, hey, this is quite similar to that building that, that had the wall collapsed, I should get all of that information and any other similar data from other similar projects that had those issues.  
**Speaker 1:** And that's like the starting, like, like, splash screen, like, like, here are other buildings just like this, but then, like, the, the, the UX looks like kind of the, the map or, like, the plan view of, like, the master plan of things.  
**Speaker 2:** Are we done with the chronicle?  
**Speaker 3:** No, we're just, we're, we're like walking through one example of, like, the kind of user flow right now.  
**Speaker 2:** Oh, that's awesome.  
**Speaker 3:** Like, one particular example.  
**Speaker 2:** Yeah.  
**Speaker 3:** I think we're just trying to understand, like, from the perspective of, like, someone who would be using it, like, what would we be looking for, like, in terms of, like, the initial, like, flow of it?  
**Speaker 2:** Yeah. Yeah, I guess just like what you said, like, we, we have the input, um, and we grab the profiles of the project we want to develop and we compare with existing databases and, and then spits out all the risk factors we should look out for, whether it's structural, like, or fire safety and other hazards. So it's like a multi-hazard sort of tool.  
**Speaker 3:** And then I was.  
**Speaker 2:** Will we have the structured plans? Can we actually type the address?  
**Speaker 1:** No, eventually I'm looking through the, through the Revit model of the structural component.  
**Speaker 3:** So we input an address, we get, like, okay, uh, the address gives us a lot of information, like the similar buildings, uh, which were built, like, uh, like, with similar conditions, like a building which you are proposing to build, but, like, we've seen other similar buildings having these type of risks. Is that what the person sees first?  
**Speaker 2:** Do you feel like that's true to how you would approach that, like comparing between buildings? Yeah, that's a very good, yeah, because if I'm working on a new project and I, I don't know about all the other similar type of project that has the problem, then it would be very beneficial to learn for the similar type of project, like, what did they do wrong and what I can do to avoid it. I think it's going to be very beneficial.  
**Speaker 3:** Now, just from the perspective of, like, bringing the DOB back in, like, it could pull in, like, all this, like, new data sources that we're talking about from, like, the DOB as well, like, objections, like, and it can basically say, like, this is the, the sort of, like, risk profile or, like, risk mitigation kind of, like, profile of your lot right now. Plus, here's some recommendations for when you're filing for DOB, how to go through it in a way that would be more, like, streamlined based on  
**Speaker 3:** if the profile of, like, the site and the building type and materiality and construction type matches similar profile of, like, DOB communications. So that could also come in there, like, and you start to get this, like, sort of, like, intelligent mapping of, like, the, the, the sort of, like, site conditions, building adjacencies, and the process for how you get this built and where there was, like, also, um, like, it could, like, flag things or, like, this is where DOB, like, might find issues too. And so, like,  
**Speaker 3:** you, you should address these upfront.  
**Speaker 2:** Mm-hmm. Yeah.  
**Speaker 4:** And as a suggestion, just, sorry, we were talking about potential use cases, and I went on Zillow to see properties on sale, and next to the building that collapsed, there are two other properties that are on the market that are of similar, built in similar time period and similar condition that are, like, relative. Well, there's a lot of buildings on sale, but the closest one I found is like a five-minute walk from the building that collapsed that was also, like, older than.  
**Speaker 2:** How easy is it to find that building?  
**Speaker 4:** I know the location of that building, so I just went on to see properties on sale, and I looked around that area.  
**Speaker 2:** So time, time.  
**Speaker 3:** Right, yeah, yeah.  
**Speaker 4:** Yeah.  
**Speaker 2:** The time period was helping you narrow down it, so it's like.  
**Speaker 4:** I mean, once you go into that property, it tells you when it was built.  
**Speaker 1:** The, the seller or, like, the organizational.  
**Speaker 4:** Sorry?  
**Speaker 1:** Like, the seller organizational data could be kind of what we do for some sort of time filter or, like.  
**Speaker 4:** Yeah.  
**Speaker 1:** Maybe inspiring.  
**Speaker 3:** Getting lots that are on sale too.  
**Speaker 1:** Or just the way, like, the UX there, like, just, like, because we were talking about, like, how we get the data, like.  
**Speaker 3:** Yeah.  
**Speaker 1:** You put, you know, address.  
**Speaker 4:** And the sales.  
**Speaker 1:** And the address and, like, time.  
**Speaker 3:** Okay. That's interesting.  
**Speaker 4:** Yeah, so that's.  
**Speaker 3:** So yeah, like, like, lots that are actually, um, properties that are on sale, like, that could also be a competitor for, like, showing risk profiles of, like, lots that are on the market.  
**Speaker 4:** That could be a use case if we wanted to demonstrate the building that collapsed and say, like, for example, if we want to buy a nearby building and then the risks would, like, come up as a precedent. I don't know, just a thought.  
**Speaker 1:** Cool.  
**Speaker 4:** Yeah.  
**Speaker 3:** All right. Good session. Um, should we.  
**Speaker 4:** Should we try to.  
**Speaker 2:** Let's go ahead and.  
**Speaker 4:** Wrap it up.  
**Speaker 2:** Good session.  
