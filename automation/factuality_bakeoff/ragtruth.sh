#!/bin/bash
# Waits for FRANK to finish, then runs the RAGTruth implicit_true sanity probe on all
# three systems with unchanged adapters and the frozen default threshold.
B=/srv/data/cripminds-new-engine-v1/experiments/factuality-bakeoff
S=/srv/data/hermes/workspace/factuality-bakeoff/automation/factuality_bakeoff
export HF_HOME=$B/models/hf HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

until grep -aq "FRANK_ALL_DONE" "$B/logs/frank.log" 2>/dev/null; do sleep 30; done
echo "FRANK finished; starting RAGTruth probes"

cd "$B/work/lettuce"   && "$B/envs/lettuce/bin/python"   "$S/run_ragtruth.py" --system lettuce   --batch-size 8
cd "$B/work/factcg"    && "$B/envs/factcg/bin/python"    "$S/run_ragtruth.py" --system factcg    --batch-size 4
cd "$B/work/minicheck" && "$B/envs/minicheck/bin/python" "$S/run_ragtruth.py" --system minicheck --batch-size 8
echo RAGTRUTH_ALL_DONE
