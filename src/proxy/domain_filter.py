import os
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s - %(asctime)s - %(levelname)s'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "blocked_domains.txt"


class DomainFilter:
    def __init__(self, config_file=None):
        self.config_file = config_file or str(DEFAULT_CONFIG)
        self.blocked_exact = set()  
        self.blocked_suffixes = [] 
        self.load_config()

    def load_config(self):
        self.blocked_exact.clear()
        self.blocked_suffixes.clear()

        if not os.path.exists(self.config_file):
            logger.warning(f"Config file '{self.config_file}' not found. No domains blocked.")
            return

        with open(self.config_file, 'r') as f:
            for line in f:
                entry = self._canonicalize(line) #canonicalization to remove whitespaces, case sensitivity and stuff
                
                if not entry or entry.startswith('#'):
                    continue

                if entry.startswith('*.'):
                    suffix = entry[2:] 
                    self.blocked_suffixes.append(suffix)
                    logger.info(f"Loaded suffix block: *.{suffix}")
                else:
                    self.blocked_exact.add(entry)
                    logger.info(f"Loaded exact block: {entry}")

        logger.info(f"Loaded {len(self.blocked_exact)} exact blocks and {len(self.blocked_suffixes)} suffix blocks")

    def _canonicalize(self, hostname):
        if hostname is None:
            return ""
        entry = hostname.strip().lower()
        
        if not entry:
            return ""
        sanitized = ''.join(c for c in entry if c.isprintable() and ord(c) < 128)

        if sanitized != entry:
            logger.warning(f"Rejected config entry with invalid characters: {repr(hostname)[:50]}")
            return ""

        MAX_HOSTNAME_LENGTH = 253
        if len(sanitized) > MAX_HOSTNAME_LENGTH:
            logger.warning(f"Rejected config entry exceeding max length: {sanitized[:50]}...")
            return ""

        check_part = sanitized[2:] if sanitized.startswith('*.') else sanitized

        import re
        if not re.match(r'^[a-z0-9]([a-z0-9\-\.]*[a-z0-9])?$|^[a-z0-9]$', check_part):
            parts = check_part.split('.')
            is_ip = len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts)
            if not is_ip:
                logger.warning(f"Rejected config entry with invalid hostname format: {sanitized[:50]}")
                return ""
        
        return sanitized

    def is_blocked(self, host):
        if not host:
            return False

        canonical_host = self._canonicalize(host)

        if ":" in canonical_host:
            canonical_host = canonical_host.split(":", 1)[0]

        if canonical_host in self.blocked_exact:
            logger.warning(f"BLOCKED (exact match): {canonical_host}")
            return True

        for suffix in self.blocked_suffixes:
            if canonical_host == suffix or canonical_host.endswith('.' + suffix):
                logger.warning(f"BLOCKED (suffix match *.{suffix}): {canonical_host}")
                return True

        return False

    def reload(self): 
        logger.info("Reloading domain filter configuration...")
        self.load_config()
    # this is for editing blocked domains.txt file during runtime and not restarting the proxy

def generate_blocked_response(headers=None):
    user_agent = ""
    if headers:
        user_agent = headers.get("User-Agent", "").lower()

    is_terminal = "curl" in user_agent or "wget" in user_agent
    # as it looked ugly when blocked on terminal so no htmls in terminal but we can force obv using curl -H and pretending user agent as mozilla or so
    if is_terminal:
        body = b"403 Forbidden\nAccess blocked by proxy server.\n"
        content_type = b"text/plain"
    else:
        body = b"""<!DOCTYPE html>
    <html>
    <head><title>403 Forbidden</title></head>
    <body>
    <h1>403 Forbidden</h1>
    <p>Access to this resource has been blocked by the proxy server.</p>
    </body>
    </html>"""
        content_type = b"text/html; charset=utf-8"

    response = (
        b"HTTP/1.1 403 Forbidden\r\n"
        b"Content-Type: " + content_type + b"\r\n"
        b"Content-Length: " + str(len(body)).encode() + b"\r\n"
        b"Connection: close\r\n"
        b"\r\n"
    ) + body

    return response

_filter = None


def get_filter(config_file=None):
    global _filter
    if _filter is None:
        _filter = DomainFilter(config_file)
    return _filter

