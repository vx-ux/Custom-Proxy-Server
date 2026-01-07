# Design Document: Custom Network Proxy Server

## Overview

This document describes the architecture, design decisions, and implementation details of an asynchronous HTTP/HTTPS forward proxy server built with Python's asyncio framework.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT APPLICATION                             │
│                    (Browser, curl, wget, applications)                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ HTTP/HTTPS Request
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PROXY SERVER                                   │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         proxy.py (Entry Point)                         │ │
│  │              • asyncio.start_server() event loop                       │ │
│  │              • Signal handling (SIGINT, SIGTERM)                       │ │
│  │              • Graceful shutdown with active task tracking             │ │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                      │
│                                      ▼                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    forwarder.py (Request Router)                       │ │
│  │              • handle_client() - Main entry per connection             │ │
│  │              • handle_http() - HTTP GET/POST forwarding                │ │
│  │              • handle_connect() - HTTPS tunnel establishment           │ │
│  └───────────────────────────────────────────────────────────────────────┘  │
│          │              │              │              │                     │
│          ▼              ▼              ▼              ▼                     │
│  ┌────────────┐ ┌─────────────┐ ┌───────────┐ ┌──────────────┐              │
│  │http_parser │ │domain_filter│ │ http_cache│ │ proxy_logger │              │
│  │            │ │             │ │   (LRU)   │ │  (rotating)  │              │
│  │ • Parse    │ │ • Blocklist │ │ • TTL     │ │ • File logs  │              │
│  │   request  │ │ • Wildcards │ │ • Eviction│ │ • Metrics    │              │
│  │   line     │ │ • IP blocks │ │ • Stats   │ │ • Console    │              │
│  └────────────┘ └─────────────┘ └───────────┘ └──────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ Forwarded Request
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            ORIGIN SERVER                                    │
│                    (httpbin.org, google.com, etc.)                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Descriptions

### 1. proxy.py - Server Entry Point
**Responsibility**: Initialize and manage the asyncio server lifecycle.

- Creates TCP server using `asyncio.start_server()`
- Binds to configurable host/port (default: 127.0.0.1:8080)
- Tracks active client tasks for graceful shutdown
- Handles OS signals (SIGINT, SIGTERM) for clean termination
- Prints statistics on shutdown (metrics, cache stats)

### 2. forwarder.py - Request Handler
**Responsibility**: Route incoming requests to appropriate handlers.

- `handle_client()`: Entry point for each client connection
- `handle_http()`: Forward HTTP requests, check cache, relay responses
- `handle_connect()`: Establish HTTPS tunnels (bidirectional pipe)
- `pipe()`: Async bidirectional data transfer for tunnels
- `relay_and_capture()`: Stream response while capturing for cache

### 3. http_parser.py - HTTP Protocol Parser
**Responsibility**: Parse raw HTTP requests into structured objects.

- Async reading until `\r\n\r\n` (headers complete)
- Parse request line: `METHOD TARGET HTTP/VERSION`
- Extract headers into dictionary
- Handle both absolute URIs (`http://host/path`) and relative URIs
- Special handling for CONNECT method (host:port extraction)
- Read body based on Content-Length header

### 4. domain_filter.py - Access Control
**Responsibility**: Block requests to blacklisted domains/IPs.

- Load blocklist from `config/blocked_domains.txt`
- Support exact matches: `ads.example.com`
- Support wildcard suffixes: `*.doubleclick.net`
- Support IP blocking: `192.168.1.100`
- Hostname canonicalization (lowercase, trim, validate)
- Generate 403 Forbidden responses (HTML for browsers, text for CLI)

### 5. http_cache.py - Response Caching
**Responsibility**: Cache HTTP responses to reduce origin server load.

- LRU (Least Recently Used) eviction policy
- Configurable limits: max entries (100), max size (50MB), TTL (300s)
- Cache key: `METHOD:host:path`
- Only cache GET requests with cacheable responses
- Skip caching for: Authorization headers, no-store, private responses
- Thread-safe with RLock

