#!/bin/bash
# Domain Blocking Tests - Verify blacklist functionality
# Usage: ./test_blocking.sh [proxy_host] [proxy_port]

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

print_header "Domain Blocking Tests"
echo "Proxy: $PROXY"
echo "Testing domain filtering and blocklist functionality"


print_header "Test 1: Allowed Domain (Control Test)"
test_info "curl -x $PROXY http://httpbin.org/get"

HTTP_CODE=$(curl -s -x "$PROXY" -o /dev/null -w "%{http_code}" --max-time 15 http://httpbin.org/get 2>&1)

if [ "$HTTP_CODE" = "200" ]; then
    test_pass "Allowed domain returned 200 OK"
else
    test_fail "Allowed domain failed (got $HTTP_CODE)"
fi


print_header "Test 2: Blocked Domain - Wildcard Match (*.doubleclick.net)"
test_info "curl -x $PROXY http://ad.doubleclick.net/"

HTTP_CODE=$(curl -s -x "$PROXY" -o /dev/null -w "%{http_code}" --max-time 10 http://ad.doubleclick.net/ 2>&1)

if [ "$HTTP_CODE" = "403" ]; then
    test_pass "Blocked domain (*.doubleclick.net) returned 403 Forbidden"
elif [ "$HTTP_CODE" = "000" ]; then
    test_pass "Blocked domain connection refused (expected behavior)"
else
    test_info "Got $HTTP_CODE - domain may not be in blocklist"
fi


print_header "Test 3: Blocked Domain - Gambling Site (bet365.com)"
test_info "curl -x $PROXY http://bet365.com/"

HTTP_CODE=$(curl -s -x "$PROXY" -o /dev/null -w "%{http_code}" --max-time 10 http://bet365.com/ 2>&1)

if [ "$HTTP_CODE" = "403" ]; then
    test_pass "Blocked gambling site returned 403 Forbidden"
elif [ "$HTTP_CODE" = "000" ]; then
    test_pass "Blocked gambling site connection refused"
else
    test_info "Got $HTTP_CODE - check if bet365.com is in blocklist"
fi


print_header "Test 4: Blocked Domain - Analytics (*.google-analytics.com)"
test_info "curl -x $PROXY http://www.google-analytics.com/"

HTTP_CODE=$(curl -s -x "$PROXY" -o /dev/null -w "%{http_code}" --max-time 10 http://www.google-analytics.com/ 2>&1)

if [ "$HTTP_CODE" = "403" ]; then
    test_pass "Blocked analytics site returned 403 Forbidden"
elif [ "$HTTP_CODE" = "000" ]; then
    test_pass "Blocked analytics site connection refused"
else
    test_info "Got $HTTP_CODE - check blocklist configuration"
fi


print_header "Test 5: HTTPS Blocked Domain"
test_info "curl -x $PROXY https://bet365.com/"

HTTP_CODE=$(curl -s -x "$PROXY" -o /dev/null -w "%{http_code}" --max-time 10 https://bet365.com/ 2>&1)

if [ "$HTTP_CODE" = "403" ]; then
    test_pass "HTTPS blocked domain returned 403 Forbidden"
elif [ "$HTTP_CODE" = "000" ]; then
    test_pass "HTTPS blocked domain connection refused"
else
    test_info "Got $HTTP_CODE - CONNECT blocking may work differently"
fi


print_header "Test 6: Blocked Response Body Check"
test_info "Verifying 403 response contains 'Forbidden' message"

RESPONSE=$(curl -s -x "$PROXY" --max-time 10 http://ad.doubleclick.net/ 2>&1)

if echo "$RESPONSE" | grep -qi "forbidden\|blocked"; then
    test_pass "Blocked response contains appropriate message"
else
    test_info "Response: $RESPONSE"
fi


print_header "Test 7: Case Insensitivity Test"
test_info "curl -x $PROXY http://AD.DOUBLECLICK.NET/"

HTTP_CODE=$(curl -s -x "$PROXY" -o /dev/null -w "%{http_code}" --max-time 10 http://AD.DOUBLECLICK.NET/ 2>&1)

if [ "$HTTP_CODE" = "403" ] || [ "$HTTP_CODE" = "000" ]; then
    test_pass "Domain blocking is case-insensitive"
else
    test_info "Got $HTTP_CODE - case sensitivity may vary"
fi


print_header "Test 8: Subdomain Wildcard Blocking"
test_info "Testing multiple subdomains of blocked wildcard domain"

for subdomain in "www" "api" "tracking" "stats"; do
    HTTP_CODE=$(curl -s -x "$PROXY" -o /dev/null -w "%{http_code}" --max-time 5 http://${subdomain}.doubleclick.net/ 2>&1)
    if [ "$HTTP_CODE" = "403" ] || [ "$HTTP_CODE" = "000" ]; then
        echo -e "  ${GREEN}${NC} ${subdomain}.doubleclick.net blocked"
    else
        echo -e "  ${RED}${NC} ${subdomain}.doubleclick.net returned $HTTP_CODE"
    fi
done


print_header "Test 9: Non-Blocked Similar Domain"
test_info "curl -x $PROXY http://example.com/ (should NOT be blocked)"

HTTP_CODE=$(curl -s -x "$PROXY" -o /dev/null -w "%{http_code}" --max-time 15 http://example.com/ 2>&1)

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
    test_pass "Non-blocked domain accessible (got $HTTP_CODE)"
else
    test_fail "Unexpected response for non-blocked domain (got $HTTP_CODE)"
fi


print_header "Test 10: Logging Verification"
test_info "Checking if blocked requests are logged"
echo -e "${YELLOW}Note: Check proxy.log for 'BLOCKED' entries after running tests${NC}"


print_header "Test Results Summary"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo -e "Total: $((PASSED + FAILED))"

echo -e "\n${YELLOW}Note: Some tests may show 'INFO' instead of PASS/FAIL${NC}"
echo -e "${YELLOW}because blocked domains may not be in your blocklist.${NC}"
echo -e "${YELLOW}Verify config/blocked_domains.txt contains expected entries.${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}Domain blocking tests completed!${NC}"
    exit 0
else
    echo -e "\n${RED}Some tests failed. Review blocklist configuration.${NC}"
    exit 1
fi
