# Async Forward Proxy Server

A forward HTTP/HTTPS proxy server built with Python's asyncio. It handles request forwarding, CONNECT tunneling for HTTPS, domain-based filtering, and basic response caching.

## Video Demonstration

Basic Proxy server demonstration: [https://youtu.be/5s3Tnp_vMlk](https://youtu.be/5s3Tnp_vMlk)

## How It Works

### HTTP Requests

1. Client connects and sends a request like `GET http://example.com/path HTTP/1.1`
2. Proxy parses the request, extracts the target host
3. Checks if the domain is blocked (returns 403 if so)
4. Checks cache for a stored response
5. If not cached, opens a connection to the origin server
6. Forwards the request, streams the response back to client
7. Caches the response for future requests (if cacheable)

### HTTPS Requests (CONNECT Tunneling)

1. Client sends `CONNECT example.com:443 HTTP/1.1`
2. Proxy checks if domain is blocked
3. Opens a TCP connection to the target
4. Responds with `200 Connection Established`
5. Blindly pipes bytes between client and server (encrypted TLS traffic)
6. No caching possible here since the proxy can't read the encrypted data

![Proxy Flow](docs/images/proxy_flow.jpg)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         proxy.py                            │
│                    (asyncio server loop)                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       forwarder.py                          │
│         handle_client() → handle_http() / handle_connect()  │
└─────────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
   ┌──────────┐  ┌─────────────┐  ┌──────────┐  ┌───────────┐
   │http_parser│ │domain_filter│  │http_cache│  │proxy_logger│
   │          │  │             │  │  (LRU)   │  │ (rotating) │
   └──────────┘  └─────────────┘  └──────────┘  └───────────┘
```

**Modules:**
- `proxy.py` — Main server, signal handling, startup/shutdown
- `forwarder.py` — Request routing, connection management, bidirectional piping
- `http_parser.py` — Parses request line, headers, body (async)
- `domain_filter.py` — Blocklist with wildcard support
- `http_cache.py` — LRU cache with TTL expiration
- `proxy_logger.py` — Structured logging with rotation, request metrics

## Installation

```bash
git clone https://github.com/yourusername/proxy-project.git
cd proxy-project

# Run directly
python run.py

# Or install as a package
pip install -e .
proxy-server
```

Requires Python 3.8+. Requires `termcolor` package (`pip install termcolor`) for colored outputs.

## Usage

### Start the proxy

```bash
python run.py --port 8080
```

### Configure a client to use the proxy

```bash
# curl
curl -x http://127.0.0.1:8080 http://httpbin.org/get
curl -x http://127.0.0.1:8080 https://httpbin.org/get

# Environment variable (works with many tools)
export http_proxy=http://127.0.0.1:8080
export https_proxy=http://127.0.0.1:8080
```

### Browser configuration

Set your browser's proxy settings to `127.0.0.1:8080` for HTTP and HTTPS.

## Configuration

### Domain Blocking

Edit `config/blocked_domains.txt`:

```
# Exact match
ads.example.com

# Wildcard (blocks all subdomains)
*.doubleclick.net
*.google-analytics.com

# Block by IP
192.168.1.100
```

The blocklist is loaded at startup. Blocked requests return `403 Forbidden`.

### Cache Settings

Defaults in `http_cache.py`:
- Max entries: 100
- Max size: 50MB
- TTL: 300 seconds

Only GET requests with cacheable responses are stored. Requests with `Authorization` headers or `Cache-Control: no-store` bypass the cache.

## Project Structure

```
proxy-project/
├── src/proxy/
│   ├── __init__.py       # Package initializer
│   ├── proxy.py          # Server entry point
│   ├── forwarder.py      # Request handling
│   ├── http_parser.py    # HTTP parsing
│   ├── http_cache.py     # LRU cache
│   ├── domain_filter.py  # Blocklist
│   └── proxy_logger.py   # Logging
├── config/
│   └── blocked_domains.txt
├── docs/
│   ├── DESIGN.md         # Architecture documentation
│   ├── SAMPLE_LOGS.md    # Example log output
│   └── images/           # Diagrams
├── tests/
│   ├── README.md         # Test documentation
│   ├── test_basic.sh     # HTTP forwarding tests
│   ├── test_blocking.sh  # Domain filtering tests
│   ├── test_concurrent.sh # Load tests
│   ├── test_connect.sh   # HTTPS tunneling tests
│   └── test_malformed.sh # Error handling tests
├── run.py                # Direct execution
├── setup.py              # Package installation
└── .gitignore
```

## Limitations

- **No HTTPS interception** — The proxy can't inspect HTTPS traffic. It just tunnels encrypted bytes.
- **No authentication** — Anyone who can reach the proxy can use it.
- **Basic cache validation** — Doesn't handle ETags or conditional requests properly.


## License

MIT

---