### 6. proxy_logger.py - Logging & Metrics
**Responsibility**: Log all proxy activity and track performance metrics.

- Rotating file handler (5MB max, 3 backups)
- Console output with colored status indicators
- Per-request logging: client IP, target, status, bytes transferred
- Metrics: total requests, blocked count, requests/minute, top hosts

---

## Concurrency Model

### Choice: asyncio Event Loop (Single-Threaded Async I/O)

```
┌─────────────────────────────────────────────────────────────────┐
│                      Event Loop (Single Thread)                 │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐    │
│  │Client 1 │ │Client 2 │ │Client 3 │ │Client 4 │ │Client N │    │
│  │  Task   │ │  Task   │ │  Task   │ │  Task   │ │  Task   │    │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘    │
│       │           │           │           │           │         │
│       └───────────┴───────────┴─────┬─────┴───────────┘         │
│                                     │                           │
│                            ┌────────▼────────┐                  │
│                            │  Cooperative    │                  │
│                            │  Scheduling     │                  │
│                            │  (await points) │                  │
│                            └─────────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
```

### Rationale

| Model | Pros | Cons |
|-------|------|------|
| **Thread-per-connection** | Simple to implement | High memory overhead, context switching |
| **Thread pool** | Bounded resources | Still has thread overhead, GIL contention |
| **asyncio (chosen)** | Low overhead, high concurrency, no GIL issues for I/O | Requires async/await discipline |

**Asyncio Pros**
1. **I/O Bound Workload**: Proxy servers spend most time waiting for network I/O
2. **High Concurrency**: Can handle thousands of connections with minimal memory
3. **No GIL Issues**: Python's GIL doesn't affect async I/O operations
4. **Modern Python**: Native support since Python 3.4, mature ecosystem
5. **Simplicity**: Single-threaded model avoids race conditions

### Implementation Details

```python
# Server startup
self.server = await asyncio.start_server(
    self._handle_client,
    self.host,
    self.port,
    reuse_address=True
)

# Each client gets a coroutine task
async def _handle_client(self, reader, writer):
    task = asyncio.current_task()
    self.active_tasks.add(task)
    await handle_client(reader, writer)
```

---

## Data Flow

### HTTP Request Flow (GET/POST)

```
1. Client ──────────────────► Proxy receives connection
                              │
2. Parse HTTP request         │ async_parse_http_request()
   - Extract method, host,    │
     path, headers, body      │
                              ▼
3. Domain filter check ───────► is_blocked(host)?
                              │
   ├─ YES ─► Return 403 Forbidden
   │
   └─ NO ──► Continue
                              │
4. Cache lookup ──────────────► cache.get(method, host, path)?
                              │
   ├─ HIT ──► Return cached response
   │
   └─ MISS ─► Continue
                              │
5. Connect to origin ─────────► asyncio.open_connection(host, port)
                              │
6. Forward request ───────────► server_writer.write(request_bytes)
                              │
7. Stream response ───────────► relay_and_capture()
   - Send to client           │   (captures for caching)
   - Capture bytes            │
                              │
8. Cache response ────────────► cache.put(method, host, path, response)
                              │
9. Log request ───────────────► logger.log_request(...)
```

### HTTPS CONNECT Flow (Tunneling)

```
1. Client ──────────────────► CONNECT host:443 HTTP/1.1
                              │
2. Parse CONNECT request      │ Extract host:port from target
                              │
3. Domain filter check ───────► is_blocked(host)?
                              │
   ├─ YES ─► Return 403 Forbidden
   │
   └─ NO ──► Continue
                              │
4. Connect to origin ─────────► asyncio.open_connection(host, 443)
                              │
   ├─ FAIL ► Return 502 Bad Gateway
   │
   └─ OK ──► Continue
                              │
5. Send tunnel response ──────► HTTP/1.1 200 Connection Established
                              │
6. Bidirectional pipe ────────► asyncio.gather(
                              │     pipe(client → server),
                              │     pipe(server → client)
                              │ )
                              │
   [Encrypted TLS traffic flows through tunnel]
   [Proxy cannot inspect content - pure byte relay]
                              │
7. Connection closes ─────────► Both directions complete
```

