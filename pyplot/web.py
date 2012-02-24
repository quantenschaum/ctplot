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
'''
Created on 27.10.2011
@author: al
webinterface to plotting tools
'''
import matplotlib
matplotlib.use('Agg')

import json, os, cgitb, cgi, sys
from plot import Plot, available_tables
from functools import wraps


# configuration ###############################################################

h5dir = 'data'
cachedir = 'cache'
plotdir = 'plots'
usecache = False

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




if __name__ == '__main__':
    print "Content-Type: text/plain;charset=utf-8"
    print


    fields = cgi.FieldStorage()
    action = fields.getfirst('a')

    if action == 'plot':
        settings = {}

        for k in fields.keys():
            print >> sys.stderr, k, '=' , fields.getfirst(k)
            settings[k] = fields.getfirst(k)

        print make_plot(settings)

    elif action == 'list':
        print tables()

    else:
        raise ValueError('unknown action ' + action)

