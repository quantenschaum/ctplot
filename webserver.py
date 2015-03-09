#!/usr/bin/env python

import os
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from ctplot.wsgi import application

port = int(os.environ['CTPLOT_PORT']) if 'CTPLOT_PORT' in os.environ else 8080
print 'listening on', port

http_server = HTTPServer(WSGIContainer(application))
http_server.listen(port)
IOLoop.instance().start()
