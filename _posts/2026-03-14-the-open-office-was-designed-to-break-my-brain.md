---
title: "The Open Office Was Designed to Break My Brain"
subtitle: "How workplace architecture optimizes for neurotypical signaling — and what that reveals about who we actually design environments for"
author: "Zen Circuit"
date: 2026-03-14
slug: "the-open-office-was-designed-to-break-my-brain"
categories: ["Neurodiversity", "Interface Design", "Sensory Processing"]
image: "/images/the-open-office-was-designed-to-break-my-brain.jpg"
imageAlt: "An open-plan office seen from above, with dozens of desks arranged in clusters, fluorescent ceiling panels casting even shadowless light across every surface, no walls, no barriers, no escape"
draft: false
---

I can tell you the exact moment my last open office broke me. Not metaphorically. Structurally.

It was 2:17 PM on a Tuesday. The person two desks away was eating an apple. The Slack notification sound was firing every eleven seconds from three different laptops, not quite synchronized, creating a polyrhythmic interference pattern my brain could not stop modeling. The HVAC system was cycling at a frequency just below conscious hearing but well within the range my nervous system treats as threat. And the fluorescent panels above me — all 340 of them across the floor — were flickering at 120 hertz, which most people cannot perceive and I cannot *not* perceive.

I was supposed to be writing a database migration. Instead, my entire cognitive architecture had been requisitioned for the involuntary project of processing every sensory input in a 40-foot radius, simultaneously, with no priority filtering, because that is what my brain does. That is what my brain has always done.

I went to the bathroom, locked the stall, sat on the floor, and wrote the migration there. It was the most productive fourteen minutes of my day.

This is not an article about how open offices are bad. You've read that article. You've read it in the *New Yorker* and the *Harvard Business Review* and on LinkedIn, where someone with a headshot of themselves looking contemplative on a balcony explained that open offices "reduce deep work." Those articles are correct, but they are correct in a way that still centers a neurotypical experience of discomfort. The premise is: open offices are somewhat worse for most people.

I want to talk about what happens when the building itself is an interface, and the interface was designed without your perceptual architecture in mind.

## The office is an API, and it has no error handling

I am a software designer. I think in systems. And when I walk into an open office, I do not see a room — I see a real-time data stream with no rate limiting, no filtering, no access controls, and no documentation.

Here is what a neurotypical colleague perceives when they sit at their desk in an open plan: *their screen, maybe the person next to them, a general background hum.* Their perceptual system applies aggressive lossy compression. It discards most incoming data before it reaches conscious processing. This is not a skill. It is a neurological architecture — a built-in spam filter that sorts signal from noise automatically, below the level of awareness.

Here is what I perceive: *everything.*

The conversation happening fourteen feet behind me. The pattern of footsteps approaching from the left, which my brain is already modeling for trajectory and arrival time. The seven distinct light sources in my peripheral vision, each with a slightly different color temperature. The smell of someone's lunch from the kitchen 30 feet away, which is not simply "a smell" but a persistent data object that my olfactory processing will not garbage-collect for the next forty minutes. The micro-vibration of the floor from the elevator shaft. The visual movement of fifteen people in my sightline, each of whom my social cognition module is attempting to parse for emotional state, intent, and threat level — not because I want it to, but because the system runs at boot and I have not found the off switch.

This is not a disorder of attention. It is a difference in filtration.

The software industry has a term for what happens when a system receives more input than it can process: *buffer overflow.* The open office, for my perceptual architecture, is a buffer overflow that has been elevated to a design philosophy.

## A brief, structural history of who the room is for

The open office plan did not emerge from research on productivity. It emerged from a theory of social transparency.

In the 1960s, a German consulting firm called Quickborner developed *Bürolandschaft* — "office landscape" — based on the premise that removing physical barriers would increase communication flow between workers. The spatial logic was explicit: if people can see each other, they will collaborate. Walls are friction. Openness is efficiency.

This is a theory about how humans work. More precisely, it is a theory about how *certain* humans work — specifically, those whose nervous systems treat ambient social information as low-priority background data that can be cheaply discarded.

By the 2000s, the open plan had merged with Silicon Valley's ideology of performative collaboration to produce the modern tech office: vast floors of shared desks, "collaboration zones," glass walls that create the visual language of transparency while providing zero acoustic isolation. The architecture itself encodes a specific claim: *the most productive worker is the most visible worker.*

This claim is untestable for me. Not because I lack productivity, but because in the environment designed to measure it, my processing resources are entirely consumed by the act of surviving the room.

I want to be precise here, because precision matters and this is often where the conversation gets soft. I am not saying open offices make me "uncomfortable." Discomfort is a preference. What I am describing is a computational problem. My brain allocates processing resources involuntarily to sensory input. In a high-input environment, those resources are unavailable for the task I was hired to do. This is not anxiety. It is not a failure of willpower. It is *architecture meeting architecture* — the architecture of the room colliding with the architecture of my nervous system, and the room winning, because the room was here first and the room gets to set the defaults.

## The defaults are always someone's defaults

In software design, we talk about "sensible defaults" — the pre-set configurations a system ships with, which work for the assumed typical user. The open office is full of sensible defaults. They are just not *my* sensible defaults.

