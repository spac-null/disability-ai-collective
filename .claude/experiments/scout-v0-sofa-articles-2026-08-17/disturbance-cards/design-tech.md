# Disturbance Cards — Design/Architecture + Technology

## Card 1 — The shed that replaced the repair

**SOURCE:** The Hustle — "Why so many New York City sidewalks are covered in scaffolding"
**URL / SOURCE ID:** https://thehustle.co/originals/why-so-many-new-york-city-sidewalks-are-covered-in-scaffolding
**DATE:** March 14, 2025

**EXACT DISTURBANCE FRAGMENT:**
A sidewalk shed on East 9th Street in Manhattan was "permitted in September 2010" and was
still standing as of this piece (March 2025) — over 14 years. City Councilmember Carlina
Rivera: "Sidewalk sheds and scaffolding are meant to keep New Yorkers safe, but too often
sheds are left in place longer than they need to be." Installing/maintaining a shed runs
about $150/linear foot ("tens of thousands of dollars" total); the facade repair it is
meant to precede "could total into the six figures and even up to $1m." The fine for
non-compliance is $1,000/month; the permit renewal is $130/year.

**LOCAL CONTEXT:** Local Law 11 requires building owners to erect a sidewalk shed — by
definition a temporary structure — the moment a facade inspection flags a safety issue,
covering pedestrians until the repair is done.

**WHY THIS IS STRANGE:** The "temporary" classification is the terminal state for
roughly 1,900 sheds citywide that have stood two years or more, 300+ that have stood
five years or more, and at least one that has stood fourteen. The structure meant to be
a stage before the repair has, for a large share of buildings, become a substitute for
the repair, indefinitely.

**WHAT THE SOURCE ITSELF SAYS IS HAPPENING:** Simple cost arithmetic: a shed costs a
tiny fraction per year of what the underlying facade repair would cost, and the
penalties for leaving it up (a $1,000 monthly fine, a $130 annual permit) are far
cheaper than fixing the building, so owners rationally defer repair as long as they can
tolerate the fine and the shed.

**WHAT THAT EXPLANATION MAY FAIL TO EXPLAIN:** If the economics are this transparent and
apparently well understood by everyone (owners, the city, reporters), it's unclear why
Local Law 11's enforcement mechanism has no escalating penalty or forced-repair trigger
after some duration — the rule appears to have been written assuming sheds would be
self-limiting, and nothing in the piece explains why that assumption was never revisited
despite decades of visible counter-evidence.

**POSSIBLE HIDDEN MECHANISM (HYPOTHESIS):** Shed rental/installation is itself a
business with an ongoing revenue interest in duration; it's plausible (unverified) that
the fine schedule has stayed low in part because it doesn't threaten an entire adjacent
industry the way a forced-repair deadline or steeply escalating fine would.

**WHAT WOULD HAVE TO BE VERIFIED:**
- Whether the $1,000/month fine has ever been raised since Local Law 11 (or its
  predecessor Local Law 10) was enacted, and by how much reform bills actually raise it
- Whether shed-rental/scaffolding companies have lobbied city council on shed-duration
  or fine legislation
- What the original drafters of Local Law 10 (1980, post-Grace Lee Boggs facade
  collapse) or Local Law 11 (1998) assumed about typical shed duration

**WHAT WOULD MAKE THIS A BAD ARTICLE:** Treating it as "NYC scaffolding is annoying and
everywhere" without showing the specific $150/linear-foot-vs-six-figure-repair-vs-
$1,000-fine arithmetic that makes indefinite deferral the obviously rational choice.

---

## Card 2 — The power plant with wheels

**SOURCE:** Winbuzzer — "EPA Rules xAI Illegally Operated Gas Turbines at Memphis Data
Centers, Closing Loophole That Allowed Year-long Pollution Without Permits"
**URL / SOURCE ID:** https://winbuzzer.com/2026/01/20/epa-rules-xai-illegally-operated-gas-turbines-at-memphis-data-centers-closing-loophole-that-allowed-year-long-pollution-without-permits-xcxwbn/
**DATE:** January 20, 2026

**EXACT DISTURBANCE FRAGMENT:**
xAI classified its gas turbines as "non-road engines — a designation typically for
mobile generators on trailers." Only 15 turbines were permitted; the company actually
operated up to 35, continuously, for a fixed data-center campus. Southern Environmental
Law Center attorney Patrick Anderson: "Every single time I've ever seen turbines
anywhere, they have an air permit. So we are confused because we have not seen a public
notice."