---

## Error Handling

| Error | HTTP Status | When |
|-------|-------------|------|
| Empty/malformed request | 400 Bad Request | Parse failure |
| Blocked domain | 403 Forbidden | Domain in blocklist |
| Request timeout | 408 Request Timeout | Client too slow |
| Origin unreachable | 502 Bad Gateway | Connection failed |
| Origin timeout | 504 Gateway Timeout | Server too slow |

### Implementation

```python
try:
    req = await asyncio.wait_for(
        async_parse_http_request(reader),
        timeout=SOCKET_TIMEOUT
    )
except asyncio.TimeoutError:
    writer.write(b"HTTP/1.1 408 Request Timeout\r\n\r\n")
except Exception:
    writer.write(b"HTTP/1.1 400 Bad Request\r\n\r\n")
```

---

## Security Considerations

### Implemented Security Measures

1. **Domain Filtering**: Block access to known malicious/unwanted domains
2. **Input Validation**: Hostname canonicalization prevents basic injection
3. **Timeout Protection**: 45-second socket timeout prevents slowloris attacks
4. **Connection Limits**: asyncio naturally limits resources per connection
5. **No HTTPS Interception**: Encrypted traffic passes through unchanged

### Known Vulnerabilities / Limitations

| Issue | Description | Mitigation |
|-------|-------------|------------|
| **No Authentication** | Anyone can use the proxy | Deploy behind firewall or add auth |
| **Open Relay Risk** | Could be used for malicious traffic | Restrict binding to localhost |
| **Log Injection** | Malicious hostnames could corrupt logs | Hostname validation |
| **Resource Exhaustion** | Many connections could exhaust memory | OS-level limits (ulimit) |
| **Cache Poisoning** | Malicious responses could be cached | Only cache 2xx from known hosts |

### Security Recommendations for Production

1. **Bind to localhost only** (default: 127.0.0.1)
2. **Run behind a firewall** to control access
3. **Implement authentication** (Basic/Digest auth - planned feature)
4. **Rate limiting** per client IP
5. **Connection pooling** to prevent SYN flood to origins
6. **TLS for proxy communication** (HTTPS proxy protocol)

---

## Configuration

### Runtime Configuration (CLI)

```bash
python run.py --host 127.0.0.1 --port 8080
```

### Blocklist Configuration

File: `config/blocked_domains.txt`

```text
# Exact domain match
ads.example.com

# Wildcard suffix (all subdomains)
*.doubleclick.net

# IP address
192.168.1.100
```

### Cache Configuration (Code)

| Parameter | Default | Location |
|-----------|---------|----------|
| Max entries | 100 | `http_cache.py` |
| Max size | 50 MB | `http_cache.py` |
| TTL | 300 seconds | `http_cache.py` |

### Logging Configuration (Code)

| Parameter | Default | Location |
|-----------|---------|----------|
| Log file | `proxy.log` | `proxy_logger.py` |
| Max file size | 5 MB | `proxy_logger.py` |
| Backup count | 3 | `proxy_logger.py` |

---

## Limitations

1. **No HTTPS Interception**: Cannot inspect encrypted traffic (by design)
2. **No Proxy Authentication**: Any client can use the proxy
3. **Basic Cache Validation**: No ETag or conditional request support
4. **Single Interface**: Binds to one address at a time
5. **No Connection Pooling**: New connection per origin request
6. **No HTTP/2 Support**: HTTP/1.1 only

---

## References

- POSIX Signal Handling: [signal(7)](https://man7.org/linux/man-pages/man7/signal.7.html)
- [RFC 7230 - HTTP/1.1 Message Syntax](https://tools.ietf.org/html/rfc7230)
- [RFC 7231 - HTTP/1.1 Semantics](https://tools.ietf.org/html/rfc7231)
- [RFC 7234 - HTTP/1.1 Caching](https://tools.ietf.org/html/rfc7234)
- [Python asyncio Documentation](https://docs.python.org/3/library/asyncio.html)
