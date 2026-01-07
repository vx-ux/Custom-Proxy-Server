#!/bin/bash
# Basic HTTP Proxy Tests - Forwarding and error handling
# Usage: ./test_basic.sh [proxy_host] [proxy_port]

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

print_header "Basic HTTP Proxy Tests"
echo "Proxy: $PROXY"
echo "Testing HTTP request forwarding and error handling"


print_header "Test 1: Simple HTTP GET Request"
test_info "curl -x $PROXY http://httpbin.org/get"

RESPONSE=$(curl -s -x "$PROXY" --max-time 15 http://httpbin.org/get 2>&1)
HTTP_CODE=$(curl -s -x "$PROXY" -o /dev/null -w "%{http_code}" --max-time 15 http://httpbin.org/get 2>&1)

if [ "$HTTP_CODE" = "200" ]; then
    test_pass "HTTP GET returned 200 OK"
else
    test_fail "HTTP GET failed (got $HTTP_CODE)"
fi


print_header "Test 2: HTTP GET with Query Parameters"
test_info "curl -x $PROXY 'http://httpbin.org/get?foo=bar&test=123'"

HTTP_CODE=$(curl -s -x "$PROXY" -o /dev/null -w "%{http_code}" --max-time 15 "http://httpbin.org/get?foo=bar&test=123" 2>&1)

if [ "$HTTP_CODE" = "200" ]; then
    test_pass "HTTP GET with query params returned 200 OK"
else
    test_fail "HTTP GET with query params failed (got $HTTP_CODE)"
fi


print_header "Test 3: HTTP POST Request"
test_info "curl -x $PROXY -X POST -d 'name=test&value=123' http://httpbin.org/post"

HTTP_CODE=$(curl -s -x "$PROXY" -X POST -d "name=test&value=123" -o /dev/null -w "%{http_code}" --max-time 15 http://httpbin.org/post 2>&1)

if [ "$HTTP_CODE" = "200" ]; then
    test_pass "HTTP POST returned 200 OK"
else
    test_fail "HTTP POST failed (got $HTTP_CODE)"
fi


print_header "Test 4: HTTP POST with JSON Body"
test_info "curl -x $PROXY -X POST -H 'Content-Type: application/json' -d '{\"key\":\"value\"}' http://httpbin.org/post"

HTTP_CODE=$(curl -s -x "$PROXY" -X POST \
    -H "Content-Type: application/json" \
    -d '{"key":"value"}' \
    -o /dev/null -w "%{http_code}" --max-time 15 http://httpbin.org/post 2>&1)

if [ "$HTTP_CODE" = "200" ]; then
    test_pass "HTTP POST with JSON returned 200 OK"
else
    test_fail "HTTP POST with JSON failed (got $HTTP_CODE)"
fi


print_header "Test 5: HTTP HEAD Request"
test_info "curl -x $PROXY -I http://httpbin.org/get"

HTTP_CODE=$(curl -s -x "$PROXY" -I -o /dev/null -w "%{http_code}" --max-time 15 http://httpbin.org/get 2>&1)

if [ "$HTTP_CODE" = "200" ]; then
    test_pass "HTTP HEAD returned 200 OK"
else
    test_fail "HTTP HEAD failed (got $HTTP_CODE)"
fi


print_header "Test 6: HTTP Request with Custom Headers"
test_info "curl -x $PROXY -H 'X-Custom-Header: TestValue' http://httpbin.org/headers"

RESPONSE=$(curl -s -x "$PROXY" -H "X-Custom-Header: TestValue" --max-time 15 http://httpbin.org/headers 2>&1)

if echo "$RESPONSE" | grep -q "X-Custom-Header"; then
    test_pass "Custom header was forwarded correctly"
else
    test_fail "Custom header was not forwarded"
fi


print_header "Test 7: Multiple Sequential Requests"
test_info "Sending 10 sequential HTTP requests"

SUCCESS=0
for i in $(seq 1 10); do
    HTTP_CODE=$(curl -s -x "$PROXY" -o /dev/null -w "%{http_code}" --max-time 15 http://httpbin.org/uuid 2>&1)
    if [ "$HTTP_CODE" = "200" ]; then
        ((SUCCESS++))
    fi
done

if [ $SUCCESS -eq 10 ]; then
    test_pass "All 10 sequential requests succeeded"
else
    test_fail "Only $SUCCESS/10 requests succeeded"
fi


print_header "Test 8: Response Content Verification"
test_info "Verifying response body content"

RESPONSE=$(curl -s -x "$PROXY" --max-time 15 http://httpbin.org/ip 2>&1)

if echo "$RESPONSE" | grep -q "origin"; then
    test_pass "Response body contains expected content"
else
    test_fail "Response body does not contain expected content"
fi


print_header "Test 9: Large Response Handling"
test_info "curl -x $PROXY http://httpbin.org/bytes/10000"

HTTP_CODE=$(curl -s -x "$PROXY" -o /dev/null -w "%{http_code}" --max-time 30 http://httpbin.org/bytes/10000 2>&1)

if [ "$HTTP_CODE" = "200" ]; then
    test_pass "Large response (10KB) handled correctly"
else
    test_fail "Large response failed (got $HTTP_CODE)"
fi

print_header "Test Results Summary"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo -e "Total: $((PASSED + FAILED))"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}All basic HTTP tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}Some tests failed. Check proxy server logs for details.${NC}"
    exit 1
fi
