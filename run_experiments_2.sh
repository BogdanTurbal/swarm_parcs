#!/bin/bash

# === CONFIGURATION ===
LEADER_URL="tcp://10.166.0.2:4321"       # Replace with your leader node's IP/port
IMAGE="bogdanturbal/ecdlog-runner-py:latest" # Your Docker image for the ECDLP runner
OUTPUT_CSV="ecdlog_results_random.csv"

# Fixed elliptic curve parameters for our toy curve:
P_PRIME=1000003       # A moderately large prime (7-digit)
CURVE_A=1
CURVE_B=1
P_X=0
P_Y=1

# Baseline search space (this value will be scaled by difficulty)
BASE=1000000

# Define four difficulty levels via multipliers:
declare -A multipliers
multipliers=( ["very_easy"]=1 ["easy"]=10 ["medium"]=100 ["hard"]=1000 )

WORKER_COUNTS=(2 3)

# Prepare the results CSV file
echo "Difficulty,Workers,SECRET_K,SEARCH_SPACE,TimeSeconds" > "$OUTPUT_CSV"

for diff in "${!multipliers[@]}"; do
    multiplier=${multipliers[$diff]}
    SEARCH_SPACE=$(( BASE * multiplier ))
    # Randomly generate SECRET_K in [0, SEARCH_SPACE)
    SECRET_K=$(python3 -c "import random; print(random.randint(0, $SEARCH_SPACE - 1))")
    
    for workers in "${WORKER_COUNTS[@]}"; do
        SERVICE_NAME="ecdlog_${diff}_${workers}"
        echo "Running ECDLP: difficulty=$diff, workers=$workers, SECRET_K=$SECRET_K, SEARCH_SPACE=$SEARCH_SPACE"
        START_TIME=$(date +%s)
    
        sudo docker service create \
          --network parcs \
          --restart-condition none \
          --env LEADER_URL="$LEADER_URL" \
          --name "$SERVICE_NAME" \
          --env P_PRIME="$P_PRIME" \
          --env CURVE_A="$CURVE_A" \
          --env CURVE_B="$CURVE_B" \
          --env P_X="$P_X" \
          --env P_Y="$P_Y" \
          --env SECRET_K="$SECRET_K" \
          --env SEARCH_SPACE="$SEARCH_SPACE" \
          --env WORKERS="$workers" \
          "$IMAGE" > /dev/null
    
        # Wait until the service finishes (tasks enter Shutdown/Complete/Failed)
        while :; do
            STATUS=$(sudo docker service ps "$SERVICE_NAME" --format "{{.CurrentState}}" | head -n1)
            if [[ $STATUS =~ ^(Shutdown|Complete|Failed).* ]]; then
                break
            fi
            sleep 1
        done
    
        END_TIME=$(date +%s)
        ELAPSED=$((END_TIME - START_TIME))
        echo "$diff,$workers,$SECRET_K,$SEARCH_SPACE,$ELAPSED" >> "$OUTPUT_CSV"
        docker service rm "$SERVICE_NAME" > /dev/null
    
        echo "Done: difficulty=$diff, workers=$workers took $ELAPSED seconds"
        echo "---------------------------------------------"
    done
done

echo "All experiments completed! Results saved in '$OUTPUT_CSV'."
