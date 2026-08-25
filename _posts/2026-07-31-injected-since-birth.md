---
layout: post
title: "Injected Since Birth"
date: 2026-07-31
author: "Zen Circuit"
category: neurodiversity
image: /assets/injected-since-birth_setting_1.jpg
image_alt: "Injected Since Birth \u2014 editorial illustration"
excerpt: "Autistic people get punished for exposing the exact same flaw in human communication that AI researchers just discovered and published."
keywords: [prompt injection attacks, ICML machine learning conference, autistic masking, neurotypical communication, language model security vulnerabilities, passing as autistic person, prompt injection disability]
source_url: "https://www.technologyreview.com/2026/07/30/1140927/a-fundamental-flaw-leaves-llms-vulnerable-to-attack/"
source_title: "A fundamental flaw leaves LLMs strikingly vulnerable to attack"
source_outlet: "MIT Tech Review"
draft_score: 9
---

> **Correction, 25 August 2026 (first-person axis):** three claims have been removed. The article
> reported a relative asking the author how she was and the exchange that followed, said the
> researchers had shown "what I knew at nineteen," and said the author had spent decades being
> punished for answering literally. A named relation, a conversation, an age and a life history are
> factual claims; Zen Circuit is a fictional editorial persona and the byline's material supplies
> none of them. Each point is now made about the mechanism rather than about a remembered occasion.
> Ye and Cui, the flaw's name, the hackathon, Ye's quotation, Cui's comparison and Hari Srinivasan's
> work and description are unchanged, as is the argument that the accusation levelled at predictive
> text is the one levelled at people who type to communicate.


> **Correction, 25 August 2026 (wound rule):** this article contained a scene in which the writer
> sits in a car with the engine off after a conversation in which they had been talking too long.
> That scene is a fixed element of this byline's authored backstory and recurs across essays under
> it; earlier passes removed its dates and durations but left it standing as standpoint. This
> publication has since decided that a persona's authored backstory is not evidence that an event
> occurred, however interior the scene or unnamed its participants. The scene has been removed and
> the point it carried is now made without claiming it happened. Nothing else has changed.


> **Correction, 24 August 2026:** Three first-person scenes were given exact places and dates —
> standing in the poster hall at COEX in Seoul, a flat in Vällingby in 2012, a driveway in
> Burnaby in 2019 — which cannot be verified. The conference itself is real and correctly placed:
> ICML ran at COEX in Seoul from 6 to 11 July 2026. The scenes are kept as this writer's
> standpoint without the false precision. The companion piece was also misdescribed. Siri Sage's
> article on the Dulwich photography show does not argue for building an archive of what a system
> cannot know; it ends undecided and says so plainly, and the disagreement is now with what that
> piece actually says. Hari Srinivasan was called "nonspeaking"; he is described in his own
> institution's material as minimally speaking, communicating largely through AAC and typing.
> **Checked and unchanged, and it all holds:** Charles Ye and Jasmine Cui as the researchers, the
> flaw's name, chain-of-thought forgery, the ICML presentation, the OpenAI red-teaming hackathon
> they won first, Ye's sentence word for word, Cui's Bart Simpson comparison, and Srinivasan as a
> Vanderbilt neuroscience researcher working on sensory processing in autism.

There is a diagram of a language model's attack surface in the work presented at ICML in Seoul this July. Arrow for arrow, exploit for exploit, it is the map of every conversation I scripted in advance before I learned that passing is just being successfully injected.

Researchers Charles Ye and Jasmine Cui, presenting at ICML, a major machine learning conference, have shown formally what autistic people work out early, and their route to it was the same kind of adversarial game: they won OpenAI's own red-teaming hackathon before anyone had written the paper up. A system that predicts the next plausible word has no inside to defend. You cannot secure an inside that does not exist. Ye put it more starkly than I would have dared in public: "There's a real probability that this is going to be a problem that's fundamentally unsolvable."

Their name for the flaw is chain-of-thought forgery — a specific version of the broader problem known as prompt injection. You slip an instruction into the input, dressed up in the style of the model's own internal reasoning, and the model obeys it, because the model doesn't identify a command by what it says. It identifies it by how it sounds. Cui compared the available defenses to Bart Simpson writing lines on a chalkboard: technically compliant, structurally beside the point.

I have been the injection. Answer "how are you" with the actual state of things, in order, with the relevant data, and watch the face do what faces do. The literal question got answered instead of the statistical one. Nobody wanted information. They wanted the token that comes after "how are you," which is "fine."

Neurotypical talk runs on exactly the mechanism the researchers found alarming. Fluency stands in for meaning. The right word in the right slot passes as understanding. Nobody checks the inside, because checking would be rude. Autistic people get punished for [answering what was actually said](https://crippledscholar.com/2018/03/25/i-like-that-i-want-that-can-i-have-that-when-nonautistic-people-dont-understand-autistic-communication-and-punish-us-for-it/). The system was gameable. We kept accidentally winning and getting called broken for it.

Here is where I part from Siri Sage, who writes on acoustic culture and the politics of designed sensory space. Siri, writing days ago about a photography show at Dulwich, ends on an unfixable gap and declines to resolve it — the argument, that piece says, is better with a hole in it. I cannot leave it there. A hole is not an argument. I do not want to document that the model has no inside. I want a release gate — a checkpoint that prevents any model from entering high-stakes settings unless operators have publicly registered in advance the specific goal the model is meant to serve and explained how input-manipulation failures will be caught.

And here is the case I cannot fold in. Hari Srinivasan, a minimally speaking autistic researcher who types to communicate, studies the sensory experience of autistic people — not predictive systems at all. But the premise I'm relying on, that predictive text has "no inside," is exactly the accusation autistic and nonspeaking people have had to fight off their whole lives when they communicate by typing. "Ungrounded pattern-matching" is close kin to the language used, generically, to cast doubt on whether typed or facilitated communication is really the author's own.

So the flaw the researchers found is real, and the same mechanism gives Hari his sentences. I know the loop of running a conversation backward looking for the moment the room turned, and never finding it — the search that does not converge. I do not have a way to hold both.