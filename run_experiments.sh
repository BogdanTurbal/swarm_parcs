#!/bin/bash

# === CONFIGURATION ===
LEADER_URL="tcp://10.166.0.2:4321"   # Replace with your leader node's IP/port
IMAGE="bogdanturbal/dlog-runner-py:latest"  # Your Docker image for the Dlog runner
OUTPUT_CSV="dlog_results_difficulty.csv"

# Define test cases.
# Each test case is defined as: 
#   "p g h secret_x"
# where:
#   p        : prime modulus
#   g        : generator
#   h        : computed value (g^x mod p)
#   secret_x : secret exponent (for verification)
TEST_CASES=(
  "424696087 152308577 229665180 362526097"
  "785547064227242117 395930555913973079 634575353534676382 381290180012095599"
  "187772725411025400773818883191297509487 53872662813989128956274819320163570448 17622448763373217681658169890716589262 106249747126031605916572071274421869904"
  "58429876151104607672206470056137054041509213438409986134240349490726719437943 39115942615287892599922701905880885999696662670347021841975174455429119950104 29150570947678462061948510956609600978487578458327684533223186653948301443274 19662041736183637604660776643118915163994991017195071982093409852348748249408"
  "3726962008226664565866988701944063196211742771454905355643210192794354542897235700534707461006104922000250870307299005926710277902287315905492478146025197 3510574545117828513242230394623197892469750708670262754288734160276684614213237767587229577541870779587177180440391740868264331077982319040441189469155210 1148049206280271687709304872510614428391599768513093780799094847744482738361373837179741222118687614419488340636366802246134544411131636840934836830308105 932526061569134109156466905753766883753268696268525484372474845380825703413243102555672339644749103579115355678982221871430941029231042349578544860002747"
)

WORKER_COUNTS=(2 3)

# Prepare the results CSV file with header.
echo "Test,Prime,G,SecretExponent,H,Workers,TimeSeconds" > "$OUTPUT_CSV"

test_index=1
for test_case in "${TEST_CASES[@]}"; do
  # Read the test case parameters into variables.
  read -r p g h secret_x <<< "$test_case"
  
  for workers in "${WORKER_COUNTS[@]}"; do
    SERVICE_NAME="dlog_test${test_index}_${workers}"
    echo "Running Test $test_index: p=$p, g=$g, secret_x=$secret_x, h=$h, workers=$workers"
    START_TIME=$(date +%s)
    
    # Create the Docker service with the test parameters.
    sudo docker service create \
      --network parcs \
      --restart-condition none \
      --env LEADER_URL="$LEADER_URL" \
      --name "$SERVICE_NAME" \
      --env P_PRIME="$p" \
      --env G="$g" \
      --env H="$h" \
      --env P="$workers" \
      "$IMAGE" > /dev/null

    # Wait until the service finishes.
    while :; do
      STATUS=$(sudo docker service ps "$SERVICE_NAME" --format "{{.CurrentState}}" | head -n1)
      if [[ $STATUS =~ ^(Shutdown|Complete|Failed).* ]]; then
        break
      fi
      sleep 2
    done
    
    END_TIME=$(date +%s)
    ELAPSED=$((END_TIME - START_TIME))
    
    # Log the results.
    echo "$test_index,$p,$g,$secret_x,$h,$workers,$ELAPSED" >> "$OUTPUT_CSV"
    sudo docker service rm "$SERVICE_NAME" > /dev/null
    
    echo "Done Test $test_index: workers=$workers took $ELAPSED seconds"
    echo "---------------------------------------------"
  done
  test_index=$((test_index + 1))
done

echo "All experiments completed! Results saved in '$OUTPUT_CSV'."
