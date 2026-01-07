import logging
import threading
import time
from collections import defaultdict
from logging.handlers import RotatingFileHandler
from termcolor import colored

class ProxyLogger:
    # 5 mb liya
    def __init__(self, log_file="proxy.log", max_bytes=5*1024*1024, backup_count=3):
        self.logger = logging.getLogger("proxy")
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            file_handler.setLevel(logging.INFO)
            
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            formatter = logging.Formatter(
                '%(asctime)s | %(message)s',
                datefmt='%d-%m-%Y %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
    
    def log_request(self, client_addr, host, port, request_line, action, 
                    status_code, bytes_transferred=0):
        client_ip, client_port = client_addr
        log_entry = (
            f"{client_ip}:{client_port} | "
            f"{host}:{port} | "
            f"\"{request_line}\" | "
            f"{action} | "
            f"{status_code} | "
            f"{bytes_transferred} bytes"
        )
        
        if action == "BLOCKED":
            self.logger.warning(log_entry)
        else:
            self.logger.info(log_entry)


class ProxyMetrics:
    
    def __init__(self):
        self._lock = threading.RLock()
        self._total_requests = 0
        self._blocked_requests = 0
        self._host_counts = defaultdict(int)
        self._request_times = [] 
        self._start_time = time.time()
    
    def record_request(self, host, blocked=False):
        with self._lock:
            self._total_requests += 1
            if blocked:
                self._blocked_requests += 1
            self._host_counts[host] += 1
            self._request_times.append(time.time())
            
            cutoff = time.time() - 300
            self._request_times = [t for t in self._request_times if t > cutoff]
    
    def get_requests_per_minute(self):
        with self._lock:
            now = time.time()
            one_minute_ago = now - 60
            recent = [t for t in self._request_times if t > one_minute_ago]
            return len(recent)
    
    def get_top_hosts(self, n=10):
        with self._lock:
            sorted_hosts = sorted(
                self._host_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )
            return sorted_hosts[:n]
    
    def get_summary(self):
        with self._lock:
            uptime = time.time() - self._start_time
            rpm = self.get_requests_per_minute()
            top_hosts = self.get_top_hosts(5)
            
            return {
                "uptime_seconds": int(uptime),
                "total_requests": self._total_requests,
                "blocked_requests": self._blocked_requests,
                "allowed_requests": self._total_requests - self._blocked_requests,
                "requests_per_minute": rpm,
                "top_hosts": top_hosts
            }
    
    def print_summary(self):
        summary = self.get_summary()
        
        print(colored("Proxy Metrics Summary\n", "red"))
        print(colored(f"Uptime: {summary['uptime_seconds']} seconds", "green", attrs=["bold"]))
        print(colored(f"Total Requests: {summary['total_requests']}", "green", attrs=["bold"]))
        print(colored(f"  - Allowed: {summary['allowed_requests']}", "green", attrs=["bold"]))
        print(colored(f"  - Blocked: {summary['blocked_requests']}", "red", attrs=["bold"]))
        print(colored(f"Requests/Minute: {summary['requests_per_minute']}", "green", attrs=["bold"]))
        print(colored("\nTop Requested Hosts:", "blue", attrs=["bold"]))
        for host, count in summary['top_hosts']:
            print(colored(f"  {host}: {count} requests", "green", attrs=["bold"]))
        print("\n")


# Global instances
_logger = None
_metrics = None


def get_logger():
    global _logger
    if _logger is None:
        _logger = ProxyLogger()
    return _logger


def get_metrics():
    global _metrics
    if _metrics is None:
        _metrics = ProxyMetrics()
    return _metrics
