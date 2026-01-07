#!/usr/bin/env python3
"""
Simple proxy server to expose the FastAPI backend on a public port
This allows phone connections to reach the backend through port forwarding
"""
import asyncio
import json
from aiohttp import web, ClientSession
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BACKEND_URL = "http://localhost:8000"

async def proxy_handler(request):
    """Proxy requests to the FastAPI backend"""
    path = request.path
    method = request.method
    
    # Build the target URL
    target_url = f"{BACKEND_URL}{path}"
    
    try:
        # Get request body if present
        body = None
        if method in ['POST', 'PUT', 'PATCH']:
            try:
                body = await request.read()
            except:
                body = None
        
        # Make the request to the backend
        async with ClientSession() as session:
            async with session.request(
                method,
                target_url,
                data=body,
                headers=dict(request.headers),
                timeout=30
            ) as resp:
                response_data = await resp.read()
                return web.Response(
                    body=response_data,
                    status=resp.status,
                    content_type=resp.content_type,
                    headers=dict(resp.headers)
                )
    except asyncio.TimeoutError:
        logger.error(f"Timeout proxying {method} {path}")
        return web.json_response(
            {"error": "Backend timeout"},
            status=504
        )
    except Exception as e:
        logger.error(f"Error proxying {method} {path}: {str(e)}")
        return web.json_response(
            {"error": str(e)},
            status=502
        )

async def health_check(request):
    """Health check endpoint"""
    return web.json_response({
        "status": "ok",
        "message": "Proxy server running",
        "backend": BACKEND_URL
    })

async def start_server():
    """Start the proxy server"""
    app = web.Application()
    
    # Add routes
    app.router.add_get('/health', health_check)
    app.router.add_post('/{path_info:.*}', proxy_handler)
    app.router.add_get('/{path_info:.*}', proxy_handler)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 9000)
    await site.start()
    
    logger.info("🚀 Proxy server running on http://0.0.0.0:9000")
    logger.info(f"📡 Forwarding requests to {BACKEND_URL}")
    
    # Keep running
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(start_server())
