# Main entry point - Async Proxy Server

import asyncio
import signal
import sys
import os
from .forwarder import handle_client
from .domain_filter import get_filter
from .http_cache import get_cache
from .proxy_logger import get_logger, get_metrics


class ProxyServer:

    def __init__(self, host='127.0.0.1', port=8080):
        self.host = host
        self.port = port
        self.server = None
        self.logger = get_logger()
        self.metrics = get_metrics()

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

        async with self.server:
            await self.server.serve_forever()

    async def _handle_client(self, reader, writer):
        try:
            await handle_client(reader, writer)
        except Exception as e:
            client_addr = writer.get_extra_info('peername')
            print(f"Error handling {client_addr}: {e}")
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    def print_stats(self):
        # Force unbuffered output
        print("\nShutting down proxy server now", flush=True)

        try:
            self.metrics.print_summary()
        except Exception as e:
            print(f"Error printing metrics: {e}", flush=True)

        try:
            cache = get_cache()
            stats = cache.get_stats()
            print(f"\nCache Statistics:", flush=True)
            print(f"  Entries: {stats['entries']}", flush=True)
            print(f"  Size: {stats['size_bytes'] / 1024:.1f} KB", flush=True)
            print(f"  Hit Rate: {stats['hit_rate']}", flush=True)
        except Exception as e:
            print(f"Error printing cache stats: {e}", flush=True)

        print("\nProxy server stopped.", flush=True)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Async HTTP/HTTPS Forward Proxy Server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', '-p', type=int, default=8080, help='Port to listen on (default: 8080)')

    args = parser.parse_args()
    
    server = ProxyServer(host=args.host, port=args.port)

    async def run():
        loop = asyncio.get_running_loop()
        stop = loop.create_future()
        
        def shutdown():
            if not stop.done():
                stop.set_result(True)
        
        loop.add_signal_handler(signal.SIGINT, shutdown)
        loop.add_signal_handler(signal.SIGTERM, shutdown)
        
        server_task = asyncio.create_task(server.start())
        
        await stop 
        
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass
        
        server.print_stats()

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
