# Proxy Server Test Suite

Test scripts for verifying proxy server functionality.

## Prerequisites

- `curl` installed
- `bash` shell (WSL or Git Bash on Windows)
- `nc` (netcat) for malformed request tests
- Proxy server running (default: `localhost:8080`)

## Test Scripts

| Script | Description |
|--------|-------------|
| `test_basic.sh` | Basic HTTP forwarding (GET, POST, headers) |
| `test_blocking.sh` | Domain blocking and filtering tests |
| `test_connect.sh` | HTTPS CONNECT tunneling tests |
| `test_concurrent.sh` | Parallel requests and load testing |
| `test_malformed.sh` | Malformed request error handling |

## Usage

### Start the proxy server:
```bash
python run.py --port 8080
```

### Run test scripts:
```bash
cd tests
bash test_basic.sh localhost 8080
bash test_blocking.sh localhost 8080
bash test_connect.sh localhost 8080
bash test_concurrent.sh localhost 8080 500
bash test_malformed.sh localhost 8080
```

## Test Categories

### Basic HTTP (`test_basic.sh`)
- HTTP GET/POST requests
- Custom header forwarding
- Query parameters
- Large response handling

### Domain Blocking (`test_blocking.sh`)
- Wildcard blocking (`*.doubleclick.net`)
- Exact domain blocking
- Case-insensitive matching
- HTTPS domain blocking

### CONNECT Tests (`test_connect.sh`)
- HTTPS tunnel establishment
- TLS handshake verification
- Blocked HTTPS domains

### Concurrent Tests (`test_concurrent.sh`)
- Parallel requests (default: 500)
- Success rate tracking

### Malformed Requests (`test_malformed.sh`)
- Empty/invalid requests
- Missing headers
- Timeout handling

## Expected Results

| Test Suite | Pass Criteria |
|------------|---------------|
| Basic HTTP | All tests pass |
| Blocking | 403 for blocked domains |
| CONNECT | HTTPS works through tunnel |
| Concurrent | >95% success rate |
| Malformed | Graceful error handling |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Connection refused | Start proxy: `python run.py` |
| Timeout errors | Increase `--max-time` in curl |
| Blocking not working | Check `config/blocked_domains.txt` |
| nc not found | Install netcat |
