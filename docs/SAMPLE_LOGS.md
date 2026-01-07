# Sample Proxy Log Output

This file contains sample log entries demonstrating the proxy server's logging format and various request scenarios.

## Log Format

```
DATE TIME | CLIENT_IP:PORT | HOST:PORT | "REQUEST_LINE" | ACTION | STATUS | BYTES
```

## Sample Log Entries

```
# ============================================================================
# PROXY SERVER - SAMPLE LOG OUTPUT
# Generated during test session on 2026-01-07
# ============================================================================

# --- HTTP GET Requests (Allowed) ---
07-01-2026 22:00:01 | 127.0.0.1:54001 | httpbin.org:80 | "GET http://httpbin.org/get HTTP/1.1" | ALLOWED | 200 | 356 bytes
07-01-2026 22:00:02 | 127.0.0.1:54002 | httpbin.org:80 | "GET http://httpbin.org/ip HTTP/1.1" | ALLOWED | 200 | 45 bytes
07-01-2026 22:00:03 | 127.0.0.1:54003 | httpbin.org:80 | "GET http://httpbin.org/headers HTTP/1.1" | ALLOWED | 200 | 512 bytes
07-01-2026 22:00:04 | 127.0.0.1:54004 | httpbin.org:80 | "GET http://httpbin.org/uuid HTTP/1.1" | ALLOWED | 200 | 53 bytes

# --- HTTP POST Requests ---
07-01-2026 22:00:05 | 127.0.0.1:54005 | httpbin.org:80 | "POST http://httpbin.org/post HTTP/1.1" | ALLOWED | 200 | 489 bytes
07-01-2026 22:00:06 | 127.0.0.1:54006 | httpbin.org:80 | "POST http://httpbin.org/post HTTP/1.1" | ALLOWED | 200 | 523 bytes

# --- HTTPS CONNECT Tunneling ---
07-01-2026 22:00:10 | 127.0.0.1:54010 | httpbin.org:443 | "CONNECT httpbin.org:443 HTTP/1.1" | ALLOWED | 200 | 0 bytes
07-01-2026 22:00:11 | 127.0.0.1:54011 | google.com:443 | "CONNECT google.com:443 HTTP/1.1" | ALLOWED | 200 | 0 bytes
07-01-2026 22:00:12 | 127.0.0.1:54012 | github.com:443 | "CONNECT github.com:443 HTTP/1.1" | ALLOWED | 200 | 0 bytes

# --- Cached Responses ---
07-01-2026 22:00:15 | 127.0.0.1:54015 | httpbin.org:80 | "GET http://httpbin.org/get HTTP/1.1" | CACHED | 200 | 356 bytes
07-01-2026 22:00:16 | 127.0.0.1:54016 | httpbin.org:80 | "GET http://httpbin.org/ip HTTP/1.1" | CACHED | 200 | 45 bytes
07-01-2026 22:00:17 | 127.0.0.1:54017 | httpbin.org:80 | "GET http://httpbin.org/uuid HTTP/1.1" | CACHED | 200 | 53 bytes

# --- Blocked Domains (HTTP) ---
07-01-2026 22:00:20 | 127.0.0.1:54020 | ad.doubleclick.net:80 | "GET http://ad.doubleclick.net/ HTTP/1.1" | BLOCKED | 403 | 47 bytes
07-01-2026 22:00:21 | 127.0.0.1:54021 | www.google-analytics.com:80 | "GET http://www.google-analytics.com/analytics.js HTTP/1.1" | BLOCKED | 403 | 47 bytes
07-01-2026 22:00:22 | 127.0.0.1:54022 | tracking.example.com:80 | "GET http://tracking.example.com/pixel HTTP/1.1" | BLOCKED | 403 | 47 bytes
07-01-2026 22:00:23 | 127.0.0.1:54023 | bet365.com:80 | "GET http://bet365.com/ HTTP/1.1" | BLOCKED | 403 | 47 bytes

# --- Blocked Domains (HTTPS CONNECT) ---
07-01-2026 22:00:25 | 127.0.0.1:54025 | bet365.com:443 | "CONNECT bet365.com:443 HTTP/1.1" | BLOCKED | 403 | 47 bytes
07-01-2026 22:00:26 | 127.0.0.1:54026 | pokerstars.com:443 | "CONNECT pokerstars.com:443 HTTP/1.1" | BLOCKED | 403 | 47 bytes

# --- Error Responses ---
07-01-2026 22:00:30 | 127.0.0.1:54030 | nonexistent.invalid.domain:80 | "GET http://nonexistent.invalid.domain/ HTTP/1.1" | ALLOWED | 502 | 0 bytes
07-01-2026 22:00:31 | 127.0.0.1:54031 | unknown:0 | "TIMEOUT" | ALLOWED | 408 | 0 bytes
07-01-2026 22:00:32 | 127.0.0.1:54032 | unknown:0 | "INVALID REQUEST" | ALLOWED | 400 | 0 bytes

# --- Concurrent Request Burst ---
07-01-2026 22:00:40 | 127.0.0.1:55001 | httpbin.org:80 | "GET http://httpbin.org/uuid HTTP/1.1" | ALLOWED | 200 | 53 bytes
07-01-2026 22:00:40 | 127.0.0.1:55002 | httpbin.org:80 | "GET http://httpbin.org/uuid HTTP/1.1" | ALLOWED | 200 | 53 bytes
07-01-2026 22:00:40 | 127.0.0.1:55003 | httpbin.org:80 | "GET http://httpbin.org/uuid HTTP/1.1" | ALLOWED | 200 | 53 bytes
07-01-2026 22:00:40 | 127.0.0.1:55004 | httpbin.org:80 | "GET http://httpbin.org/uuid HTTP/1.1" | ALLOWED | 200 | 53 bytes
07-01-2026 22:00:40 | 127.0.0.1:55005 | httpbin.org:80 | "GET http://httpbin.org/uuid HTTP/1.1" | ALLOWED | 200 | 53 bytes
07-01-2026 22:00:41 | 127.0.0.1:55006 | httpbin.org:80 | "GET http://httpbin.org/uuid HTTP/1.1" | ALLOWED | 200 | 53 bytes
07-01-2026 22:00:41 | 127.0.0.1:55007 | httpbin.org:80 | "GET http://httpbin.org/uuid HTTP/1.1" | ALLOWED | 200 | 53 bytes
07-01-2026 22:00:41 | 127.0.0.1:55008 | httpbin.org:80 | "GET http://httpbin.org/uuid HTTP/1.1" | ALLOWED | 200 | 53 bytes
07-01-2026 22:00:41 | 127.0.0.1:55009 | httpbin.org:80 | "GET http://httpbin.org/uuid HTTP/1.1" | ALLOWED | 200 | 53 bytes
07-01-2026 22:00:41 | 127.0.0.1:55010 | httpbin.org:80 | "GET http://httpbin.org/uuid HTTP/1.1" | ALLOWED | 200 | 53 bytes

# --- Various Domains ---
07-01-2026 22:01:00 | 127.0.0.1:56001 | example.com:80 | "GET http://example.com/ HTTP/1.1" | ALLOWED | 200 | 1256 bytes
07-01-2026 22:01:01 | 127.0.0.1:56002 | jsonplaceholder.typicode.com:80 | "GET http://jsonplaceholder.typicode.com/todos/1 HTTP/1.1" | ALLOWED | 200 | 83 bytes
07-01-2026 22:01:02 | 127.0.0.1:56003 | api.github.com:443 | "CONNECT api.github.com:443 HTTP/1.1" | ALLOWED | 200 | 0 bytes
```

## Action Types Explained

| Action | Description |
|--------|-------------|
| `ALLOWED` | Request forwarded to origin server |
| `BLOCKED` | Request denied due to blocklist match |
| `CACHED` | Response served from cache |

## Status Codes Explained

| Status | Meaning |
|--------|---------|
| `200` | Success (for tunnels: tunnel established) |
| `400` | Bad Request - malformed HTTP request |
| `403` | Forbidden - domain blocked |
| `408` | Request Timeout - client too slow |
| `502` | Bad Gateway - origin server unreachable |
| `504` | Gateway Timeout - origin server too slow |
