#!/usr/bin/env python
# -*- coding: utf-8 -*-

# run this using mod_wsgi in a SINGLE process
#    WSGIApplicationGroup %{GLOBAL}
#    WSGIDaemonProcess ctplot processes=2 threads=20
#    WSGIScriptAlias /ctplot /path/to/ctplot.wsgi process-group=ctplot

import os
import string
import locale
from os.path import join, abspath, basename
from mimetypes import guess_type
from time import sleep, time
from Queue import Queue
from pkg_resources import resource_string, resource_exists, resource_isdir, resource_listdir

import matplotlib
matplotlib.use('Agg')  # headless backend 

import json, os, cgi, sys, random, string
import ctplot
import ctplot.plot
#from ctplot.plot import Plot, available_tables
from ctplot.utils import hashargs, getCpuLoad, getRunning
from datetime import datetime
import pytz



_plot_queue = Queue(1)
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
               p+'sessiondir':join(basedir,'sessions')}
              
    for k in _config.keys():
        if k in env:
            _config[k]=env[k]
            
    return _config


# This is our application object. It could have any name,
# except when using mod_wsgi where it must be "application"
# see http://webpython.codepoint.net/wsgi_application_interface
def application(environ, start_response):
    path = environ['PATH_INFO']
    if path =='/webplot.py' or path.startswith('/plot'):
        return dynamic_content(environ, start_response)
    else:
        return static_content(environ, start_response)

# http://www.mobify.com/blog/beginners-guide-to-http-cache-headers/      
# http://www.mnot.net/cache_docs/  
# http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html
cc_nocache = 'Cache-Control', 'no-cache, max-age=0'
cc_cache = 'Cache-Control', 'public, max-age=86400'



   
def static_content(environ, start_response):
    path = environ['PATH_INFO']
    
    if not path: # redirect
        start_response('301 Redirect', [('Content-Type', 'text/plain'),
                                        ('Location',environ['REQUEST_URI']+'/')])
        return []
 
    if path=='/':
        path='web/index.html'   # map / to index.html
    else:
        path=('web/'+path).replace('//','/')
        
    if path=='web/js': # combined java scripts
        scripts={}
        for s in resource_listdir('ctplot','web/js'):
            scripts[s]='\n// {}\n\n'.format(s)+resource_string('ctplot','web/js/'+s)
        content_type = guess_type(path)[0] or 'text/plain' 
        start_response('200 OK', [('Content-Type', content_type), cc_cache])
        return [scripts[k] for k in sorted(scripts.keys())]
    
    if not resource_exists('ctplot',path): # 404
        start_response('404 Not Found', [('Content-Type', 'text/plain')])
        return ['404\n','{} not found!'.format(path)]
        
    elif resource_isdir('ctplot',path): # 403
        start_response('403 Forbidden', [('Content-Type', 'text/plain' )])
        return ['403 Forbidden']
    else:  
        content_type = guess_type(path)[0] or 'text/plain' 
        start_response('200 OK', [('Content-Type', content_type), cc_cache])
        return resource_string('ctplot',path)



def dynamic_content(environ, start_response):
    global _plot_queue
    config = get_config(environ)
    path = environ['PATH_INFO']
    
    if path.startswith('/plots'):
        return serve_plot(path, start_response, config)

    try:
        _plot_queue.put('task') # push to queue to indicate a longer running task
        return handle_action(environ, start_response, config)

    finally:
        _plot_queue.get() # mark task as finished
        


def serve_plot(path, start_response, config):
    with open(join(config['ctplot_plotdir'],basename(path))) as f:
        start_response('200 OK', [('Content-Type', guess_type(path)[0]), cc_cache])
        return [f.read()]
        
        
def serve_json(data, start_response):        
    start_response('200 OK', [('Content-Type', 'text/plain'), cc_nocache])
    return [json.dumps(data)]
    

def serve_plain(data, start_response):        
    start_response('200 OK', [('Content-Type', 'text/plain'), cc_nocache])
    return [data]





def make_plot(settings, config):
    basename = 'plot{}'.format(hashargs(settings))
    name = os.path.join(config['ctplot_plotdir'], basename).replace('\\', '/')

    # try to get plot from cache
    if config['ctplot_cachedir'] and os.path.isfile(name + '.png'):
        return dict([(e, name + '.' + e) for e in ['png', 'svg', 'pdf']])

    else:
        p = ctplot.plot.Plot(config,**settings)
        return p.save(name)


def randomChars(n):
    return ''.join(random.choice(string.ascii_lowercase+string.ascii_uppercase+string.digits) for _ in range(n))
    
available_tables = None    

def handle_action(environ,start_response, config):
    global available_tables
    fields =  cgi.FieldStorage(fp=environ['wsgi.input'],  environ=environ)
    action = fields.getfirst('a')
    datadir = config['ctplot_datadir']
    sessiondir = config['ctplot_sessiondir']

    if action in ['plot', 'png', 'svg', 'pdf']:

        settings = {}
        for k in fields.keys():
            if k[0] in 'xyzcmsorntwhfgl':
                settings[k] = fields.getfirst(k).strip().decode('utf8', errors = 'ignore')

        images = make_plot(settings, config)
        for k,v in images.items():
            images[k]='plots/'+basename(v)

        if action == 'plot':
            return serve_json(images, start_response)

        elif action in ['png', 'svg', 'pdf']:
            return serve_plot(images[action], start_response, config)
              
                
                
    elif action == 'list':
        start_response('200 OK',[('Content-Type','text/plain')])
        if not available_tables or time()-available_tables[0]>86400: 
            available_tables = time(), ctplot.plot.available_tables(datadir)
        return serve_json(available_tables[1], start_response)

    elif action == 'save':
        id = fields.getfirst('id').strip()
        if len(id) < 8: raise RuntimeError('session id must have at least 8 digits')
        data = fields.getfirst('data').strip()
        with open(os.path.join(sessiondir, '{}.session'.format(id)), 'w') as f:
            f.write(data.replace('},{', '},\n{'))
        return serve_json('saved {}'.format(id), start_response)

    elif action == 'load':
        id = fields.getfirst('id').strip()
        if len(id) < 8: raise RuntimeError('session id must have at least 8 digits')
        try:
            with open(os.path.join(sessiondir, '{}.session'.format(id))) as f:
                return serve_plain(f.read(), start_response)
        except:
            return serve_json('no data for {}'.format(id), start_response)

    elif action == 'newid':
        id = randomChars(16)
        while os.path.isfile(os.path.join(sessiondir, '{}.session'.format(id))):
            id = randomChars(16)
        return serve_plain(id, start_response)
        
    else:
        raise ValueError('unknown action {}'.format(action))













