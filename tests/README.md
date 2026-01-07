# Proxy Server Test Suite

Comprehensive test suite for verifying all proxy server functionality.

## Prerequisites

- `curl` must be installed
- `bash` shell (use WSL or Git Bash on Windows)
- `nc` (netcat) for malformed request tests
- Proxy server running (default: `localhost:8080`)

## Test Scripts

| Script | Description |
|--------|-------------|
| `run_all_tests.sh` | **Master runner** - executes all test suites |
| `test_basic.sh` | Basic HTTP forwarding (GET, POST, headers, redirects) |
| `test_blocking.sh` | Domain blocking and filtering tests |
| `test_connect.sh` | HTTPS CONNECT tunneling tests |
| `test_concurrent.sh` | Parallel requests and load testing |
| `test_malformed.sh` | Malformed request error handling |

## Quick Start

### 1. Start the proxy server:
```bash
cd /path/to/proxy-project
python run.py --port 8080
```

### 2. Run all tests:
```bash
cd tests
bash run_all_tests.sh localhost 8080
```

### 3. Or run individual test suites:
```bash
bash test_basic.sh localhost 8080
bash test_blocking.sh localhost 8080
bash test_connect.sh localhost 8080
bash test_concurrent.sh localhost 8080 500
bash test_malformed.sh localhost 8080
```

## Test Categories

### 1. Basic HTTP Tests (`test_basic.sh`)
- Simple HTTP GET requests
- HTTP POST with form data and JSON
- Custom header forwarding
- Query parameter handling
- Redirect following
- Large response handling

### 2. Domain Blocking Tests (`test_blocking.sh`)
- Wildcard domain blocking (`*.doubleclick.net`)
- Exact domain blocking (`bet365.com`)
- Case-insensitive matching
- HTTPS domain blocking
- Subdomain wildcard verification
- 403 response body verification

### 3. CONNECT Tests (`test_connect.sh`)
- Basic HTTPS through tunnel
- TLS handshake verification
- HTTPS POST requests
- Multiple HTTPS requests
- Blocked HTTPS domains
- Tunnel establishment check

### 4. Concurrent Tests (`test_concurrent.sh`)
- Parallel curl requests (configurable, default: 500)
- Sequential vs parallel comparison
- Requests per second calculation
- Success rate tracking

### 5. Malformed Request Tests (`test_malformed.sh`)
- Empty requests
- Invalid HTTP methods
- Missing Host headers
- Very long URIs
- Binary garbage data
- Incomplete requests
- Timeout handling

## Expected Results

| Test Suite | Pass Criteria |
|------------|---------------|
| Basic HTTP | All 10 tests pass |
| Blocking | Blocked domains return 403 |
| CONNECT | HTTPS works through tunnel |
| Concurrent | >95% success rate |
| Malformed | Server handles gracefully (400/408/close) |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Connection refused | Make sure proxy is running: `python run.py` |
| Timeout errors | Increase `--max-time` in curl commands |
| Blocking not working | Verify `config/blocked_domains.txt` entries |
| HTTPS failures | Check CONNECT handler in `forwarder.py` |
| nc not found | Install netcat: `apt install netcat` (Linux) |

## Sample Log Output

See `../docs/SAMPLE_LOGS.md` for example log entries produced during tests.
