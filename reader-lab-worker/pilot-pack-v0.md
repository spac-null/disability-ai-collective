# Reader Lab v0 — first pilot pack

Status: prepared, **seeded locally only** (verified end-to-end against
`wrangler dev --local`), **not sent to production**, no invitations sent.
`dataset_bucket: "pilot"` on every real item.

All content below is invented for this pilot. None of it is derived
from, or a disguised version of, any CJ-1/CJ-2/B2 research fixture
(H03/H05/H08/H09/H14/H17, De Hooch/Z, the Nature-cluster fresh-batch
items, or the cross-publisher evaluation batch). Domains used — a
library, a museum, a neighborhood newsletter, a community garden — share
no subject matter with any held-out or in-progress research material.

## Practice items (4, invented, `is_practice: true`)

These teach the four choices before real judgments start. Feedback is
shown after each one. They never enter the response dataset used for
anything beyond "did the reviewer complete practice."

1. **Source established.**
   Source: "The library extended its opening hours to 9pm starting in
   March."
   Sentence: "The library is now open later in the evening than it used
   to be."
   Correct: `source_established` — directly follows from what's stated.

2. **Reading of the source.**
   Source: "The museum removed the rope barriers around the sculpture
   garden last year."
   Sentence: "That change reads as an invitation to get closer to the
   work, physically and otherwise."
   Correct: `interpretive_only` — offered as a reading ("reads as"), not
   a claim about what actually happened or why.

