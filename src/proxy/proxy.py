# Main entry point - Async Proxy Server

import asyncio
import signal
import sys
from .forwarder import handle_client
from .domain_filter import get_filter
from .http_cache import get_cache
from .proxy_logger import get_logger, get_metrics
from termcolor import colored

class ProxyServer:

    def __init__(self, host='127.0.0.1', port=8080):
        self.host = host
        self.port = port
        self.server = None
        self.logger = get_logger()
        self.metrics = get_metrics()
        self.active_tasks = set()

    async def start(self):
        get_filter()  
        get_cache()  

        self.server = await asyncio.start_server(
            self._handle_client,
            self.host,
            self.port,
            reuse_address=True
        )

        addrs = ', '.join(str(sock.getsockname()) for sock in self.server.sockets)
        print(f"  Proxy Server has been Started")
        print(f"  Listening on {addrs}")
        print(f"  Press Ctrl+C to close")

        try:
            await self.server.serve_forever()
        except asyncio.CancelledError:
            pass

    async def _handle_client(self, reader, writer):
        task = asyncio.current_task()
        self.active_tasks.add(task)
        try:
            await handle_client(reader, writer)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            client_addr = writer.get_extra_info('peername')
            print(f"Error handling {client_addr}: {e}")
        finally:
            self.active_tasks.discard(task)
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    async def stop(self):
        if self.server:
            self.server.close()
            
            if self.active_tasks:
                for task in self.active_tasks:
                    task.cancel()
                await asyncio.gather(*self.active_tasks, return_exceptions=True)
            
            await self.server.wait_closed()

    def print_stats(self):
        print("\nShutting down proxy server now\n", flush=True)

        try:
            self.metrics.print_summary()
        except Exception as e:
            print(f"Error printing metrics: {e}", flush=True)

        try:
            cache = get_cache()
            stats = cache.get_stats()
            print(colored("\nCache Statistics:", "blue", attrs=["bold"]), flush=True)
            print(colored(f"  Entries: {stats['entries']}", "green", attrs=["bold"]), flush=True)
            print(colored(f"  Size: {stats['size_bytes'] / 1024:.1f} KB", "green", attrs=["bold"]), flush=True)
            print(colored(f"  Hit Rate: {stats['hit_rate']}", "green", attrs=["bold"]), flush=True)
        except Exception as e:
            print(colored(f"Error printing cache stats: {e}", "red"), flush=True)

        print(colored("\nProxy server stopped.", "red"), flush=True)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Async HTTP/HTTPS Forward Proxy Server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', '-p', type=int, default=8080, help='Port to listen on (default: 8080)')

    args = parser.parse_args()
    
    server = ProxyServer(host=args.host, port=args.port)

    async def run():
        loop = asyncio.get_running_loop()
        stop_event = asyncio.Event()
        
        def shutdown():
            stop_event.set()
        
        if sys.platform != 'win32':
            loop.add_signal_handler(signal.SIGINT, shutdown)
            loop.add_signal_handler(signal.SIGTERM, shutdown)
        else:
            def windows_signal_handler(signum, frame):
                loop.call_soon_threadsafe(shutdown)
            
            signal.signal(signal.SIGINT, windows_signal_handler)
            signal.signal(signal.SIGTERM, windows_signal_handler)
        
        get_filter()  
        get_cache()  

        server.server = await asyncio.start_server(
            server._handle_client,
            server.host,
            server.port,
            reuse_address=True
        )

        addrs = ', '.join(str(sock.getsockname()) for sock in server.server.sockets)
        print(f"  Proxy Server has been Started")
        print(f"  Listening on {addrs}")
        print(f"  Press Ctrl+C to close")
        await server.server.start_serving()
        await stop_event.wait()
        await server.stop()
        server.print_stats()

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        server.print_stats()


if __name__ == "__main__":
    main()
