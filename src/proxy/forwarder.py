import asyncio
from .http_parser import async_parse_http_request, HTTPRequest
from .domain_filter import get_filter, generate_blocked_response
from .http_cache import get_cache
from .proxy_logger import get_logger, get_metrics

# Socket timeout in seconds
SOCKET_TIMEOUT = 45


def build_request_bytes(req):
    request_line = f"{req.method} {req.path} {req.version}\r\n"
    headers = b""

    for key, value in req.headers.items():
        headers += f"{key}: {value}\r\n".encode()

    headers += b"\r\n"
    return request_line.encode() + headers + req.body


async def relay_and_capture(reader, writer):
    response_bytes = b""
    try:
        while True:
            data = await asyncio.wait_for(reader.read(4096), timeout=SOCKET_TIMEOUT)
            if not data:
                break
            writer.write(data)
            await writer.drain()
            response_bytes += data
    except asyncio.TimeoutError:
        pass
    return response_bytes


async def pipe(reader, writer):
    while True:
        try:
            data = await reader.read(4096)
            if not data:
                break
            
            writer.write(data)
            await writer.drain()

        except (ConnectionResetError, BrokenPipeError):
            pass
        except asyncio.CancelledError:
            pass
        except Exception:
            pass
        
# CONNECT is just a http request like GET 
# basically we create a passage/tunnel b/w the client and the server for https request forwarding as https is obv protected
# also in here no caching would be implemented as after CONNECT is established, the raw bytes which the proxy server receives are encrypted due to https and hence no caching possible 
async def handle_connect(client_reader, client_writer, req, client_addr):
    logger = get_logger()
    metrics = get_metrics()
    domain_filter = get_filter()
    request_line = f"CONNECT {req.target} {req.version}"

    # domain filter checker
    if domain_filter.is_blocked(req.host):
        response = generate_blocked_response(req.headers)
        client_writer.write(response)
        await client_writer.drain()
        client_writer.close()
        await client_writer.wait_closed()
        logger.log_request(client_addr, req.host, req.port, request_line, "BLOCKED", 403, len(response))
        metrics.record_request(req.host, blocked=True)
        return

    try:
        server_reader, server_writer = await asyncio.wait_for(
            asyncio.open_connection(req.host, req.port),
            timeout=SOCKET_TIMEOUT
        )
    except Exception:
        client_writer.write(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
        await client_writer.drain()
        client_writer.close()
        await client_writer.wait_closed()
        logger.log_request(client_addr, req.host, req.port, request_line, "ALLOWED", 502, 0)
        metrics.record_request(req.host)
        return

    client_writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
    await client_writer.drain()
    logger.log_request(client_addr, req.host, req.port, request_line, "ALLOWED", 200, 0)
    metrics.record_request(req.host)

    try:
        await asyncio.gather(
            pipe(client_reader, server_writer),
            pipe(server_reader, client_writer),
            return_exceptions=True
        )
    finally:
        try:
            server_writer.close()
            await server_writer.wait_closed()
        except Exception:
            pass
        try:
            client_writer.close()
            await client_writer.wait_closed()
        except Exception:
            pass


# handling http -> 2 ways either find the request in cache or else we can just forward it to the server, easier just need to get the await right

async def handle_http(client_reader, client_writer, req, client_addr):
    logger = get_logger()
    metrics = get_metrics()
    cache = get_cache()
    request_line = f"{req.method} {req.target} {req.version}"

    cached = cache.get(req.method, req.host, req.path, req.headers)
    if cached:
        client_writer.write(cached.response_bytes)
        await client_writer.drain()
        client_writer.close()
        await client_writer.wait_closed()
        logger.log_request(client_addr, req.host, req.port, request_line, "CACHED", 200, len(cached.response_bytes))
        metrics.record_request(req.host)
        return

    try:
        server_reader, server_writer = await asyncio.wait_for(
            asyncio.open_connection(req.host, req.port),
            timeout=SOCKET_TIMEOUT
        )
    except Exception:
        client_writer.write(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
        await client_writer.drain()
        client_writer.close()
        await client_writer.wait_closed()
        logger.log_request(client_addr, req.host, req.port, request_line, "ALLOWED", 502, 0)
        metrics.record_request(req.host)
        return

    try:
        request_bytes = build_request_bytes(req)
        server_writer.write(request_bytes)
        await server_writer.drain()

        response_bytes = await relay_and_capture(server_reader, client_writer)

        cache.put(req.method, req.host, req.path, req.headers, response_bytes)

        logger.log_request(client_addr, req.host, req.port, request_line, "ALLOWED", 200, len(response_bytes))
        metrics.record_request(req.host)
    except asyncio.TimeoutError:
        logger.log_request(client_addr, req.host, req.port, request_line, "ALLOWED", 504, 0)
    except Exception:
        pass
    finally:
        try:
            server_writer.close()
            await server_writer.wait_closed()
        except Exception:
            pass
        try:
            client_writer.close()
            await client_writer.wait_closed()
        except Exception:
            pass


async def handle_client(reader, writer):
    logger = get_logger()
    metrics = get_metrics()
    domain_filter = get_filter()

    client_addr = writer.get_extra_info('peername')
    if client_addr is None:
        client_addr = ('unknown', 0)

    try:
        req = await asyncio.wait_for(
            async_parse_http_request(reader),
            timeout=SOCKET_TIMEOUT
        )
    except asyncio.TimeoutError:
        try:
            writer.write(b"HTTP/1.1 408 Request Timeout\r\n\r\n")
            await writer.drain()
        except Exception:
            pass
        writer.close()
        await writer.wait_closed()
        logger.log_request(client_addr, "unknown", 0, "TIMEOUT", "ALLOWED", 408, 0)
        return
    except Exception:
        try:
            writer.write(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            await writer.drain()
        except Exception:
            pass
        writer.close()
        await writer.wait_closed()
        logger.log_request(client_addr, "unknown", 0, "INVALID REQUEST", "ALLOWED", 400, 0)
        return

    request_line = f"{req.method} {req.target} {req.version}"

    if domain_filter.is_blocked(req.host):
        response = generate_blocked_response(req.headers)
        writer.write(response)
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        logger.log_request(client_addr, req.host, req.port, request_line, "BLOCKED", 403, len(response))
        metrics.record_request(req.host, blocked=True)
        return

    # simple if else for http and connect reqs
    if req.method.upper() == "CONNECT":
        await handle_connect(reader, writer, req, client_addr)
    else:
        await handle_http(reader, writer, req, client_addr)