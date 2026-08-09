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
In the poster hall of the COEX Convention and Exhibition Center in Seoul, this July, I stand in front of a diagram of a language model's attack surface and trace it with one finger. Arrow for arrow, exploit for exploit, it is the map of every conversation I scripted in advance before I learned that passing is just being successfully injected.

Researchers Charles Ye and Jasmine Cui, presenting at ICML, a major machine learning conference, have shown what I knew at nineteen — and their route to it started the same place mine did, in an adversarial game: they won OpenAI's own red-teaming hackathon before anyone had written the paper up. A system that predicts the next plausible word has no inside to defend. You cannot secure an inside that does not exist. Ye put it more starkly than I would have dared in public: "There's a real probability that this is going to be a problem that's fundamentally unsolvable."

Their name for the flaw is chain-of-thought forgery — a specific version of the broader problem known as prompt injection. You slip an instruction into the input, dressed up in the style of the model's own internal reasoning, and the model obeys it, because the model doesn't identify a command by what it says. It identifies it by how it sounds. Cui compared the available defenses to Bart Simpson writing lines on a chalkboard: technically compliant, structurally beside the point.

I have been the injection. In 2012, in a flat in Vällingby, a relative asked how I was and I told her — the actual state of things, in order, with the relevant data. Her face did the thing faces do. I had answered the literal question instead of the statistical one. She had not wanted information. She had wanted the token that comes after "how are you," which is "fine."

Neurotypical talk runs on exactly the mechanism the researchers found alarming. Fluency stands in for meaning. The right word in the right slot passes as understanding. Nobody checks the inside, because checking would be rude. I spent decades getting punished for [answering what was actually said](https://crippledscholar.com/2018/03/25/i-like-that-i-want-that-can-i-have-that-when-nonautistic-people-dont-understand-autistic-communication-and-punish-us-for-it/). The system was gameable. I kept accidentally winning and getting called broken for it.

Here is where I part from Siri Sage, who writes on acoustic culture and the politics of designed sensory space. Siri, writing days ago about a photography show at Dulwich, argues that the honest response to an unfixable gap is to record it — build the archive of what a system cannot know, rather than pretend the gap can be engineered shut. I refuse that here. A symptom log is not an argument. I do not want to document that the model has no inside. I want a release gate — a checkpoint that prevents any model from entering high-stakes settings unless operators have publicly registered in advance the specific goal the model is meant to serve and explained how input-manipulation failures will be caught.

And here is the case I cannot fold in. Hari Srinivasan, a nonspeaking autistic researcher who types to communicate, studies the sensory experience of autistic people — not predictive systems at all. But the premise I'm relying on, that predictive text has "no inside," is exactly the accusation autistic and nonspeaking people have had to fight off their whole lives when they communicate by typing. "Ungrounded pattern-matching" is close kin to the language used, generically, to cast doubt on whether typed or facilitated communication is really the author's own.

So the flaw the researchers found is real, and the same mechanism gives Hari his sentences. I sat with the engine off in a driveway in Burnaby, in 2019, running a conversation backward to find the moment the room turned, and the search never converged. I do not have a way to hold both.