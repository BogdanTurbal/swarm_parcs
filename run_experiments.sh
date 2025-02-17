#!/bin/bash

# === CONFIGURATION ===
LEADER_URL="tcp://10.166.0.2:4321"           # Replace with your leader node's IP/port
IMAGE="bogdanturbal/dlog-runner-py:latest"       # Your Docker image for the Dlog runner
OUTPUT_CSV="dlog_results_difficulty.csv"

# Use larger primes to increase the workload:
#  - 100003 is a 6-digit prime.
#  - 1000033 is a 7-digit prime.
PRIMES=(1003 100003 1000033 10000019)
WORKER_COUNTS=(1 2 3)
DIFFICULTY_TYPES=("low" "high")

# Prepare results file
echo "Prime,DifficultyType,Workers,SecretExponent,H,TimeSeconds" > "$OUTPUT_CSV"

# === MAIN LOOP ===
for p in "${PRIMES[@]}"; do
  for diff_type in "${DIFFICULTY_TYPES[@]}"; do
    # For low difficulty, use a small exponent (solution found early)
    # For high difficulty, use an exponent near the end of the search space.
    if [ "$diff_type" = "low" ]; then
      x=5
    else
      x=$(($p - 5))
    fi

    # Compute H = 2^x mod p (using g=2)
    h=$(python3 -c "print(pow(2, $x, $p))")

    for workers in "${WORKER_COUNTS[@]}"; do
      SERVICE_NAME="dlog_${p}_${diff_type}_${workers}"
      echo "Running: prime=$p, difficulty=$diff_type (x=$x), workers=$workers, h=$h"
      START_TIME=$(date +%s)

      # Create the Docker service with our parameters
      sudo docker service create \
        --network parcs \
        --restart-condition none \
        --env LEADER_URL="$LEADER_URL" \
        --name "$SERVICE_NAME" \
        --env P_PRIME="$p" \
        --env G="2" \
        --env H="$h" \
        --env P="$workers" \
        "$IMAGE" > /dev/null

      # Wait for the service to finish
      while :; do
        STATUS=$(sudo docker service ps "$SERVICE_NAME" --format "{{.CurrentState}}" | head -n1)
        if [[ $STATUS =~ ^(Shutdown|Complete|Failed).* ]]; then
          break
        fi
        sleep 2
      done

      END_TIME=$(date +%s)
      ELAPSED=$((END_TIME - START_TIME))

      # Log the results
      echo "$p,$diff_type,$workers,$x,$h,$ELAPSED" >> "$OUTPUT_CSV"
      sudo docker service rm "$SERVICE_NAME" > /dev/null

      echo "Done: prime=$p, difficulty=$diff_type, workers=$workers took $ELAPSED seconds"
      echo "---------------------------------------------"
    done
  done
done

echo "All experiments completed! Results saved in '$OUTPUT_CSV'."
