#!/usr/bin/env python3

import asyncio
import click
import os
import sys
import time
from aiohttp import web


DEFAULT_PORT = os.environ.get('NOMAD_PORT_http', 8080)


class WebApp:
    def __init__(self, health_toggle=False, oom=False):
        self.app = web.Application()
        self.app.router.add_get('/', self.hello)
        self.app.router.add_get('/health', self.health)
        self.app.router.add_get('/info', self.info)
        self.app.router.add_get('/oom', self.oom)
        self.app.router.add_get('/crash', self.crash_like_a_quiche)

        self.health_toggle = health_toggle
        self.oom = oom

        self.status = {
            'health': True,
        }
        self.data = [1]

    def run(self, port=8080):
        web.run_app(self.app, port=port)

    async def health(self, request):
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
        data = {'version': '1.0.0'}
        return web.json_response(data)

    async def hello(self, request):
        data = {'text': 'Hello, world!'}
        return web.json_response(data)

    async def oom(self, request):
        response = web.StreamResponse()
        await response.prepare(request)

        while True:
            self.data.extend(self.data)
            await response.write(b'size=%d\n' % len(self.data))
            await asyncio.sleep(0.1)

        return response

    async def crash_like_a_quiche(self, request):
        os._exit(255)


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
    app.run(port)


if __name__ == '__main__':
    cli()
