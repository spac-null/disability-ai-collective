import collections
import json

E = "/srv/data/cripminds-new-engine-v1/experiments/evidence-to-draft-pilot-audit-v2/"
d = json.load(open(E + "C21_FAILURE_CLASSIFICATION_V2.json"))

cnt = collections.Counter()
for s in d["subjects"]:
    for c in s["complaints"]:
        cnt[c["classification"]] += 1
print("## classification counts:", cnt.most_common())
print("## subjects:", [s["subject_id"] for s in d["subjects"]])

for s in d["subjects"]:
    for c in s["complaints"]:
        if c["classification"] == "SCHEMA_FAILURE":
            continue
        ev = c.get("evidence") or {}
        print("\n" + "=" * 70)
        print("SUBJECT:", s["subject_id"])
        print("CLASS  :", c["classification"])
        print("RELATION:", ev.get("relation"), "TRIGGER:", repr(ev.get("trigger")), "FIELD:", ev.get("field"))
        print("TEXT   :", ev.get("text"))
        print("DECLARED_BASIS:", ev.get("declared_basis"))
        print("CITED_CARRYING:", ev.get("cited_facts_carrying_" + str(ev.get("relation"))))
        print("LEDGER_CARRYING:", ev.get("ledger_facts_carrying_" + str(ev.get("relation"))))
        print("WHY    :", c.get("why"))