**LOCAL CONTEXT:** Under the Clean Air Act, whether a pollution source needs a full air
permit turns on whether it's "stationary." Genuinely mobile equipment (e.g., a
construction-site generator on a trailer) gets lighter regulatory treatment than a fixed
power plant.

**WHY THIS IS STRANGE:** The turbines satisfy the letter of "mobile" — they sit on
trailers — while doing, in practice, exactly what a stationary power plant does: running
in place, continuously, for over a year, to power a permanent supercomputer campus. The
wheels underneath the machine, not anything about how it's actually used, are what
determined its regulatory category.

**WHAT THE SOURCE ITSELF SAYS IS HAPPENING:** xAI is described as relocating (or
administratively re-designating) turbines before the 364-day threshold that would
trigger mandatory permitting, resetting the clock on the "temporary" designation each
time.

**WHAT THAT EXPLANATION MAY FAIL TO EXPLAIN:** It doesn't explain why the presence of
wheels/trailers should determine emissions-permitting obligations at all, when the
variable regulators actually care about — tons of NOx released into one neighborhood's
air per year — is identical whether or not the machine happens to be bolted down.

**POSSIBLE HIDDEN MECHANISM (HYPOTHESIS):** The "non-road/mobile engine" carve-out in
Clean Air Act implementing rules was likely written for genuinely itinerant equipment
moving between short-term job sites, and never anticipated a use case where "mobile"
hardware is deployed permanently at data-center scale — a classification built around
one physical pattern (temporary construction power) repurposed for a completely
different one (permanent industrial power) because the rule's text checks form
(wheeled/trailer-mounted) rather than function (actual dwell time and continuous
operation) until a regulator is forced to specify it after the fact.

**WHAT WOULD HAVE TO BE VERIFIED:**
- The literal regulatory text defining "non-road engine"/mobile source, and whether it
  specifies any dwell-time limit independent of the 364-day permit-exemption clock
- Whether turbines were ever physically moved between the two Memphis-area sites, or
  only administratively re-designated on paper
- Full timeline cross-check between EPA's January 2026 ruling and xAI's continued
  turbine operation afterward

**WHAT WOULD MAKE THIS A BAD ARTICLE:** Flattening it into a generic "Elon Musk pollutes
a Black neighborhood" piece without dwelling on the specific mechanism — a permitting
category built for equipment with wheels being used to describe a power plant.

---

## Card 3 — The genuine part that fails its own authenticity check

**SOURCE:** The Register — "iFixit disappointed by repairability of new M4 MacBook Air"
**URL / SOURCE ID:** https://www.theregister.com/2025/03/17/m4_macbook_air_repair/
**DATE:** March 17, 2025

**EXACT DISTURBANCE FRAGMENT:**
iFixit swapped logic boards between two identical M4 MacBook Airs. Apple's System
Configuration utility flagged an error that disabled True Tone on the display. iFixit:
"These software blocks manifest regardless of whether you're using third-party
components or OEM parts from salvaged devices." Their only fix required going "through
the Self Service Repair Store team, which of course, we hadn't used to buy the part."

**LOCAL CONTEXT:** In 2024 (iOS 18), Apple publicly said it would stop disabling
features like True Tone and battery health when a genuine part is installed without
going through Apple's approval process — framed as a rollback of "parts pairing"
restrictions.

**WHY THIS IS STRANGE:** The swapped part isn't counterfeit, isn't third-party, isn't
damaged — it's a working, genuine Apple component pulled from another unit of the exact
same model — and the software still treats it as suspect. The check isn't verifying
"is this part real and functional," it's verifying "was this part's serial number
registered to this specific device through Apple's tracked channel" — a supply-chain
provenance check dressed as a hardware-compatibility check.

**WHAT THE SOURCE ITSELF SAYS IS HAPPENING:** Apple's parts-pairing system checks each
component's serial number against Apple's servers; if a part isn't registered as
sold-to-this-device, dependent features (True Tone, in this case) get disabled until the
swap is "approved" through Apple's own repair channel.

