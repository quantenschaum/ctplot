#!/usr/bin/env python
# -*- coding: utf-8 -*-

# run this using mod_wsgi in a SINGLE process
#    WSGIDaemonProcess ctplot processes=1 threads=20
#    WSGIScriptAlias /ctplot /path/to/ctplot.wsgi process-group=ctplot

import os
from os.path import join, abspath
import cgi
from mimetypes import guess_type
from time import sleep
from Queue import Queue
from pkg_resources import resource_string, resource_filename, resource_exists, resource_stream, resource_isdir

_plot_queue = None
_config=None

def get_config(env):
    global _config
    
    if _config:
        return _config
        
    p='ctplot_'
    basekey=p+'basedir'
    basedir=abspath(env[basekey] if basekey in env else '.')
    _config = {p+'cachedir':join(basedir,'cache'),
               p+'datadir':join(basedir,'data'),
               p+'plotdir':join(basedir,'plots'),
               p+'sessiondir':join(basedir,'sessions'),
               p+'parallel':'4'}
              
    for k in _config.keys():
        if k in env:
            _config[k]=env[k]
            
    return _config


# This is our application object. It could have any name,
# except when using mod_wsgi where it must be "application"
# see http://webpython.codepoint.net/wsgi_application_interface
def application(environ, start_response):
    response = []

    config = get_config(environ)
    response.append('config={}\n'.format(config))

    query = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ)
    response.append(repr(query)+'\n')
    path = environ['PATH_INFO']
    response.append('path={}\n'.format(path))
    
    # create the plot and adjust path
    if path in ['/webplot.py','/plot']:
        global _plot_queue

        if not _plot_queue:
            _plot_queue=Queue(int(config['ctplot_parallel']))

        try:
            _plot_queue.put(query)
            start_response('200', [('Content-Type', 'text/plain')])
            return ['dummy']

        finally:
            _plot_queue.get()
    
    
    
    response.append('\n\n')
    response += ['{}={}\n'.format(k, v).encode('utf-8') for k, v in environ.items()]


#    start_response('200', [('Content-Type', 'text/plain')])
#    return response
    
    return static_content(environ, start_response)
    
    
def static_content(environ, start_response):
    path = environ['PATH_INFO']
    
    if not path: # redirect
        start_response('301 Redirect', [('Content-Type', 'text/plain'),
                                        ('Location',environ['REQUEST_URI']+'/')])
        return []
 
    if path=='/':
        path='web/index.html'   # map / to index.html
    else:
        path='web/'+path
    
    if not resource_exists('ctplot',path): # 404
        start_response('404 Not Found', [('Content-Type', 'text/plain')])
        return ['404\n','{} not found!'.format(path)]
        
    if resource_isdir('ctplot',path): # 403
        content_type = guess_type(path)[0] or 'text/plain' 
        start_response('403 Forbidden', [('Content-Type', 'text/plain' )])
        return ['403 Forbidden']
        
    content_type = guess_type(path)[0] or 'text/plain' 
    start_response('200 OK', [('Content-Type', content_type)])
    return resource_stream('ctplot',path)


