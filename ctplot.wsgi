#!/usr/bin/env python

import os
from ctplot.wsgi import application

# os.environ['ctplot_basedir'] = '/basedir'
# os.environ['ctplot_datadir'] = '/basedir/data'
# os.environ['ctplot_cachedir'] = '/basedir/cache'
# os.environ['ctplot_sessionsdir'] = '/basedir/sessions'
# os.environ['ctplot_plotsdir'] = '/basedir/plots'

if __name__ == '__main__':
    import wsgiref.handlers
    wsgiref.handlers.CGIHandler().run(application)
