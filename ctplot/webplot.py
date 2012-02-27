#!/opt/python/bin/python
# -*- coding: utf-8 -*-
#!c:\Program Files (x86)\Python27\python.exe
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

import json, os, cgitb, cgi, sys, subprocess, time
from plot import Plot, available_tables
from functools import wraps
from utils import hashargs, getCpuLoad
from config import *
from threading import Thread



def cached(func):
    'write return values of func into cache (disk) and read them from cache for same arguments'
    @wraps(func)
    def cached_func(*args, **kwargs):
        if usecache:
            h = hashargs(*args, **kwargs)
            filename = '%s%d.cache' % (func.__name__, h)
            filename = os.path.join(cachedir, filename)
            try:
                f = open(filename)
                v = f.read()
                f .close()
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
    # wait until cpu usage is <80%
    if os.name == 'posix':
        while getCpuLoad() > .8:
            time.sleep(1)

    p = Plot(**settings)
    h = hashargs(settings)
    name = 'plot-%d' % (h,)
    name = os.path.join(plotdir, name).replace('\\', '/')
    return p.save(name)


contenttypes = {'png': 'image/png'  , 'svg': 'image/svg+xml'  , 'pdf':'application/pdf'   }


def countInstances(process):
    if os.name == 'nt':
        ps = ['tasklist']
    elif os.name == 'psix':
        ps = ['ps', '-fe']
    else:
        raise RuntimeError('no tasklist command for {} defined'.format(os.name))
    p = subprocess.Popen(ps, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
    count = 0
    for line in p.stdout:
        if process in line:
            print line.strip()
            count += 1
    return count


if __name__ == '__main__':

    cgitb.enable()
    fields = cgi.FieldStorage()
    action = fields.getfirst('a')

    if action in ['plot', 'png', 'svg', 'pdf', 'job']:

        settings = {}
        for k in fields.keys():
            if k[0] in 'xyzcmsorntwfgl':
                settings[k] = fields.getfirst(k).strip()
#            else: print >> sys.stderr, 'discarded', k, '=', fields.getfirst(k).strip()

        images = make_plot(settings)

        if action == 'plot':
            print "Content-Type: text/plain;charset=utf-8\n"
            print json.dumps(images)

        elif action in ['png', 'svg', 'pdf']:
            ct = action
            imgfile = images[ct]
            print 'Content-Type: {}\n'.format(contenttypes[ct])
            with open(imgfile) as img:
                for l in img:
                    sys.stdout.write(l)

    elif action == 'list':
        print "Content-Type: text/plain;charset=utf-8\n"
        print tables()

    else:
        raise ValueError('unknown action ' + action)

