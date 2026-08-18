import sys, json
sys.path.insert(0, 'automation')
from orchestrator.sofa_discovery_shadow_form1_1 import build_form1_1_packet, build_form1_1_writer_prompt

CASE = ".claude/experiments/sofa-real-ab-1-2026-08-18"
commission = json.load(open(f"{CASE}/commission-brief.json"))
evidence = json.load(open(f"{CASE}/evidence-packet.json"))
source_text = open(f"{CASE}/source-snapshot.txt").read()
evidence["source_text"] = source_text

packet = build_form1_1_packet(commission, evidence)
print("PACKET OK, keys:", list(packet.keys()))
print("correction_material count:", len(packet["correction_material"]))
print("Hasegawa decision:", packet["hasegawa_decision"][:80])
system, user = build_form1_1_writer_prompt(packet, source_text)
checks = [
    "Hasegawa", "the festival says", "the festival argues", "the festival allows",
    "the festival admits", "the festival's own account", "center of what the festival",
    "Zen", "Circuit", "hidden_mechanism",
]
for bad in checks:
    print(repr(bad), "-> in user:", bad in user, "| in system:", bad in system)
print()
print("=== SYSTEM ===")
print(system)