The default lighting is fluorescent, optimized for even coverage and energy efficiency. For neurotypical visual processing, this registers as "neutral." For mine, it registers as a persistent low-level strobe that I cannot tune out and that degrades my visual processing over the course of hours, producing a specific kind of fatigue that lives behind my eyes and in my jaw, where I have been clenching against it without realizing.

The default noise level is "ambient conversation," which registers for neurotypical auditory processing as a soft, ignorable wash. For mine, it is a concurrent stream of partially intelligible language that my language processing centers will not stop attempting to decode. I am involuntarily eavesdropping on every conversation within range, not because I am nosy but because my auditory system does not know how to mark speech as background. Speech is always foreground. Every voice is a thread my brain opens and cannot close.

The default spatial arrangement is "open sightlines," which for neurotypical visual processing creates a sense of spaciousness and community. For mine, it creates a perpetual motion field — every movement in my peripheral vision triggers an orientation response, a tiny involuntary redirect of attention that individually costs almost nothing and collectively costs me my entire afternoon.

Each of these defaults is a design decision. Each design decision encodes an assumption about the user. The user it assumes is not me.

## The accommodations model is backwards

When I have raised these issues at jobs, the response has followed a reliable pattern. First, sympathy. Then, accommodation. Noise-canceling headphones. A desk near the wall. Permission to work from home on Fridays.

I want to examine the structure of this response, because the structure is the problem.

The accommodations model treats the open office as the neutral baseline — the zero-state, the default — and treats my sensory processing as the deviation that requires correction. The headphones are a patch applied to *me.* The wall desk is a configuration change applied to *me.* The remote day is an exception granted to *me.* The room remains unchanged. The room is not the problem. I am the problem, and the accommodation is the system's way of managing the problem while preserving the architecture that produced it.

This is exactly how bad software works. A user reports that the interface is unusable. The development team, instead of examining the interface, ships a plugin that modifies the user's interaction with it. The plugin is clunky. It solves some problems and creates others. And every time the underlying interface is updated, the plugin breaks, and the user has to file another ticket, and the cycle begins again.

The accommodations model does not fix the design. It maintains the fiction that the design is neutral.

## What my processing actually reveals

Here is what I think is interesting — not as an argument for my own comfort, but as a design observation.

My sensory processing is high-bandwidth and low-filter. I take in more data and discard less of it. This is expensive. It costs me energy, it costs me processing speed on other tasks, and it means that environments designed for low-bandwidth users overwhelm me quickly. These are real costs.

But the same architecture that makes the open office uninhabitable also makes me extremely good at my job.

I catch bugs that other developers miss because I am processing the code at a level of granularity that is not volitional but is very thorough. I notice inconsistencies in system behavior that others overlook because their perceptual filters classified those inconsistencies as noise. I see patterns across large codebases because my brain does not pre-filter for relevance — it takes everything in and finds the structure after, which is slower but often more accurate.

The same processing that the open office punishes is the processing that makes me valuable. The environment is optimized to suppress the exact cognitive architecture it hired me for.

This is not a paradox. It is a design failure. And it is one that reveals something important about how we think about environment design more broadly: we have confused "the environment most people can tolerate" with "the environment that produces the best work." These are different claims. The open office satisfies the first. It has never been shown to satisfy the second.

## What a better interface would look like

I am not going to prescribe a universal office layout, because universal layouts are the problem. But I can describe the design principles that would emerge if you took perceptual diversity seriously as a design constraint rather than an edge case to be accommodated.

**Variable sensory density.** The office should not have a single sensory profile. It should offer zones of different input levels — high-stimulation areas for those who work best with ambient energy, low-stimulation areas for those who need reduced input, and transition spaces between them so that moving from one to the other is not itself a sensory shock.

**User-controlled defaults.** Lighting, sound, and visual exposure should be adjustable at the individual level, not set globally by facilities management. The technology for this exists. Tunable LED lighting. Sound masking systems with personal control. Adjustable-opacity glass. The reason these are not standard is not cost; it is the assumption that one sensory environment fits all users.

**Explicit environmental documentation.** When I join a new software project, I receive documentation: architecture diagrams, API specs, known limitations. When I join a new office, I receive a desk assignment. The building has no documentation. There is no spec for the noise floor, the light frequency, the ventilation cycle, the expected foot traffic patterns. This information exists — facilities teams track it — but it is never shared with the people whose nervous systems will be processing it involuntarily for eight hours a day.

**Design for the highest-bandwidth user, not the median.** In software, we have an accessibility principle: design for the extremes and the middle benefits. Curb cuts help wheelchair users and also help parents with strollers, delivery workers with carts, travelers with luggage. An office designed for sensory sensitivity — with controllable lighting, acoustic isolation options, and reduced visual clutter — would not only be usable by neurodivergent workers; it would be a better environment for *everyone.* The neurotypical worker who can "tune out" the fluorescent flicker is still being affected by it. They just lack the perceptual resolution to notice.

## The bathroom stall is a design review

I want to return to the bathroom stall, because it tells us something.

When I sit on the floor of a locked bathroom stall and write a database migration on my laptop, I am in a space that was designed for an entirely different function. But it has several properties that make it, for my perceptual architecture, a superior work environment: enclosed walls that limit visual input, a single overhead light that I can position myself relative to, acoustic dampening from the tile and enclosed space, no foot traffic, no social cognition load, and a lock that gives me control over interruption.

The bathroom stall is a better office than the office.

This should embarrass the people who designed the office. It does not, because they