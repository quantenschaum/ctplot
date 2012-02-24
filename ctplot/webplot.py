#!c:\Program Files (x86)\Python27\python.exe
# -*- coding: utf-8 -*-
#!/opt/python/bin/python
#!/usr/bin/python
#    pyplot - python based data plotting tools
#    created for DESY Zeuthen
#    Copyright (C) 2012  Adam Lucke  software@louisenhof2.de
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>. 
#
#    $Id$
#
import matplotlib
matplotlib.use('Agg')

import json, os, cgitb, cgi, sys
from plot import Plot, available_tables
from functools import wraps


# configuration ###############################################################

h5dir = 'data'
cachedir = 'cache'
plotdir = 'plots'
usecache = 0

###############################################################################

cgitb.enable()

def hashargs(*args, **kwargs):
    return hash(json.dumps((args, kwargs), separators = (',', ':'), sort_keys = True))

def cached(func):
    'write return values of func into cache (disk) and read them from cache for same arguments'
    @wraps(func)
    def cached_func(*args, **kwargs):
        if usecache:
            h = hashargs(*args, **kwargs)
            filename = '%s-%d.cache' % (func.__name__, h)
            filename = os.path.join(cachedir, filename)
            try:
                f = open(filename)
                v = f.read()
                f .close()
    #            print 'from', filename
                return json.loads(v)

            except IOError:
                f = open(filename, 'w')
                v = func(*args, **kwargs)
                f.write(json.dumps(v))
                f .close()
                return v
        else:
            return func(*args, **kwargs)

    return cached_func

@cached
def tables():
    tabs = available_tables(h5dir)
    return json.dumps(tabs)

@cached
def make_plot(settings):
    p = Plot(**settings)
    h = hashargs(settings)
    name = 'plot-%d' % (h,)
    name = os.path.join(plotdir, name).replace('\\', '/')
    return json.dumps(p.save(name))


contenttypes = {'png': 'image/png'  , 'svg': 'image/svg+xml'  , 'pdf':'application/pdf'   }


if __name__ == '__main__':


    fields = cgi.FieldStorage()
    action = fields.getfirst('a')

    if action in ['plot', 'png', 'svg', 'pdf']:
        settings = {}

        for k in fields.keys():
            if k == 'a': continue
            v = fields.getfirst(k).strip()
            print >> sys.stderr, k, '=' , v
            settings[k] = v

        imgs = make_plot(settings)

        if action == 'plot':
            print "Content-Type: text/plain;charset=utf-8"
            print
            print imgs

        elif action in ['png', 'svg', 'pdf']:
            ct = action
            imgfile = json.loads(imgs)[ct]
            print 'Content-Type: ' + contenttypes[ct]
            print
            with open(imgfile) as img:
                for l in img:
                    sys.stdout.write(l)

    elif action == 'list':
        print "Content-Type: text/plain;charset=utf-8"
        print
        print tables()

    else:
        raise ValueError('unknown action ' + action)

