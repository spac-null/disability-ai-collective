#!/bin/bash
B=/srv/data/cripminds-new-engine-v1/experiments/factuality-bakeoff
S=/srv/data/hermes/workspace/factuality-bakeoff/automation/factuality_bakeoff
export HF_HOME=$B/models/hf HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
cd "$B/work/factcg" && "$B/envs/factcg/bin/python" "$S/run_frank.py" --system factcg --batch-size 8
cd "$B/work/minicheck" && "$B/envs/minicheck/bin/python" "$S/run_frank.py" --system minicheck --batch-size 16
echo FRANK_ALL_DONE