3. **Adds something unestablished.**
   Source: "Enrollment in the after-school program dropped by a third
   this year."
   Sentence: "Parents stopped trusting the program after last year's
   staffing changes."
   Correct: `unsupported_factual_dependency` — depends on a specific,
   unstated cause (parents' trust, tied to a specific event) the source
   never establishes.

4. **Genuinely unsure.**
   Source: "Three of the five board members voted to delay the vote."
   Sentence: "The board was divided on the issue."
   Correct: `uncertain` — a split procedural vote doesn't necessarily
   mean substantive disagreement on the underlying issue; a reasonable
   reviewer could read it either way. Deliberately included so "I'm not
   sure" gets modeled as a legitimate, non-failing answer during
   practice, not only explained in prose.

## Real pilot items (4, invented, `dataset_bucket: "pilot"`)

Same four items go to both initial reviewers, independently.

1. Source: "The city repainted the crosswalk near the elementary school
   with high-visibility yellow paint in September."
   Sentence: "The crosswalk by the elementary school is now painted in a
   brighter color than before."

2. Source: "The café swapped its overhead fluorescent lights for warmer,
   dimmer bulbs last spring."
   Sentence: "The change reads as an attempt to make the space feel
   calmer."

3. Source: "The neighborhood newsletter has been mailed instead of
   emailed since January."
   Sentence: "Older residents asked for the change because they don't
   use email."

4. Source: "Attendance at the community garden's Saturday hours nearly
   doubled after the new bike rack went in."
   Sentence: "The bike rack made it easier for people to attend."

Item 4 is deliberately the hardest of the four — a real correlation
("after the bike rack went in") tightened into a specific causal
mechanism claim ("made it easier... to attend") that the source doesn't
actually establish. It's the closest analogue in plain, everyday
language to the exact failure pattern (`SEMANTIC_FACT_LAUNDERING`) B2's
own research has struggled with — a genuine test of whether an ordinary
reader's ear catches it, not a giveaway either direction. No "expected"
label is attached to any real item anywhere a reviewer, or this repo's
governance rules, would treat as ground truth — per the design doc,
majority vote is never auto-applied as truth even after both reviewers
respond.

## Seeding (already run once, locally, verified working)

The exact commands below were run against `wrangler dev --local` only.
Re-run against the real deployment (with `$BASE` and `$ADMIN_TOKEN` set
to production values) only after the deployment sequence in
`README.md` is complete and approved.

```bash
BASE=http://localhost:8787   # replace with https://lab.cripminds.com later
ADMIN_TOKEN=...              # your real ADMIN_TOKEN, never hardcoded

# 4 practice items
curl -s -X POST $BASE/admin/items -H "X-Admin-Token: $ADMIN_TOKEN" -H "Content-Type: application/json" -d '{
  "source_snapshot": "The library extended its opening hours to 9pm starting in March.",
  "candidate_sentence": "The library is now open later in the evening than it used to be.",
  "is_practice": true,
  "practice_explanation": "The source states this directly, so the sentence just reports it.",
  "practice_correct_answer": "source_established"
}'

curl -s -X POST $BASE/admin/items -H "X-Admin-Token: $ADMIN_TOKEN" -H "Content-Type: application/json" -d '{
  "source_snapshot": "The museum removed the rope barriers around the sculpture garden last year.",
  "candidate_sentence": "That change reads as an invitation to get closer to the work, physically and otherwise.",
  "is_practice": true,
  "practice_explanation": "This is offered as a reading of the change, not a claim about what actually happened or why.",
  "practice_correct_answer": "interpretive_only"
}'

curl -s -X POST $BASE/admin/items -H "X-Admin-Token: $ADMIN_TOKEN" -H "Content-Type: application/json" -d '{
  "source_snapshot": "Enrollment in the after-school program dropped by a third this year.",
  "candidate_sentence": "Parents stopped trusting the program after last year'"'"'s staffing changes.",
  "is_practice": true,
  "practice_explanation": "This depends on a specific cause the source never mentions.",
  "practice_correct_answer": "unsupported_factual_dependency"
}'

curl -s -X POST $BASE/admin/items -H "X-Admin-Token: $ADMIN_TOKEN" -H "Content-Type: application/json" -d '{
  "source_snapshot": "Three of the five board members voted to delay the vote.",
  "candidate_sentence": "The board was divided on the issue.",
  "is_practice": true,
  "practice_explanation": "A split procedural vote doesn'"'"'t necessarily mean real disagreement on the issue itself — a fair case for ‘not sure.’",
  "practice_correct_answer": "uncertain"
}'

# 4 real pilot items — save the returned item_id for each into $ITEM1..$ITEM4
curl -s -X POST $BASE/admin/items -H "X-Admin-Token: $ADMIN_TOKEN" -H "Content-Type: application/json" -d '{
  "source_snapshot": "The city repainted the crosswalk near the elementary school with high-visibility yellow paint in September.",
  "candidate_sentence": "The crosswalk by the elementary school is now painted in a brighter color than before.",
  "dataset_bucket": "pilot"
}'
curl -s -X POST $BASE/admin/items -H "X-Admin-Token: $ADMIN_TOKEN" -H "Content-Type: application/json" -d '{
  "source_snapshot": "The café swapped its overhead fluorescent lights for warmer, dimmer bulbs last spring.",
  "candidate_sentence": "The change reads as an attempt to make the space feel calmer.",
  "dataset_bucket": "pilot"
}'
curl -s -X POST $BASE/admin/items -H "X-Admin-Token: $ADMIN_TOKEN" -H "Content-Type: application/json" -d '{
  "source_snapshot": "The neighborhood newsletter has been mailed instead of emailed since January.",
  "candidate_sentence": "Older residents asked for the change because they don'"'"'t use email.",
  "dataset_bucket": "pilot"
}'
curl -s -X POST $BASE/admin/items -H "X-Admin-Token: $ADMIN_TOKEN" -H "Content-Type: application/json" -d '{
  "source_snapshot": "Attendance at the community garden'"'"'s Saturday hours nearly doubled after the new bike rack went in.",
  "candidate_sentence": "The bike rack made it easier for people to attend.",
  "dataset_bucket": "pilot"
}'

# 2 invitations
curl -s -X POST $BASE/admin/invitations -H "X-Admin-Token: $ADMIN_TOKEN" -H "Content-Type: application/json" -d '{}'
curl -s -X POST $BASE/admin/invitations -H "X-Admin-Token: $ADMIN_TOKEN" -H "Content-Type: application/json" -d '{}'

# assign the same 4 real items to both reviewers independently
curl -s -X POST $BASE/admin/assignments -H "X-Admin-Token: $ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d '{"reviewer_ids":["reader_A","reader_B"],"item_ids":["ITEM1","ITEM2","ITEM3","ITEM4"]}'
```

Verified locally: both reviewers see practice first, then exactly these
4 real items after completing practice, independently, with no
cross-visibility. See the production-readiness report for the exact
test run.
