#!/bin/bash
# Concurrent Proxy Tests - Load and concurrency testing
# Usage: ./test_concurrent.sh [proxy_host] [proxy_port] [num_requests]


PROXY_HOST="${1:-localhost}"
PROXY_PORT="${2:-8080}"
NUM_REQUESTS="${3:-500}" # change the requests here default we'll keep 500 for now 
PROXY="$PROXY_HOST:$PROXY_PORT"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}$1${NC}"
}


print_header "Concurrent Proxy Tests"
echo "Proxy: $PROXY"
echo "Number of concurrent requests: $NUM_REQUESTS"


print_header "Test 1: Parallel Curl Requests"
echo "Starting $NUM_REQUESTS parallel requests..."

TEMP_DIR=$(mktemp -d)
START_TIME=$(date +%s.%N)


for i in $(seq 1 $NUM_REQUESTS); do
    (
        HTTP_CODE=$(curl -s -x "$PROXY" -o /dev/null -w "%{http_code}" http://httpbin.org/get 2>&1)
        echo "$HTTP_CODE" > "$TEMP_DIR/result_$i.txt"
    ) &
done


wait

END_TIME=$(date +%s.%N)
DURATION=$(echo "$END_TIME - $START_TIME" | bc)


SUCCESS=0
FAIL=0
for f in "$TEMP_DIR"/result_*.txt; do
    CODE=$(cat "$f")
    if [ "$CODE" = "200" ]; then
        ((SUCCESS++))
    else
        ((FAIL++))
    fi
done

rm -rf "$TEMP_DIR"

echo -e "${GREEN}Successful: $SUCCESS${NC}"
echo -e "${RED}Failed: $FAIL${NC}"
echo -e "${YELLOW}Total time: ${DURATION}s${NC}"
echo -e "${YELLOW}Requests/sec: $(echo "scale=2; $NUM_REQUESTS / $DURATION" | bc)${NC}"

if [ $SUCCESS -eq $NUM_REQUESTS ]; then
    echo -e "\n${GREEN}[PASS] All concurrent requests succeeded!${NC}"
else
    echo -e "\n${RED}[FAIL] Some concurrent requests failed${NC}"
fi


print_header "Test 2: Sequential Baseline (500 requests)"
START_TIME=$(date +%s.%N)

for i in $(seq 1 100); do
    curl -s -x "$PROXY" -o /dev/null http://httpbin.org/get
done

END_TIME=$(date +%s.%N)
SEQ_DURATION=$(echo "$END_TIME - $START_TIME" | bc)
echo -e "${YELLOW}Sequential time: ${SEQ_DURATION}s${NC}"



print_header "Concurrent Test Summary"
echo "Parallel requests handled: $NUM_REQUESTS"
echo "See results above for pass/fail status"

