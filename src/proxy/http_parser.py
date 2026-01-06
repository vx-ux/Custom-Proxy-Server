from urllib.parse import urlparse

class HTTPRequest:
    def __init__(self, method, target, path, version, headers, body, host, port):
        self.method = method
        self.target = target
        self.path = path
        self.version = version 
        self.headers = headers
        self.body = body 
        self.host = host
        self.port = port

# for reading until headers end
async def async_recv_until(reader, delimiter=b"\r\n\r\n"):
    data = b""
    while delimiter not in data:
        chunk = await reader.read(4096)
        if not chunk:
            break
        data += chunk
    return data
    
# main parser fxn

async def async_parse_http_request(reader):

    raw = await async_recv_until(reader)

    if not raw:
        raise ValueError("Empty request")

    header_bytes, _, remaining = raw.partition(b"\r\n\r\n")
    header_lines = header_bytes.decode(errors="replace").split("\r\n")

    # parsing req line
    request_line = header_lines[0]
    parts = request_line.split()
    if len(parts) != 3:
        raise ValueError("Invalid request line")
    method, target, version = parts

    # parsing headers
    headers = {}
    for line in header_lines[1:]:
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip()] = value.strip()
    
    # normal default values
    host = None
    port = 80
    path = None

    # Handling CONNECT (later)
    if method.upper() == "CONNECT":
        # target is something like "example.com:443" and looks like CONNECT example.com:443 HTTP/1.1
        # CONNECT server.example.com:80 HTTP/1.1
        # Host: server.example.com:80
        # Proxy-Authorization: basic aGVsbG86d29ybGQ=
        host, port = target.split(":")
        port = int(port)
        path = None
        body = b""

        return HTTPRequest(
            method, target, path, version, headers, body, host, port
        )

    # Handling relative uris and absolute uris
    if target.startswith("http://") or target.startswith("https://"):
        parsed = urlparse(target)
        host = parsed.hostname
        port = parsed.port or (80 if parsed.scheme == "http" else 443)

        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query
        
    else:
    #Relative uris use host header
        if "Host" not in headers:
            raise ValueError("400 Bad Request: Missing Host Header")
        
        host_header = headers["Host"]
        if ":" in host_header:
            host, port = host_header.split(":")
            port = int(port)
        else:
            host = host_header
        path = target
    
    # Reading body using Content-Length basically len(body) starts from 0 and ends when it is = to CL and CL is the total length of the body like POST data etc
    content_length = int(headers.get("Content-Length", 0))
    body = remaining

    while len(body) < content_length:
        chunk = await reader.read(content_length - len(body))
        if not chunk:
            break
        body += chunk

    return HTTPRequest(
        method = method,
        target = target,
        path = path,
        version = version,
        headers=headers,
        body=body,
        host=host,
        port=port
    )
    # parse host and path from URI

    # else:
    #     use Host header + target
