# Proxy Server Test Suite

This folder contains test scripts for verifying the proxy server functionality.

## Prerequisites

- `curl` must be installed
- `bash` shell (use WSL on Windows)
- Proxy server running (default: `localhost:8080`)

## Test Scripts

| Script | Description |
|--------|-------------|
| `test_concurrent.sh` | Parallel requests and load testing |
| `test_connect.sh` | HTTPS CONNECT tunneling tests |

## Usage

### Start the proxy server first:
```bash
cd /path/to/proxy-project
python run.py --port 8080
```

### Run individual test suites:
```bash
# HTTPS/CONNECT tests
bash test_connect.sh localhost 8080

# Concurrent/load tests
bash test_concurrent.sh localhost 8080 100
```

## Test Categories

### 1. Concurrent Tests (`test_concurrent.sh`)
- Parallel curl requests (default: 500)
- Sequential vs parallel comparison

### 2. CONNECT Tests (`test_connect.sh`)
- Basic HTTPS through tunnel
- TLS handshake verification
- HTTPS POST requests
- Multiple HTTPS requests
- Blocked HTTPS domains
- Tunnel establishment check

## Expected Results

- **CONNECT tests**: HTTPS works through tunnel
- **Concurrent tests**: High success rate (>95%)

## Troubleshooting

1. **Connection refused**: Make sure proxy is running
2. **Timeout errors**: Increase `--max-time` in curl
3. **Blocking not working**: Check `blocked_domains.txt`
4. **HTTPS failures**: Verify CONNECT handler is working