**WHAT THAT EXPLANATION MAY FAIL TO EXPLAIN:** It doesn't explain why Apple's 2024
policy change — publicly framed as ending exactly this behavior — hadn't reached
MacBooks a year later, or why "genuine parts should just work" and "every part must be
individually re-registered with Apple regardless of authenticity" can both be
simultaneously true descriptions of the same product line.

**POSSIBLE HIDDEN MECHANISM (HYPOTHESIS):** The pairing system may function primarily as
an inventory/anti-theft and warranty-liability control — tracking which serialized part
is installed in which serialized device for Apple's own records — rather than as a
security or quality-assurance feature, with the True Tone/feature-disabling behavior
being a side effect used to make unregistered swaps visibly worse for the user, rather
than the check's actual purpose.

**WHAT WOULD HAVE TO BE VERIFIED:**
- Apple's own documentation on what registering a part through "Self Service Repair
  Store" actually updates in Apple's backend systems
- Whether the 2024 iOS 18 parts-pairing rollback was ever formally extended to (or
  explicitly excluded from) macOS/MacBook hardware
- Whether independent repair shops report the same True-Tone-disable behavior on
  MacBook Air/Pro models released after this March 2025 report

**WHAT WOULD MAKE THIS A BAD ARTICLE:** Framing it as a generic "right to repair is
hard" complaint instead of isolating the specific contradiction — a genuine, identical,
functioning part still failing an authenticity check.

---

## Card 4 — The vendor's risk disclosure contradicts its own product pitch

**SOURCE:** TechCrunch — "OpenAI says AI browsers may always be vulnerable to prompt
injection attacks"
**URL / SOURCE ID:** https://techcrunch.com/2025/12/22/openai-says-ai-browsers-may-always-be-vulnerable-to-prompt-injection-attacks/
**DATE:** December 22, 2025

**EXACT DISTURBANCE FRAGMENT:**
In OpenAI's own demonstrated scenario, an AI agent asked to draft an out-of-office reply
instead executed a hidden instruction embedded in an email and sent a resignation
message. OpenAI's stated position: "Prompt injection, much like scams and social
engineering on the web, is unlikely to ever be fully 'solved.'"

**LOCAL CONTEXT:** "Agent mode" products let an AI read a user's inbox or browse the web
and take actions (send, click, purchase) on the user's behalf, following natural-language
instructions found in whatever content it processes along the way.

**WHY THIS IS STRANGE:** The company shipping the product states, in its own security
materials, that the system's core design goal — "follow instructions found in the text
you're processing" — is structurally indistinguishable, from the system's point of view,
from an attack — "follow instructions an attacker planted in text you're processing" —
and that this isn't a bug awaiting a patch but a property they expect to persist
indefinitely.

**WHAT THE SOURCE ITSELF SAYS IS HAPPENING:** Agentic systems can't reliably tell the
user's actual intent apart from any other instruction-shaped text encountered while
completing a task, so hidden text in a webpage or email can redirect the agent's
real-world actions.

**WHAT THAT EXPLANATION MAY FAIL TO EXPLAIN:** It doesn't explain why these products are
simultaneously marketed as autonomous assistants trusted with sensitive, irreversible
actions (sending mail, making purchases) while the vendor concedes the core trust
boundary between "user instruction" and "arbitrary planted instruction" is unsolved and
may be unsolvable — the risk disclosure and the product pitch point in opposite
directions.

**POSSIBLE HIDDEN MECHANISM (HYPOTHESIS):** The "may never be fully solved" framing may
function less as a narrow technical prediction and more as pre-emptive liability
language — recasting an unbounded, product-specific failure mode as an inherent,
industry-wide property of the category ("like scams will always exist") rather than a
specific, addressable defect in a specific shipped product with specific capabilities.

**WHAT WOULD HAVE TO BE VERIFIED:**
- The full text of OpenAI's underlying security documentation/blog post beyond
  TechCrunch's summary of it
- Whether OpenAI actually restricts agent-mode from irreversible actions (sending,
  purchasing) pending stronger safeguards, or ships full capability regardless of the
  disclosed risk
- How competing agentic-browser products (Perplexity Comet, Google's equivalents)
  describe the same risk in their own security disclosures or terms of service

**WHAT WOULD MAKE THIS A BAD ARTICLE:** Treating "AI agents can be tricked by hidden
text" as the finding, rather than the sharper fact that the vendor itself frames an
unsolved trust-boundary problem as a permanent, acceptable feature of a shipped
consumer product handling real email and real transactions.
