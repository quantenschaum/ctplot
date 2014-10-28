#!/usr/bin/env python

from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from ctplot.wsgi import application

print 'http://localhost:8080'

http_server = HTTPServer(WSGIContainer(application))
http_server.listen(8080)
IOLoop.instance().start()

