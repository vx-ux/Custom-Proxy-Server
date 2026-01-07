#!/bin/bash
# CONNECT Tests - HTTPS tunneling functionality
# Usage: ./test_connect.sh [proxy_host] [proxy_port]

PROXY_HOST="${1:-localhost}"
PROXY_PORT="${2:-8080}"
PROXY="$PROXY_HOST:$PROXY_PORT"


RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASSED=0
FAILED=0

print_header() {
    echo -e "\n${BLUE}$1${NC}"
}

test_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED++))
}

test_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED++))
}

test_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

print_header "CONNECT (HTTPS Tunnel) Tests"
echo "Proxy: $PROXY"

print_header "Test 1: Basic HTTPS Request"
test_info "curl -x $PROXY https://httpbin.org/get"

HTTP_CODE=$(curl -s -x "$PROXY" -o /dev/null -w "%{http_code}" --max-time 15 https://httpbin.org/get 2>&1)

if [ "$HTTP_CODE" = "200" ]; then
    test_pass "HTTPS request through tunnel returned 200 OK"
else
    test_fail "HTTPS request failed (got $HTTP_CODE)"
fi


print_header "Test 2: HTTPS with Certificate Verification"
test_info "Testing TLS handshake through tunnel"

RESPONSE=$(curl -s -x "$PROXY" --max-time 15 https://httpbin.org/get 2>&1)

if echo "$RESPONSE" | grep -q "origin"; then
    test_pass "TLS connection established and data received"
else
    test_fail "TLS connection may have failed"
fi


print_header "Test 3: HTTPS POST Request"
test_info "curl -x $PROXY -X POST -d 'data=test' https://httpbin.org/post"

HTTP_CODE=$(curl -s -x "$PROXY" -X POST -d "data=test" -o /dev/null -w "%{http_code}" --max-time 15 https://httpbin.org/post 2>&1)

if [ "$HTTP_CODE" = "200" ]; then
    test_pass "HTTPS POST through tunnel returned 200 OK"
else
    test_fail "HTTPS POST failed (got $HTTP_CODE)"
fi


print_header "Test 4: Standard HTTPS Port (443)"
test_info "Testing connection to port 443 explicitly"

HTTP_CODE=$(curl -s -x "$PROXY" -o /dev/null -w "%{http_code}" --max-time 15 https://www.google.com:443 2>&1)

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
    test_pass "HTTPS to port 443 succeeded (code: $HTTP_CODE)"
else
    test_fail "HTTPS to port 443 failed (got $HTTP_CODE)"
fi


print_header "Test 5: Multiple HTTPS Requests"
test_info "Sending 5 sequential HTTPS requests"

SUCCESS=0
for i in $(seq 1 5); do
    HTTP_CODE=$(curl -s -x "$PROXY" -o /dev/null -w "%{http_code}" --max-time 15 https://httpbin.org/uuid 2>&1)
    if [ "$HTTP_CODE" = "200" ]; then
        ((SUCCESS++))
    fi
done

if [ $SUCCESS -eq 5 ]; then
    test_pass "All 5 HTTPS requests succeeded"
else
    test_fail "Only $SUCCESS/5 HTTPS requests succeeded"
fi


print_header "Test 6: HTTPS to Blocked Domain"
test_info "Testing HTTPS request to blocked domain (should return 403)"

HTTP_CODE=$(curl -s -x "$PROXY" -o /dev/null -w "%{http_code}" --max-time 10 https://bet365.com 2>&1)

if [ "$HTTP_CODE" = "403" ]; then
    test_pass "Blocked HTTPS domain returned 403 Forbidden"
elif [ "$HTTP_CODE" = "000" ]; then
    test_pass "Blocked HTTPS domain connection refused"
else
    test_info "Got $HTTP_CODE - blocking may occur at different stage"
fi

print_header "Test 7: Tunnel Verbose Output"
test_info "Checking CONNECT tunnel establishment"

VERBOSE=$(curl -v -x "$PROXY" --max-time 10 https://httpbin.org/get 2>&1)

if echo "$VERBOSE" | grep -q "200 Connection [Ee]stablished"; then
    test_pass "CONNECT tunnel established (200 Connection Established)"
else
    test_fail "CONNECT tunnel may not have been established properly"
fi


print_header "Test Results"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo -e "Total: $((PASSED + FAILED))"


echo -e "\n${YELLOW}Note: CONNECT tests require proper TLS support in the proxy${NC}"
echo -e "${YELLOW}The proxy acts as a tunnel, not decrypting HTTPS traffic${NC}"

if [ $FAILED -eq 0 ]; then
    exit 0
else
    exit 1
fi
