#!/bin/bash
cd /workspace/t4l_validation
source /workspace/venv/bin/activate
export HF_HOME=/workspace/cache/hf
export TF_FORCE_GPU_ALLOW_GROWTH=true XLA_PYTHON_CLIENT_PREALLOCATE=false PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True TF_CPP_MIN_LOG_LEVEL=2
log() { echo "$(date -u +%FT%TZ) $*" >> runner.log; }
stop_pod() {
  log "stopping pod via GraphQL podStop"
  curl -s -m 30 -H "Content-Type: application/json" -H "Authorization: Bearer $RUNPOD_API_KEY" \
    -d '{"query":"mutation { podStop(input: {podId: \"'$RUNPOD_POD_ID'\"}) { id desiredStatus } }"}' https://api.runpod.io/graphql >> runner.log 2>&1
  echo >> runner.log
  sleep 30; log "still alive after podStop, trying runpodctl"; runpodctl stop pod $RUNPOD_POD_ID >> runner.log 2>&1
}
rm -f ALL_DONE COLLECTED jobs_done.txt
rm -f C_*_results.json stageB_results.json
log "runner3 start: 10 jobs, max 4 concurrent, retries on failure"
cat > job.sh <<'J'
#!/bin/bash
# usage: job.sh NAME RESULTFILE CMD...
name=$1; res=$2; shift 2
cd /workspace/t4l_validation
for try in 1 2 3; do
  timeout 18000 "$@" > $name.log 2>&1
  if [ -s "$res" ] && grep -q DONE $name.log; then echo "$(date -u +%FT%TZ) $name OK (try $try)" >> runner.log; exit 0; fi
  echo "$(date -u +%FT%TZ) $name failed try $try" >> runner.log; sleep 30
done
echo "$(date -u +%FT%TZ) $name GAVE UP" >> runner.log
J
chmod +x job.sh
{
for seed in 0 1 2; do for arm in off es1.0 on1.0; do
  echo "./job.sh C_${arm}_s${seed} C_${arm}_s${seed}_results.json python stageC.py --samples 16 --pop 20 --gens 3 --seeds $seed --arms $arm --tag C_${arm}_s${seed}"
done; done
echo "./job.sh stageB stageB_results.json python stageB.py 250 0 1 2"
} > jobs.txt
# stage B first (it is the validation of the state metric), then C jobs
{ tail -1 jobs.txt; head -9 jobs.txt; } > jobs_ordered.txt
cat jobs_ordered.txt | xargs -P 4 -I{} bash -c '{}'
log "all jobs finished"
touch ALL_DONE
for i in $(seq 1 180); do [ -f COLLECTED ] && break; sleep 60; done
log "collected-or-timeout; stopping"
stop_pod
