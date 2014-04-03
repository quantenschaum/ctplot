#!/usr/bin/env python

import os, json, random, string
from os.path import join, abspath, basename
from mimetypes import guess_type
from time import  time
from Queue import Queue
from cgi import FieldStorage
from locket import lock_file
from pkg_resources import resource_string, resource_exists, resource_isdir, resource_listdir

import matplotlib
matplotlib.use('Agg')  # headless backend

import ctplot.plot
from ctplot.utils import hashargs




_config = None

def get_config(env):
    global _config

    if _config:
        return _config

    prefix = 'ctplot_'
    basekey = prefix + 'basedir'
    basedir = abspath(env[basekey] if basekey in env else '.')

    _config = {'cachedir':join(basedir, 'cache'),
               'datadir':join(basedir, 'data'),
               'plotdir':join(basedir, 'plots'),
               'sessiondir':join(basedir, 'sessions')}

    for k in _config.keys():
        ek = prefix + k
        if ek in env:
            _config[k] = env[ek]

    return _config

def getpath(environ):
    return environ['PATH_INFO'] if 'PATH_INFO' in environ else ''


# This is our application object. It could have any name,
# except when using mod_wsgi where it must be "application"
# see http://webpython.codepoint.net/wsgi_application_interface
def application(environ, start_response):
    path = getpath(environ)
    if path == '/webplot.py' or path.startswith('/plot'):
        return dynamic_content(environ, start_response)
    else:
        return static_content(environ, start_response)

# http://www.mobify.com/blog/beginners-guide-to-http-cache-headers/
# http://www.mnot.net/cache_docs/
# http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html
cc_nocache = 'Cache-Control', 'no-cache, max-age=0'
cc_cache = 'Cache-Control', 'public, max-age=86400'



def content_type(path = ''):
    mime_type = None

    if path:
        mime_type = guess_type(path)[0]

    if not mime_type:
        mime_type = 'text/plain'

    return 'Content-Type', mime_type


def static_content(environ, start_response):
    path = getpath(environ)

    if not path:  # redirect
        start_response('301 Redirect', [content_type(), ('Location', environ['REQUEST_URI'] + '/')])
        return []

    if path == '/':
        path = 'web/index.html'  # map / to index.html
    else:
        path = ('web/' + path).replace('//', '/')

    if path == 'web/js':  # combined java scripts
        scripts = {}
        for s in resource_listdir('ctplot', 'web/js'):
            scripts[s] = '\n// {}\n\n'.format(s) + resource_string('ctplot', 'web/js/' + s)
        start_response('200 OK', [content_type(path), cc_cache])
        return [scripts[k] for k in sorted(scripts.keys())]

    if not resource_exists('ctplot', path):  # 404
        start_response('404 Not Found', [content_type()])
        return ['404\n', '{} not found!'.format(path)]

    elif resource_isdir('ctplot', path):  # 403
        start_response('403 Forbidden', [content_type()])
        return ['403 Forbidden']
    else:
        start_response('200 OK', [content_type(path), cc_cache])
        return resource_string('ctplot', path)



def dynamic_content(environ, start_response):
    path = getpath(environ)
    config = get_config(environ)

    if path.startswith('/plots'):
        return serve_plot(path, start_response, config)
    else:
        return handle_action(environ, start_response, config)



def serve_plot(path, start_response, config):
    with open(join(config['plotdir'], basename(path))) as f:
        start_response('200 OK', [content_type(path), cc_cache])
        return [f.read()]


def serve_json(data, start_response):
    start_response('200 OK', [content_type(), cc_nocache])
    return [json.dumps(data)]


def serve_plain(data, start_response):
    start_response('200 OK', [content_type(), cc_nocache])
    return [data]





def make_plot(settings, config):
    basename = 'plot{}'.format(hashargs(settings))
    name = os.path.join(config['plotdir'], basename).replace('\\', '/')

    # try to get plot from cache
    if config['cachedir'] and os.path.isfile(name + '.png'):
        return dict([(e, name + '.' + e) for e in ['png', 'svg', 'pdf']])

    else:
        # lock long running plot creation
        with lock_file(join(config['cachedir'], 'plot.lock')):
            p = ctplot.plot.Plot(config, **settings)
        return p.save(name)


def randomChars(n):
    return ''.join(random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(n))

available_tables = None

def handle_action(environ, start_response, config):
    global available_tables
    fields = FieldStorage(fp = environ['wsgi.input'], environ = environ)
    action = fields.getfirst('a')
    datadir = config['datadir']
    sessiondir = config['sessiondir']

    if action in ['plot', 'png', 'svg', 'pdf']:

        settings = {}
        for k in fields.keys():
            if k[0] in 'xyzcmsorntwhfgl':
                settings[k] = fields.getfirst(k).strip().decode('utf8', errors = 'ignore')

        images = make_plot(settings, config)
        for k, v in images.items():
            images[k] = 'plots/' + basename(v)

        if action == 'plot':
            return serve_json(images, start_response)

        elif action in ['png', 'svg', 'pdf']:
            return serve_plot(images[action], start_response, config)



    elif action == 'list':
        if not available_tables or time() - available_tables[0] > 86400:
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






