import os
import asyncio
from aiohttp import web

loop = asyncio.get_event_loop()

app = web.Application(loop=loop)

app.router.add_get("/", lambda request: web.FileResponse("app/index.html"))
app.router.add_static('/static/', 'app/static', name='public')
app.router.add_static('/node_modules/', 'app/node_modules', name='publicnm')

from routes import routes

for route in routes:
        app.router.add_route(method=route[0], path=route[1], handler=route[2], name=route[3])



web.run_app(app, host="0.0.0.0", port=os.environ.get("PORT") or 8080)   