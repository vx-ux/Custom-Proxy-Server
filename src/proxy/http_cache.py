import time
import threading
from collections import OrderedDict


class CacheEntry:
    
    def __init__(self, response_bytes, headers, status_code):
        self.response_bytes = response_bytes
        self.headers = headers
        self.status_code = status_code
        self.timestamp = time.time()
        self.content_length = len(response_bytes)
        self.hits = 0
    
    def is_fresh(self, max_age=300):
        return (time.time() - self.timestamp) < max_age
    
    def get_age(self):
        return int(time.time() - self.timestamp)


class LRUCache:
    
    def __init__(self, max_entries=100, max_size_bytes=50*1024*1024, default_ttl=300):
        self._cache = OrderedDict()  # OrderedDict provides LRU behavior
        self._lock = threading.RLock()
        self.max_entries = max_entries
        self.max_size_bytes = max_size_bytes
        self.default_ttl = default_ttl
        self._current_size = 0
        
        # Stats
        self.hits = 0
        self.misses = 0
    
    def _normalize_key(self, method, host, path):
        return f"{method.upper()}:{host.lower()}{path}"
    
    def _is_cacheable_request(self, method, headers):
        if method.upper() != "GET":
            return False
        
        if "Authorization" in headers:
            return False
        
        cache_control = headers.get("Cache-Control", "").lower()
        if "no-store" in cache_control or "no-cache" in cache_control:
            return False
        
        return True
    
    def _is_cacheable_response(self, status_code, response_headers):
        if status_code not in (200, 301, 302, 304):
            return False
        
        cache_control = response_headers.get("Cache-Control", "").lower()
        if "no-store" in cache_control or "private" in cache_control:
            return False
        
        return True
    
    def _parse_response_headers(self, response_bytes):
        try:
            header_end = response_bytes.find(b"\r\n\r\n")
            if header_end == -1:
                return None, {}, response_bytes
            
            header_bytes = response_bytes[:header_end]
            body = response_bytes[header_end + 4:]
            
            lines = header_bytes.decode("utf-8", errors="replace").split("\r\n")
            
            status_line = lines[0]
            parts = status_line.split(" ", 2)
            status_code = int(parts[1]) if len(parts) >= 2 else 0
            
            headers = {}
            for line in lines[1:]:
                if ":" in line:
                    key, value = line.split(":", 1)
                    headers[key.strip()] = value.strip()
            
            return status_code, headers, response_bytes
        except Exception:
            return None, {}, response_bytes
    
    def _evict_if_needed(self):
        while len(self._cache) >= self.max_entries:
            oldest_key, oldest_entry = self._cache.popitem(last=False)
            self._current_size -= oldest_entry.content_length
        
        while self._current_size > self.max_size_bytes and self._cache:
            oldest_key, oldest_entry = self._cache.popitem(last=False)
            self._current_size -= oldest_entry.content_length
    
    def get(self, method, host, path, request_headers):
        if not self._is_cacheable_request(method, request_headers):
            return None
        
        key = self._normalize_key(method, host, path)
        
        with self._lock:
            if key not in self._cache:
                self.misses += 1
                return None
            
            entry = self._cache[key]
            
            if not entry.is_fresh(self.default_ttl):
                del self._cache[key]
                self._current_size -= entry.content_length
                self.misses += 1
                return None
            
            self._cache.move_to_end(key)
            entry.hits += 1
            self.hits += 1
            
            return entry
    
    def put(self, method, host, path, request_headers, response_bytes):
        if not self._is_cacheable_request(method, request_headers):
            return False
        
        status_code, response_headers, _ = self._parse_response_headers(response_bytes)
        
        if status_code is None:
            return False
        
        if not self._is_cacheable_response(status_code, response_headers):
            return False
        
        key = self._normalize_key(method, host, path)
        
        with self._lock:
            if key in self._cache:
                old_entry = self._cache.pop(key)
                self._current_size -= old_entry.content_length

            self._evict_if_needed()

            entry = CacheEntry(response_bytes, response_headers, status_code)
            self._cache[key] = entry
            self._current_size += entry.content_length
            
            return True
    
    def clear(self):
        with self._lock:
            self._cache.clear()
            self._current_size = 0
    
    def get_stats(self):
        with self._lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100) if total > 0 else 0
            return {
                "entries": len(self._cache),
                "size_bytes": self._current_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": f"{hit_rate:.1f}%"
            }


_cache = None


def get_cache():
    global _cache
    if _cache is None:
        _cache = LRUCache()
    return _cache
