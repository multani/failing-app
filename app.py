#!/usr/bin/env python3

import asyncio
import click
import os
import random
import sys
import time
from aiohttp import web


DEFAULT_PORT = os.environ.get('NOMAD_PORT_http', 8080)

CODES_DISTRIBUTION = ([200] * 1000) + ([404] * 1) + ([500] * 1) + ([503] * 1)

class WebApp:
    def __init__(self, health_toggle=False, oom=False):
        self.app = web.Application()
        self.app.router.add_get('/', self.hello)
        self.app.router.add_get('/health', self.health)
        self.app.router.add_get('/echo', self.echo)
        self.app.router.add_get('/info', self.info)
        self.app.router.add_get('/oom', self.oom)
        self.app.router.add_get('/crash', self.crash_like_a_quiche)
        self.app.router.add_get('/timeout', self.long_execution)
        self.app.router.add_get('/code/{code:\d+}', self.reply_code)
        self.app.router.add_get('/code/random', self.reply_random_code)

        self.health_toggle = health_toggle
        self.oom = oom

        self.status = {
            'health': True,
        }
        self.data = [1]

    def run(self, port=8080):
        web.run_app(self.app, port=port)

    def show_help(self):
        for route in self.app.router.routes():
            method = route.method
            if method == "HEAD":
                continue

            info = route.get_info()
            if 'path' in info:
                path = info['path']
            else:
                path = info['formatter']

            doc = route.handler.__doc__
            if not doc:
                doc = "{}()".format(route.handler.__func__.__name__)
            doc = doc.split('\n')[0]

            print("{} on {:<20}: {:<25}".format(method, path, doc))

    async def health(self, request):
        """Health of the application"""

        if self.health_toggle:
            self.status['health'] = not self.status['health']

        if self.oom:
            self.data.extend(self.data)

        ok = self.status['health']
        data = {
            'status': "ok" if ok else "failure",
            'size': len(self.data),
        }
        return web.json_response(data, status=200 if ok else 500)

    async def info(self, request):
        """Basic information"""

        data = {'version': '1.0.0'}
        return web.json_response(data)

    async def echo(self, request):
        data = ["{} {} {}".format(request.method, request.url, request.version)]
        data = data + [
            "{}: {}".format(key, value)
            for (key, value) in sorted(request.headers.items())
        ]

        response = web.Response(text="\n".join(data))
        return response

    async def hello(self, request):
        """Just some basic JSON"""

        data = {'text': 'Hello, world!'}
        return web.json_response(data)

    async def oom(self, request):
        """Consume more and more of memory"""

        response = web.StreamResponse()
        await response.prepare(request)

        while True:
            self.data.extend(self.data)
            await response.write(b'size=%d\n' % len(self.data))
            await asyncio.sleep(0.1)

        return response

    async def crash_like_a_quiche(self, request):
        """Exit as rudely as possible the application"""

        os._exit(255)

    async def long_execution(self, request):
        """Return a response after a very long time"""

        timeout = 120 # seconds
        print("waiting {} seconds to answer request".format(timeout))
        await asyncio.sleep(timeout)
        return web.json_response({'waited': timeout})

    async def reply_code(self, request):
        """Return the request HTTP status code"""

        code = int(request.match_info['code'])
        return web.json_response({'code': code}, status=code)

    async def reply_random_code(self, request):
        """Generate a random HTTP status code"""

        code = random.choice(CODES_DISTRIBUTION)
        return web.json_response({'code': code}, status=code)


@click.group()
def cli():
    pass


@cli.command(help="A non web-app which crashes after the specified duration")
@click.option("-d", "--duration", type=int, default=10)
@click.option("-e", "--exit-code", type=int, default=255)
def fail_after(duration, exit_code):
    print("Starting application: will fail in {} seconds".format(duration))
    while duration > 0:
        time.sleep(1)
        duration -= 1
        print("Will fail in {} seconds".format(duration))

    print("Will fail now!")
    os._exit(exit_code)


@cli.command(help="/health flaps between OK and not OK at each call")
@click.option("-p", "--port", type=int, default=DEFAULT_PORT)
def flapping_health(port):
    app = WebApp(health_toggle=True)
    app.run(port)


@cli.command(help="Leak memory on each /health call")
@click.option("-p", "--port", type=int, default=DEFAULT_PORT)
def mem_leak(port):
    app = WebApp(oom=True)
    app.run(port)


@cli.command(help="A 'normal' web app")
@click.option("-p", "--port", type=int, default=DEFAULT_PORT)
def web_app(port):
    app = WebApp()
    app.show_help()
    app.run(port)


if __name__ == '__main__':
    cli()
