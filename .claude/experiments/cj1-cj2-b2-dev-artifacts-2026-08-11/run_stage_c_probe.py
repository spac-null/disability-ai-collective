import sys, json, time
sys.path.insert(0, ".")
import cj2_b2_stage_c_first_integrated_development_probe as probe

start = time.time()
results = probe.run_probe()
elapsed = time.time() - start

with open("full_results.json", "w") as f:
    json.dump(results, f, indent=2, default=str, ensure_ascii=False)

summary = {
    "calls_made": results["calls_made"],
    "stopped": results["stopped"],
    "stop_reason": results["stop_reason"],
    "elapsed_seconds": elapsed,
    "admitted_item_ids": results.get("admitted_item_ids", []),
    "per_item_summary": {
        iid: {
            "final_disposition": r.get("final_disposition"),
            "gate_status": (r.get("gate") or {}).get("status"),
            "gate_should_call_r1": (r.get("gate") or {}).get("should_call_r1"),
            "r1_valid": r.get("r1_valid"),
            "r2_valid_before_repair": r.get("r2_valid_before_repair"),
            "repair_triggered": r.get("repair_triggered"),
            "r2_valid_after_repair": r.get("r2_valid_after_repair"),
            "effective_verdict": r.get("effective_verdict"),
            "integration_failures": r.get("integration_failures"),
            "admission": r.get("admission"),
        }
        for iid, r in results["per_item"].items()
    },
}
with open("run_summary.json", "w") as f:
    json.dump(summary, f, indent=2, default=str, ensure_ascii=False)

print("DONE. elapsed:", elapsed, "calls_made:", results["calls_made"], "admitted:", results.get("admitted_item_ids"))
