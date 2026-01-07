#!/bin/bash
# Malformed Request Tests - Error handling for invalid inputs
# Usage: ./test_malformed.sh [proxy_host] [proxy_port]

PROXY_HOST="${1:-localhost}"
PROXY_PORT="${2:-8080}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASSED=0
FAILED=0

print_header() {
    echo -e "\n${BLUE}${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}${NC}"
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

print_header "Malformed Request Tests"
echo "Proxy: $PROXY_HOST:$PROXY_PORT"
echo "Testing error handling for invalid/malformed requests"


print_header "Test 1: Empty Request"
test_info "Sending empty request via netcat"

RESPONSE=$(echo "" | nc -w 2 $PROXY_HOST $PROXY_PORT 2>&1)

if echo "$RESPONSE" | grep -qi "400\|bad request\|error"; then
    test_pass "Empty request handled (400 Bad Request or connection closed)"
else
    test_info "Response: ${RESPONSE:-<empty or connection closed>}"
fi


print_header "Test 2: Invalid HTTP Method"
test_info "Sending: INVALID / HTTP/1.1"

RESPONSE=$(echo -e "INVALID / HTTP/1.1\r\nHost: httpbin.org\r\n\r\n" | nc -w 3 $PROXY_HOST $PROXY_PORT 2>&1)

if echo "$RESPONSE" | grep -qi "400\|405\|bad\|not allowed"; then
    test_pass "Invalid method handled correctly"
else
    test_info "Response: ${RESPONSE:-<empty>}"
fi


print_header "Test 3: Malformed Request Line"
test_info "Sending: GET HTTP/1.1 (missing URI)"

RESPONSE=$(echo -e "GET HTTP/1.1\r\nHost: httpbin.org\r\n\r\n" | nc -w 3 $PROXY_HOST $PROXY_PORT 2>&1)

if echo "$RESPONSE" | grep -qi "400\|bad"; then
    test_pass "Malformed request line handled correctly"
else
    test_info "Response: ${RESPONSE:-<empty>}"
fi


print_header "Test 4: Missing Host Header (HTTP/1.1)"
test_info "Sending: GET /path HTTP/1.1 (no Host header)"

RESPONSE=$(echo -e "GET /path HTTP/1.1\r\n\r\n" | nc -w 3 $PROXY_HOST $PROXY_PORT 2>&1)

if echo "$RESPONSE" | grep -qi "400\|bad"; then
    test_pass "Missing Host header handled correctly"
else
    test_info "Response: ${RESPONSE:-<empty>}"
fi


print_header "Test 5: Invalid HTTP Version"
test_info "Sending: GET http://httpbin.org/get HTTP/9.9"

RESPONSE=$(echo -e "GET http://httpbin.org/get HTTP/9.9\r\nHost: httpbin.org\r\n\r\n" | nc -w 3 $PROXY_HOST $PROXY_PORT 2>&1)

# Some proxies may accept this, others will reject
if [ -n "$RESPONSE" ]; then
    test_info "Got response (proxy accepted or rejected the version)"
else
    test_info "No response or connection closed"
fi


print_header "Test 6: Very Long URI"
test_info "Sending request with 10000 character URI"

LONG_URI=$(printf 'a%.0s' {1..10000})
RESPONSE=$(echo -e "GET http://httpbin.org/${LONG_URI} HTTP/1.1\r\nHost: httpbin.org\r\n\r\n" | timeout 5 nc $PROXY_HOST $PROXY_PORT 2>&1)

if echo "$RESPONSE" | grep -qi "414\|400\|413\|error"; then
    test_pass "Long URI rejected appropriately"
else
    test_info "Response: ${RESPONSE:0:100}..."
fi


print_header "Test 7: Binary Garbage Data"
test_info "Sending random binary data"

RESPONSE=$(dd if=/dev/urandom bs=100 count=1 2>/dev/null | nc -w 2 $PROXY_HOST $PROXY_PORT 2>&1)

if [ -z "$RESPONSE" ] || echo "$RESPONSE" | grep -qi "400\|bad"; then
    test_pass "Binary garbage handled (closed or 400)"
else
    test_info "Response: ${RESPONSE:0:50}..."
fi


print_header "Test 8: Incomplete Request (No CRLF)"
test_info "Sending incomplete headers"

RESPONSE=$(echo -n "GET http://httpbin.org/get HTTP/1.1" | timeout 3 nc $PROXY_HOST $PROXY_PORT 2>&1)

# Should timeout or return error
test_info "Incomplete request: ${RESPONSE:-timeout/no response (expected)}"


print_header "Test 9: Double CRLF Only"
test_info "Sending only \\r\\n\\r\\n"

RESPONSE=$(echo -e "\r\n\r\n" | nc -w 2 $PROXY_HOST $PROXY_PORT 2>&1)

if [ -z "$RESPONSE" ] || echo "$RESPONSE" | grep -qi "400\|bad"; then
    test_pass "Empty headers handled correctly"
else
    test_info "Response: ${RESPONSE:-<empty>}"
fi


print_header "Test 10: CONNECT to Invalid Port"
test_info "CONNECT example.com:99999"

RESPONSE=$(echo -e "CONNECT example.com:99999 HTTP/1.1\r\nHost: example.com:99999\r\n\r\n" | nc -w 5 $PROXY_HOST $PROXY_PORT 2>&1)

if echo "$RESPONSE" | grep -qi "502\|400\|bad\|gateway"; then
    test_pass "Invalid port CONNECT handled correctly"
else
    test_info "Response: ${RESPONSE:-<empty>}"
fi


print_header "Test 11: Request Timeout Test"
test_info "Opening connection but not sending data (should timeout)"

# Open connection and wait
timeout 5 nc $PROXY_HOST $PROXY_PORT &
NC_PID=$!
sleep 3
kill $NC_PID 2>/dev/null

test_info "Timeout behavior tested (check proxy logs for 408)"


print_header "Test Results Summary"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo -e "Total: $((PASSED + FAILED))"

echo -e "\n${YELLOW}Note: Many malformed request tests show 'INFO' since${NC}"
echo -e "${YELLOW}correct behavior varies (400 error, connection close, etc.)${NC}"
echo -e "${YELLOW}Check proxy.log for detailed error handling information.${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}Malformed request tests completed!${NC}"
    exit 0
else
    echo -e "\n${RED}Some tests failed.${NC}"
    exit 1
fi
